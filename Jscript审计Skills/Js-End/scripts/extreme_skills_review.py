#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, sys
from pathlib import Path

STATUS_LEGEND = ['ready','partial','doc-only','fake-ready','missing','conflict','未证实']
SKILL_REQUIRED_SECTIONS = ['职责边界','必须触发','禁止触发','输入','输出','执行步骤','质量门槛']
SEMANTIC_HINTS = ['Babel','TypeScript Compiler API','tree-sitter','AST','CFG','DFG','source-sink','taint','dataflow','auth resolver','tenant']
RUNTIME_HINTS = ['Playwright','Burp','HAR','trace','screenshot','browser','多角色','多租户']


def read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def rel(root: Path, p: Path) -> str:
    return str(p.relative_to(root)).replace('\\','/')


def all_files(root: Path):
    return sorted([p for p in root.rglob('*') if p.is_file()])


def load_data(root: Path, name: str):
    p = root/'data'/name
    if not p.exists(): return []
    return json.loads(read(p))


def grep_files(root: Path, patterns):
    hits=[]
    regs=[re.compile(p, re.I) for p in patterns]
    for p in all_files(root):
        rp=str(p).replace('\\','/')
        if '/tests/last-extreme-review' in rp or '/tests/last-second-pass-review' in rp:
            continue
        if p.suffix.lower() not in {'.md','.py','.json','.yaml','.yml','.js','.ts'}: continue
        txt=read(p)
        if any(r.search(txt) for r in regs): hits.append(rel(root,p))
    return hits


def has_executable_script(root: Path, keywords):
    scripts=list((root/'scripts').glob('*.py')) if (root/'scripts').exists() else []
    out=[]
    for p in scripts:
        txt=read(p)+p.name
        if any(k.lower() in txt.lower() for k in keywords): out.append(rel(root,p))
    return out


def section_audit(root: Path):
    rows=[]; findings=[]
    for d in sorted([p for p in root.glob('[0-9][0-9]-*') if p.is_dir()]):
        skill=d/'SKILL.md'
        if not skill.exists():
            rows.append([rel(root,d),'Skill 目录','缺失 SKILL.md','路由可能丢失','Claude Skills 不可识别','新增 SKILL.md','P0'])
            findings.append({'priority':'P0','path_or_object':rel(root,d),'problem':'缺失 SKILL.md','evidence':rel(root,d),'fix':'新增标准 SKILL.md'})
            continue
        txt=read(skill)
        miss=[s for s in SKILL_REQUIRED_SECTIONS if f'## {s}' not in txt and s not in txt]
        problem='缺少章节：'+','.join(miss) if miss else '未发现结构性缺失'
        pri='P1' if miss else 'P2'
        rows.append([rel(root,d),'Claude Skill',problem,'缺章节会导致误触发或证据不足' if miss else '低','维护与交接不稳定' if miss else '低','补齐触发/禁止/输入/输出/步骤/质量门槛' if miss else '保持','P1' if miss else 'P2'])
        if miss:
            findings.append({'priority':'P1','path_or_object':rel(root,skill),'problem':problem,'evidence':rel(root,skill),'fix':'补齐标准章节'})
    for p in all_files(root):
        if p.name == '__pycache__' or p.suffix == '.pyc' or p.name.endswith('~') or p.suffix in {'.tmp','.bak'}:
            rows.append([rel(root,p),'冗余/缓存','禁止进入发布包','hash 漂移或泄露本机状态','打包不可复现','删除并加入 self-check','P0'])
            findings.append({'priority':'P0','path_or_object':rel(root,p),'problem':'发现冗余/缓存文件','evidence':rel(root,p),'fix':'删除并在 package_self_check 中阻断'})
    return rows, findings


def classify_capability(root: Path, name: str, mode: str):
    # Evidence heuristics: this script is intentionally conservative.
    terms=[re.escape(x) for x in re.findall(r'[A-Za-z0-9_./+-]+|[\u4e00-\u9fff]{2,}', name)]
    hits=grep_files(root, terms[:8]) if terms else []
    scripts=[]
    method='未证实'
    semantic='否'
    if 'AST' in name or 'Compiler' in name or 'tree-sitter' in name or mode == 'audit':
        scripts=has_executable_script(root, ['ast','parser','babel','tree','typescript','source_sink','taint','dataflow'])
    elif 'Playwright' in name or 'Burp' in name or 'HAR' in name or '运行态' in name:
        scripts=has_executable_script(root, ['playwright','burp','har','browser','trace'])
    elif 'source map' in name.lower() or 'sourcemap' in name.lower():
        scripts=has_executable_script(root, ['sourcemap','source_map'])
    elif 'endpoint' in name.lower() or '接口' in name:
        scripts=has_executable_script(root, ['endpoint','route','asset'])
    elif 'manifest' in name.lower() or 'quality' in name.lower():
        scripts=has_executable_script(root, ['quality','manifest'])
    else:
        scripts=has_executable_script(root, ['extract','asset','route','endpoint','graph'])
    tests=grep_files(root/'tests' if (root/'tests').exists() else root, [re.escape(name.split(' ')[0])])
    fixtures=grep_files(root/'fixtures' if (root/'fixtures').exists() else root, [re.escape(name.split(' ')[0])])
    # Conservative status
    if scripts and (tests or fixtures): status='partial'
    elif scripts: status='partial'
    elif hits: status='doc-only'
    else: status='missing'
    if mode == 'audit' and any(k.lower() in name.lower() for k in ['babel','typescript compiler','tree-sitter','dataflow','taint','resolver','ast']):
        if not scripts: status = 'doc-only' if hits else 'missing'
        semantic = '是' if scripts and ('ast' in ' '.join(scripts).lower() or 'parser' in ' '.join(scripts).lower()) else '否'
        method = 'parser/语义脚本' if semantic == '是' else ('文档/候选规则' if hits else '缺失')
    elif mode == 'collection':
        method = '采集脚本' if scripts else ('文档规则' if hits else '缺失')
    else:
        method = '候选/模板/规则' if hits else '缺失'
    return status, hits[:6], scripts[:4], tests[:3], fixtures[:3], method, semantic


def markdown_audit(root: Path):
    rows=[]; findings=[]
    for p in sorted(root.rglob('*.md')):
        txt=read(p)
        claims=[]
        for h in SEMANTIC_HINTS + RUNTIME_HINTS:
            if h.lower() in txt.lower(): claims.append(h)
        support=[]
        if any(h in claims for h in SEMANTIC_HINTS): support += has_executable_script(root, ['ast','parser','babel','typescript','tree','taint','dataflow'])
        if any(h in claims for h in RUNTIME_HINTS): support += has_executable_script(root, ['playwright','burp','har','browser','trace'])
        if claims and not support:
            rows.append([rel(root,p), ', '.join(sorted(set(claims))[:8]), '未发现对应 runtime/parser 脚本', '声明强于实现', '可能导致 fake-ready 与 Claude 幻觉', '改成 doc-only 或新增脚本/测试/availability check'])
            findings.append({'priority':'P1','path_or_object':rel(root,p),'problem':'Markdown 声明能力缺少脚本支撑','evidence':rel(root,p),'fix':'绑定实现文件或降级声明'})
        else:
            rows.append([rel(root,p), ', '.join(sorted(set(claims))[:8]) if claims else '常规规则/模板', ', '.join(support[:5]) if support else '无需专门支撑或未声明强能力', '未发现明显不一致', '低', '保持'])
    return rows, findings


def script_audit(root: Path):
    expected=load_data(root,'script_inventory_expected.json')
    rows=[]; findings=[]
    for item in expected:
        name=item['script']; low=name.lower()
        candidates=[]
        for p in (root/'scripts').glob('*.py') if (root/'scripts').exists() else []:
            blob=(p.name+' '+read(p)).lower()
            if any(tok in blob for tok in re.split(r'[/ _-]+', low) if len(tok)>3): candidates.append(rel(root,p))
        executable='yes' if candidates else 'no'
        tests=grep_files(root/'tests' if (root/'tests').exists() else root, [re.escape(name.split('/')[0]), re.escape(name.split()[0])])
        called='yes' if grep_files(root, [re.escape(Path(c).name) for c in candidates]) else ('no' if not candidates else 'partial')
        handles='yes' if candidates and any(('try' in read(root/c) or 'except' in read(root/c) or 'raise' in read(root/c)) for c in candidates) else 'no'
        evidence='yes' if candidates and any(('json' in read(root/c).lower() or 'manifest' in read(root/c).lower() or 'print' in read(root/c).lower()) for c in candidates) else 'no'
        defect='缺失脚本' if not candidates else ('缺测试' if not tests else '覆盖有限')
        rows.append([name,item.get('input',''),item.get('output',''),executable,'yes' if tests else 'no',called,handles,evidence,defect,'新增真实脚本、测试、fixture 与调用链' if not candidates else '补齐测试与失败处理'])
        if not candidates:
            findings.append({'priority':'P0','path_or_object':name,'problem':'预期核心脚本缺失','evidence':'data/script_inventory_expected.json','fix':'新增脚本并加入 self-check/replay'})
    return rows, findings


def score(root: Path, findings):
    files=all_files(root); texts='\n'.join(read(p) for p in files if p.suffix in {'.md','.py','.json','.yaml','.yml'})
    skill_count=len([p for p in root.glob('[0-9][0-9]-*') if (p/'SKILL.md').exists()])
    structure=max(0,10 - sum(1 for f in findings if f['priority']=='P0' and 'SKILL' in f.get('problem',''))*3)
    info=4 + (1 if 'HAR' in texts else 0) + (1 if 'Burp' in texts else 0) + (1 if 'Playwright' in texts else 0)
    js_collection=5 + (2 if 'source map' in texts.lower() or 'sourcemap' in texts.lower() else 0) + (1 if 'chunk' in texts.lower() else 0) + (1 if 'asset' in texts.lower() else 0)
    semantic=4 + (2 if 'Babel' in texts else 0) + (2 if 'TypeScript Compiler API' in texts else 0) + (2 if 'tree-sitter' in texts else 0)
    if not has_executable_script(root, ['ast','parser','babel','tree','typescript','taint','dataflow']): semantic=min(semantic,7)
    severe=8 + (2 if 'GraphQL' in texts else 0) + (2 if 'WebSocket' in texts else 0) + (2 if 'Electron' in texts else 0) + (2 if 'postMessage' in texts else 0)
    dynamic=4 + (1 if '三次复现' in texts else 0) + (1 if '反证' in texts else 0) + (1 if 'Playwright' in texts else 0) + (1 if 'Burp' in texts else 0) + (1 if 'HAR' in texts else 0)
    if not has_executable_script(root, ['playwright','burp','har','browser','trace']): dynamic=min(dynamic,6)
    tests=3 + (2 if (root/'tests').exists() else 0) + (1 if (root/'fixtures').exists() else 0)
    if not list((root/'fixtures').rglob('*')) if (root/'fixtures').exists() else True: tests=min(tests,5)
    knowledge=1 + (2 if (root/'knowledge').exists() else 0) + (1 if (root/'templates').exists() else 0) + (1 if (root/'schemas').exists() else 0)
    sc={'structure':min(structure,10),'info_collection':min(info,10),'js_collection':min(js_collection,15),'semantic_audit':min(semantic,20),'severe_vuln':min(severe,20),'dynamic_evidence':min(dynamic,10),'tests_replay':min(tests,10),'knowledge_templates':min(knowledge,5)}
    sc['total']=sum(sc.values())
    return sc


def md_table(headers, rows):
    out=['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---']*len(headers)) + '|']
    for r in rows:
        out.append('| ' + ' | '.join(str(x).replace('\n',' ') for x in r) + ' |')
    return '\n'.join(out)


def build_report(root: Path, result):
    parts=[]
    sc=result['scores']
    parts.append('# JS 安全审计 Skills 极限评审报告')
    parts.append('\n## 1. 执行摘要\n')
    parts.append(f"当前自动审查分数：{sc['total']}/100。该分数由静态包内证据估算；未执行真实浏览器、Burp、AST parser 或真实 OSS replay 时，不得视为人工最终分。")
    parts.append('\n## 2. Skills 包结构审查\n')
    parts.append(md_table(['文件/目录','当前作用','发现问题','安全影响','工程影响','修复建议','优先级'], result['structure_rows']))
    parts.append('\n## 3. JS 收集能力审查\n')
    parts.append(md_table(['JS 收集点','当前是否支持','对应文件','真实程度','缺陷','漏洞挖掘影响','修复方式','测试样本'], result['collection_rows']))
    parts.append('\n## 4. JS 审计能力审查\n')
    parts.append(md_table(['审计能力','当前实现文件','方法类型','是否语义级','缺陷','会漏掉什么严重漏洞','修复方案','应增加的测试'], result['audit_rows']))
    parts.append('\n## 5. 严重 JS 漏洞发现能力审查\n')
    parts.append(md_table(['漏洞链','Skills 是否覆盖','证据来源','当前检测深度','是否支持动态验证','是否支持多角色/多租户','漏报风险','误报风险','修复建议'], result['severe_rows']))
    parts.append('\n## 6. 信息收集与 JS 联动审查\n')
    parts.append(md_table(['联动链路','当前是否闭环','对应文件','断点','影响','修复方式'], result['linkage_rows']))
    parts.append('\n## 7. 脚本工程落地审查\n')
    parts.append(md_table(['脚本','输入','输出','是否可执行','是否有测试','是否真实调用','是否处理失败','是否产生证据','主要缺陷','修复建议'], result['script_rows']))
    parts.append('\n## 8. Markdown 文件一致性审查\n')
    parts.append(md_table(['Markdown 文件','声明能力','实际支撑文件','不一致点','风险','修复建议'], result['markdown_rows']))
    parts.append('\n## 9. 知识库与漏洞模板保真度审查\n')
    kt=[]
    for obj,path in [('knowledge',root/'knowledge'),('templates',root/'templates'),('schemas',root/'schemas')]:
        files=[rel(root,p) for p in path.rglob('*') if p.is_file()] if path.exists() else []
        kt.append([obj, ', '.join(files[:8]) if files else '缺失', '需检查索引/触发/绑定' if files else '缺失', '可能无法被真实调用', '增加 index/checker/manifest 绑定'])
    parts.append(md_table(['对象','当前证据','缺陷','影响','修复建议'], kt))
    parts.append('\n## 10. 动态验证与证据链审查\n')
    parts.append(md_table(['验证链路','当前证据','缺口','风险','修复建议'], [
        ['Playwright/Burp/HAR bridge', ', '.join(has_executable_script(root,['playwright','burp','har'])) or '未发现脚本', '缺真实 runtime bridge 或 availability check', '静态候选被误写成 verified', '新增只读采集桥接脚本、HAR schema、fixture'],
        ['三次复现与反证', '07-js-dynamic-validator/SKILL.md, scripts/strict_quality_gate.py', '缺真实请求/响应样本与多角色 fixture', '越权类误报/漏报', '增加 positive/blocked/review fixtures']
    ]))
    parts.append('\n## 11. 测试与 replay 审查\n')
    parts.append(md_table(['测试类型','当前证据','缺口','风险','修复建议'], [
        ['触发路由测试','tests/trigger-test-cases.json, scripts/skill_trigger_tester.py','缺真实 OSS replay','路由正确不等于漏洞发现能力真实','增加多框架 replay'],
        ['质量门禁测试','tests/sample-manifests/insufficient.json, scripts/strict_quality_gate.py','缺 positive/blocked/needs_review 完整样本','verified 可能虚高','补齐样本矩阵']
    ]))
    parts.append('\n## 12. 质量评分\n')
    score_rows=[
        ['Skills 包结构',sc['structure'],'见结构审查','目录/SKILL.md/self-check','补齐缺失章节与冗余阻断'],
        ['信息收集能力',sc['info_collection'],'联动闭环与 runtime 证据不足','data/info_js_linkage_matrix.json','接入 crawl/HAR/Burp/Playwright'],
        ['JS 收集能力',sc['js_collection'],'多数为文档/规则，缺真实采集器','data/js_collection_points.json','新增 asset/chunk/sourcemap/runtime collectors'],
        ['JS AST / 语义审计能力',sc['semantic_audit'],'无真实 parser backend 时封顶较低','data/js_audit_capabilities.json','接入 Babel/TS/tree-sitter/source-sink'],
        ['严重 JS 漏洞发现能力',sc['severe_vuln'],'链路存在但动态验证与多角色 replay 不足','data/js_severe_vulnerability_chains.json','拆 detector 并接 evidence'],
        ['动态验证与证据链',sc['dynamic_evidence'],'缺浏览器/Burp/HAR 桥接脚本时扣分','07/08/scripts','新增 availability check 与 manifest bridge'],
        ['测试与回放',sc['tests_replay'],'缺真实 OSS replay 与完整样本矩阵','tests/fixtures','增加正/负/阻断/needs_review'],
        ['知识库与模板保真度',sc['knowledge_templates'],'有文件但仍需索引与绑定检查','knowledge/templates/schemas','增加 index checker']
    ]
    parts.append(md_table(['评分项','分数','扣分原因','证据文件','提升到顶级所需修复'], score_rows))
    parts.append('\n## 13. P0/P1/P2 修复清单\n')
    fix_rows=[]
    for i,f in enumerate(result['findings'][:80],1):
        fix_rows.append([f.get('priority','P2'), f"AUTO-{i:03d}", f.get('problem',''), f.get('path_or_object',''), '按修复方案新增', '加入对应 fixture/replay', f.get('fix','')])
    parts.append(md_table(['优先级','编号','问题','修改文件','新增文件','测试','验收标准'], fix_rows or [['P2','AUTO-000','未发现自动阻断项','无','无','保持现有自检','self-check pass']]))
    parts.append('\n## 14. 顶级标准差距\n')
    parts.append('1. 最大差距通常是：真实 parser backend、运行态浏览器采集、Burp/HAR 桥接、多角色多租户 replay、真实 OSS replay 与 detector 级测试。\n2. 仅 Markdown 声明的能力必须降级为 doc-only。\n3. grep/regex/模板只能证明候选，不是漏洞发现。\n4. 最容易漏报：role-only chunk、tenant-only endpoint、source map 原始源码链、postMessage、GraphQL hidden mutation、WebSocket auth、Electron/Extension/WebView 边界。\n5. 最容易导致 Claude 幻觉：README 愿景、TODO、模板示例、工具名、未运行的 Playwright/Burp、未安装 parser。')
    parts.append('\n## 15. 最终结论\n')
    parts.append(f"当前自动分数：{sc['total']}/100。目标分数：90+/100。最短补强路径：先补 P0 的 parser backend、runtime evidence bridge、样本矩阵、manifest/report/dashboard 绑定，再做 P1 的 detector 拆分与真实项目 replay。")
    return '\n'.join(parts)+'\n'


def main():
    ap=argparse.ArgumentParser(description='Conservative extreme reviewer for JS audit Claude Skills packages')
    ap.add_argument('root', nargs='?', default='.')
    ap.add_argument('--json-out')
    ap.add_argument('--markdown')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    if not root.exists():
        print(json.dumps({'ok':False,'error':f'root not found: {root}'}, ensure_ascii=False)); return 2
    structure_rows, findings = section_audit(root)
    # Collection rows
    collection_rows=[]
    for item in load_data(root,'js_collection_points.json'):
        st,hits,scripts,tests,fixtures,method,semantic=classify_capability(root,item['name'],'collection')
        collection_rows.append([item['name'], '支持' if st in {'ready','partial','doc-only'} else '不支持', ', '.join(hits[:4] or scripts[:4]) or '未发现', st, '实现证据不足' if st!='ready' else '无', '可能漏掉运行态/隐藏资产' if st!='ready' else '低', '新增采集脚本、ledger、fixture、失败处理', ', '.join(tests or fixtures) or '缺失'])
    audit_rows=[]
    for item in load_data(root,'js_audit_capabilities.json'):
        st,hits,scripts,tests,fixtures,method,semantic=classify_capability(root,item['name'],'audit')
        audit_rows.append([item['name'], ', '.join(scripts or hits[:4]) or '未发现', method, semantic, '缺语义级证据' if semantic=='否' else '覆盖需验证', '高危链路漏报或误报' if semantic=='否' else '低', '接入真实 parser backend/source-sink/auth/tenant detector', ', '.join(tests or fixtures) or '缺失'])
    severe_rows=[]
    for item in load_data(root,'js_severe_vulnerability_chains.json'):
        st,hits,scripts,tests,fixtures,method,semantic=classify_capability(root,item['name'],'severe')
        dynamic=bool(grep_files(root, ['三次复现','dynamic','Playwright','Burp','HAR'])) and bool(has_executable_script(root,['quality','manifest']))
        multi=bool(grep_files(root,['多角色','多租户','tenant','role']))
        severe_rows.append([item['name'], '覆盖' if hits else '未证实', ', '.join(hits[:5]) or '未发现', method, 'partial' if dynamic else 'no', 'partial' if multi else 'no', '高' if not hits or not dynamic else '中', '高' if not dynamic else '中', '增加 detector、动态验证、双账号/多租户 replay、manifest 字段'])
    linkage_rows=[]
    for item in load_data(root,'info_js_linkage_matrix.json'):
        st,hits,scripts,tests,fixtures,method,semantic=classify_capability(root,item['name'],'linkage')
        linkage_rows.append([item['name'], 'partial' if hits or scripts else 'no', ', '.join(hits[:4] or scripts[:4]) or '未发现', '缺运行态桥接/数据流入脚本' if not scripts else '脚本覆盖有限', '信息收集结果不能稳定喂给 JS 深审' if not scripts else '需验证', '新增 bridge、index、evidence ledger'])
    script_rows, f2=script_audit(root); findings += f2
    markdown_rows, f3=markdown_audit(root); findings += f3
    sc=score(root, findings)
    result={'ok':True,'package':{'root':str(root),'file_count':len(all_files(root)),'skill_count':len([p for p in root.glob('[0-9][0-9]-*') if (p/'SKILL.md').exists()])},'status_legend':STATUS_LEGEND,'scores':sc,'structure_rows':structure_rows,'collection_rows':collection_rows,'audit_rows':audit_rows,'severe_rows':severe_rows,'linkage_rows':linkage_rows,'script_rows':script_rows,'markdown_rows':markdown_rows,'findings':findings}
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.markdown:
        Path(args.markdown).write_text(build_report(root, result), encoding='utf-8')
    print(json.dumps({'ok':True,'root':str(root),'total_score':sc['total'],'findings':len(findings),'markdown':args.markdown,'json_out':args.json_out}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
