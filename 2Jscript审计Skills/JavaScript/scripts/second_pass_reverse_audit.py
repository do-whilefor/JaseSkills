#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

STATUS_TERMS = ['ready','partial','doc-only','fake-ready','missing','conflict','candidate-only','未证实','未动态验证','缺少 role/tenant replay','测试不足','证据不可强校验','无法闭环到报告','无法量化质量']
FORBIDDEN_AS_READY = ['TODO','planned','plan','计划','后续','待接入','待实现','doc-only','fake-ready']


def read(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace('\\','/')
    except Exception:
        return str(p).replace('\\','/')


def files(root: Path):
    return sorted([p for p in root.rglob('*') if p.is_file()])


def load_json(root: Path, relpath: str, default=None):
    p=root/relpath
    if not p.exists():
        return [] if default is None else default
    return json.loads(read(p))


def grep(root: Path, needles, exts={'.md','.py','.json','.yaml','.yml','.js','.ts'}):
    if not root.exists():
        return []
    regs=[]
    for n in needles:
        if not n: continue
        regs.append(re.compile(re.escape(n), re.I))
    hits=[]
    for p in files(root):
        rp=str(p).replace('\\','/')
        if '/tests/last-extreme-review' in rp or '/tests/last-second-pass-review' in rp:
            continue
        if p.suffix.lower() not in exts: continue
        txt=read(p)
        if any(r.search(txt) for r in regs):
            hits.append(rel(root,p))
    return sorted(set(hits))


def script_paths(root: Path):
    return sorted((root/'scripts').glob('*.py')) if (root/'scripts').exists() else []


def strong_parser_backend(root: Path):
    strong=[]
    backend_terms=['@babel/parser','typescript.createprogram','require(\"typescript\")','require(\"@babel/parser\")','tree_sitter.Parser','tree-sitter-cli','swc.parse','esbuild.transform','acorn.parse','espree.parse','recast.parse','jscodeshift']
    excluded={'extreme_skills_review.py','second_pass_reverse_audit.py','skill_dispatcher.py','skill_trigger_tester.py','verify_extreme_review_assets.py','verify_second_pass_assets.py','package_self_check.py','strict_quality_gate.py','document_fingerprint_checker.py'}
    for p in script_paths(root):
        if p.name in excluded:
            continue
        txt=(p.name+'\n'+read(p)).lower()
        # Count only actual backend-style files/imports, not generic review wording.
        filename_backend=any(k in p.name.lower() for k in ['parser','backend','ast','taint','dataflow','source_sink'])
        if filename_backend and any(t.lower() in txt for t in backend_terms) and ('import ' in txt or 'require(' in txt or 'subprocess' in txt or 'node ' in txt):
            strong.append(rel(root,p))
    return strong


def strong_runtime_bridge(root: Path):
    strong=[]
    runtime_terms=['playwright','burp','har','browser','trace','chromium','firefox','webkit']
    for p in script_paths(root):
        txt=(p.name+'\n'+read(p)).lower()
        if any(t in txt for t in runtime_terms) and ('import ' in txt or 'subprocess' in txt or 'async ' in txt or 'requests' in txt or 'browser' in txt):
            # Exclude generic review scripts that merely mention terms in tables.
            if p.name in {'extreme_skills_review.py','second_pass_reverse_audit.py','skill_dispatcher.py','skill_trigger_tester.py','verify_extreme_review_assets.py','verify_second_pass_assets.py','package_self_check.py','strict_quality_gate.py','document_fingerprint_checker.py'}:
                continue
            strong.append(rel(root,p))
    return strong


def strong_detector(root: Path):
    strong=[]
    detector_terms=['detector','source_sink','taint','authz','tenant','idor','xss','prototype','postmessage','graphql','websocket']
    for p in script_paths(root):
        txt=(p.name+'\n'+read(p)).lower()
        if any(t in txt for t in detector_terms) and ('def ' in txt or 'class ' in txt):
            if p.name in {'extreme_skills_review.py','second_pass_reverse_audit.py','skill_dispatcher.py','skill_trigger_tester.py','verify_extreme_review_assets.py','verify_second_pass_assets.py','package_self_check.py','strict_quality_gate.py','document_fingerprint_checker.py'}:
                continue
            strong.append(rel(root,p))
    return strong


def fixture_categories(root: Path):
    out={}
    froot=root/'fixtures'
    if not froot.exists(): return out
    for d in froot.iterdir():
        if d.is_dir():
            out[d.name]=[rel(root,p) for p in d.rglob('*') if p.is_file()]
    return out


def has_dashboard(root: Path):
    return [rel(root,p) for p in files(root) if 'dashboard' in rel(root,p).lower()]


def has_report_mapping(root: Path):
    hits=grep(root,['report template','report mapping','报告模板','final-report','extreme-skills-review-report'])
    return hits


def evidence_status(root: Path, name: str, category: str):
    terms=[]
    # split bilingual capability name into searchable tokens
    for token in re.findall(r'[A-Za-z][A-Za-z0-9_.+-]{2,}|[\u4e00-\u9fff]{2,}', name):
        terms.append(token)
    hits=grep(root, terms[:8]) if terms else []
    parsers=strong_parser_backend(root)
    runtime=strong_runtime_bridge(root)
    detectors=strong_detector(root)
    fixtures=fixture_categories(root)
    tests=grep(root/'tests', terms[:5]) if (root/'tests').exists() and terms else []
    dashboard=has_dashboard(root)
    report=has_report_mapping(root)
    quality=[rel(root,p) for p in [root/'scripts/strict_quality_gate.py', root/'docs/QUALITY_GATE_SPEC.md'] if p.exists()]
    schema=[rel(root,p) for p in [root/'schemas/evidence-manifest.schema.json', root/'schemas/extreme-review.schema.json', root/'schemas/second-pass-review.schema.json'] if p.exists()]

    if category == 'collection':
        if any(k in name.lower() for k in ['runtime','登录态','多角色','多租户']):
            real=runtime
        else:
            real=[rel(root,p) for p in script_paths(root) if any(k in p.name.lower() for k in ['asset','extract','source','map','chunk','crawl','collector']) and p.name not in {'extreme_skills_review.py','second_pass_reverse_audit.py'}]
        if real and tests:
            status='partial'
        elif real:
            status='partial'
        elif hits:
            status='doc-only'
        else:
            status='missing'
        return status, hits[:6], real[:5], tests[:5]

    if category == 'audit':
        lower=name.lower()
        requires_parser=any(k in lower for k in ['babel','typescript','tree-sitter','source map','resolver','dataflow','taint','source-sink']) or any(k in name for k in ['语义','映射','是否真实存在'])
        if 'quality gate' in lower or 'report template' in lower or 'dashboard' in lower:
            real = quality if 'quality' in lower else (report if 'report' in lower else dashboard)
        elif any(k in lower for k in ['正样本','负样本','blocked','needs_review']):
            real=[]
            for cat,paths in fixtures.items():
                if ('positive' in cat and '正样本' in name) or ('negative' in cat and '负样本' in name) or ('blocked' in cat and 'blocked' in lower) or ('needs-review' in cat and 'needs_review' in lower):
                    real += paths
        elif '证据' in name or 'evidence' in lower:
            real=schema
        elif requires_parser:
            real=parsers
        else:
            real=detectors
        if real and tests and (not requires_parser or parsers):
            status='partial'
        elif real:
            status='partial'
        elif hits:
            status='doc-only'
        else:
            status='missing'
        return status, hits[:6], real[:5], tests[:5]

    if category == 'severe':
        # A severe chain is only covered if there is a detector and evidence/dynamic support.
        if detectors and (runtime or schema) and tests:
            status='partial'
        elif hits:
            status='doc-only'
        else:
            status='missing'
        return status, hits[:6], detectors[:5], tests[:5]

    if category == 'obscure':
        if hits:
            status='doc-only'
        else:
            status='missing'
        return status, hits[:6], [], tests[:5]

    return '未证实', hits[:6], [], tests[:5]


def original_score(root: Path):
    p=root/'tests/last-extreme-review.json'
    if p.exists():
        try:
            return json.loads(read(p)).get('scores',{})
        except Exception:
            pass
    return {}


def corrected_scores(root: Path):
    parsers=strong_parser_backend(root)
    runtime=strong_runtime_bridge(root)
    detectors=strong_detector(root)
    fixtures=fixture_categories(root)
    schema=(root/'schemas/evidence-manifest.schema.json').exists()
    # Very strict caps requested by the second-pass audit prompt.
    structure=8 if len([d for d in root.glob('[0-9][0-9]-*') if (d/'SKILL.md').exists()]) >= 10 else 5
    info=4 if grep(root,['信息收集','HAR','Burp','Playwright','子域名']) else 2
    js_collection=4 if grep(root,['Source Map','chunk','asset-manifest','Service Worker','WebSocket']) else 2
    semantic=2 if not parsers else 8
    severe=5 if not detectors else 10
    dynamic=2 if not runtime else 6
    tests=4 if fixtures and (root/'tests').exists() else 2
    knowledge=3 if (root/'knowledge').exists() and (root/'templates').exists() else 1
    scores={'Skills 包结构':structure,'信息收集能力':info,'JS 收集能力':js_collection,'JS AST / 语义审计能力':semantic,'严重 JS 漏洞发现能力':severe,'动态验证与证据链':dynamic,'测试与回放':tests,'知识库与模板保真度':knowledge}
    scores['总分']=sum(scores.values())
    return scores


def table(headers, rows):
    out=['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']
    for row in rows:
        out.append('| '+' | '.join(str(x).replace('\n',' ').replace('|','\\|') for x in row)+' |')
    return '\n'.join(out)


def build(root: Path):
    result={'ok':True,'package':{'root':str(root),'file_count':len(files(root)),'skill_count':len([d for d in root.glob('[0-9][0-9]-*') if (d/'SKILL.md').exists()])},'status_terms':STATUS_TERMS}
    parsers=strong_parser_backend(root); runtime=strong_runtime_bridge(root); detectors=strong_detector(root)
    fixtures=fixture_categories(root)
    result['runtime_evidence']={'parser_backend':parsers,'runtime_bridge':runtime,'detectors':detectors,'fixture_categories':fixtures,'dashboard':has_dashboard(root)}

    # 1. Original conclusion recheck
    conclusion_rows=[]
    for item in load_json(root,'data/second_pass_original_conclusion_checks.json'):
        fe=item['file_evidence']
        # file evidence may be semicolon-separated
        fe_ok=[]; fe_missing=[]
        for part in re.split(r';\s*', fe):
            if not part: continue
            if (root/part).exists(): fe_ok.append(part)
            else: fe_missing.append(part)
        te=item['test_evidence']
        te_ok=[]; te_missing=[]
        for part in re.split(r';\s*', te):
            if not part: continue
            if (root/part).exists(): te_ok.append(part)
            else: te_missing.append(part)
        hallucination='是' if fe_missing or ('无 ' in te or '缺 ' in te) else '可能' if not te_ok else '否'
        need=[]
        if fe_missing: need.append('补文件证据: '+','.join(fe_missing))
        if not te_ok: need.append('补测试证据: '+te)
        conclusion_rows.append([item['original_conclusion'],'是: '+','.join(fe_ok) if fe_ok else '否','是: '+','.join(te_ok) if te_ok else '否/证据不足',hallucination,item['corrected_conclusion'],'；'.join(need) or '保持证据链'])
    result['conclusion_recheck_rows']=conclusion_rows

    # 2. JS collection
    rows=[]
    prev_names='\n'.join(x.get('name','') for x in load_json(root,'data/js_collection_points.json'))
    for item in load_json(root,'data/second_pass_js_collection_points.json'):
        st,hits,real,tests=evidence_status(root,item['name'],'collection')
        original='是' if item['name'] in prev_names or any(tok.lower() in prev_names.lower() for tok in item['name'].replace('/',' ').split() if len(tok)>3) else '否/未直接覆盖'
        leak_eval='是' if original.startswith('否') or st in {'missing'} else '否' if st!='doc-only' else '可能'
        rows.append([item['name'],original,('是: '+','.join(real[:3])) if real else ('仅文档: '+','.join(hits[:3]) if hits else '否'),leak_eval,f'{st}；没有真实采集器/ledger/失败处理时不得标 ready'])
    result['js_collection_reverse_rows']=rows

    # 3. JS audit
    rows=[]
    for item in load_json(root,'data/second_pass_js_audit_capabilities.json'):
        st,hits,real,tests=evidence_status(root,item['name'],'audit')
        original='未证实'
        if hits: original='原评估可能写为覆盖/纳入评审'
        high='是' if st in {'doc-only','missing'} and any(k in item['name'] for k in ['真实存在','source-sink','taint','detector','resolver','AST','Compiler','tree-sitter']) else '否'
        fix='接入真实 parser/backend/detector，补 positive/negative/blocked/needs_review，绑定 quality/report/dashboard' if high=='是' or st in {'missing','doc-only'} else '补齐端到端测试'
        evidence=','.join(real[:4]) if real else (','.join(hits[:4]) if hits else '未证实')
        rows.append([item['name'],original,evidence,high,st if st!='partial' else 'partial；仍需端到端验证',fix])
    result['js_audit_reverse_rows']=rows

    # 4. Severe JS chains
    rows=[]
    for item in load_json(root,'data/second_pass_severe_js_chains.json'):
        st,hits,real,tests=evidence_status(root,item['name'],'severe')
        detector='是: '+','.join(real[:3]) if real else '否'
        dyn='是: '+','.join(runtime[:3]) if runtime else '否，未动态验证'
        tmpl='是' if (root/'templates/single-vulnerability-validation-22-fields.md').exists() or (root/'templates/candidate-vulnerability.md').exists() else '否'
        risk='高：'+('只有知识/模板，没有 detector 与 role/tenant replay' if st=='doc-only' else '完全未证实或缺动态验证')
        original='是/知识链可能覆盖' if hits else '否/未证实'
        rows.append([item['name'],original,detector,dyn,tmpl,risk])
    result['severe_chain_reverse_rows']=rows

    # 5. File coverage
    file_rows=[]
    important_dirs=['00-js-master-dispatcher','01-js-scope-evidence-quality-gate','02-js-structure-runtime-graph','03-js-source-sink-authz-graph','04-js-config-dependency-framework','05-js-frontend-build-exposure','06-js-high-risk-candidate-hunter','07-js-dynamic-validator','08-js-evidence-manifest-gate','09-js-reverse-review-chain-audit','10-js-final-report','11-js-special-targets','12-js-skills-extreme-reviewer','13-js-skills-second-pass-reverse-auditor','docs','scripts','schemas','templates','tests','fixtures','knowledge','data','dashboard','reports']
    previous_report=read(root/'tests/last-extreme-review.md')+read(root/'tests/last-extreme-review.json')
    for d in important_dirs:
        p=root/d
        exists=p.exists()
        cited=d in previous_report
        if not exists:
            file_rows.append([d,'否/不存在','否','可能遗漏','缺少该目录或能力承载'])
        elif p.is_dir():
            count=len([x for x in p.rglob('*') if x.is_file()])
            file_rows.append([d,f'是，{count} 个文件','是' if cited else '否/未直接引用','可能' if not cited else '低', '需要逐文件审查' if count>5 and not cited else '已纳入二次文件级清点'])
        else:
            file_rows.append([d,'是','是' if cited else '否','低' if cited else '可能','单文件检查'])
    # add all files concise rows
    for p in files(root):
        rp=rel(root,p)
        cited=rp in previous_report or p.name in previous_report
        file_rows.append([rp,'是','是' if cited else '否','可能' if not cited and p.suffix in {'.py','.json','.md'} else '低','二次审计已列入文件清单；需要人工抽查内容' if not cited else '已被原评估引用'])
    result['file_coverage_rows']=file_rows

    # 6. Score reverse
    orig=original_score(root); corr=corrected_scores(root)
    score_map=[('Skills 包结构','structure',10),('信息收集能力','info_collection',10),('JS 收集能力','js_collection',15),('JS AST / 语义审计能力','semantic_audit',20),('严重 JS 漏洞发现能力','severe_vuln',20),('动态验证与证据链','dynamic_evidence',10),('测试与回放','tests_replay',10),('知识库与模板保真度','knowledge_templates',5)]
    score_rows=[]
    for label,key,maxv in score_map:
        ov=orig.get(key,'未读取')
        cv=corr[label]
        inflated='是' if isinstance(ov,int) and ov>cv else '否/未证实'
        reason=[]
        if label=='JS AST / 语义审计能力' and not parsers: reason.append('缺真实 AST/parser backend')
        if label=='动态验证与证据链' and not runtime: reason.append('缺 Playwright/Burp/HAR bridge')
        if label=='严重 JS 漏洞发现能力' and not detectors: reason.append('缺 detector 级实现')
        if label=='测试与回放': reason.append('缺真实 OSS replay 与完整样本矩阵')
        if label=='JS 收集能力': reason.append('多数为文档矩阵，缺真实 collector/ledger')
        if label=='知识库与模板保真度': reason.append('文件存在但缺强制索引调用证明')
        if not reason: reason.append('按二次证据保守降级')
        score_rows.append([label,ov,inflated,'；'.join(reason),cv])
    score_rows.append(['总分',orig.get('total','未读取'),'是' if isinstance(orig.get('total'),int) and orig.get('total')>corr['总分'] else '否/未证实','文档/模板/矩阵不能替代真实实现分',corr['总分']])
    result['score_reverse_rows']=score_rows
    result['corrected_scores']=corr

    # 7. Fix item executability
    fixes=[]
    p0=[
        ('P0-2PASS-01','接入真实 JS/TS parser backend','scripts/parser_backends/js_ts_parser_bridge.py','tests/parser-backend/positive-negative-blocked-review.json','python scripts/parser_backends/js_ts_parser_bridge.py --self-test','输出 AST/route/wrapper/source-sink JSON，失败时降级为 unavailable','删除新增 backend 并恢复 dispatcher 旧链路'),
        ('P0-2PASS-02','接入 source map 原始映射与 stale map 检测','scripts/sourcemap_runtime_parser.py','fixtures/second-pass-positive/stale-sourcemap.json','python scripts/sourcemap_runtime_parser.py --self-test','能输出 sources/sourcesContent/originalPath/buildId/hash ledger','回滚该脚本与新增 manifest 字段'),
        ('P0-2PASS-03','接入 Playwright/Burp/HAR 只读运行态 bridge','scripts/runtime_evidence_bridge.py','tests/runtime-bridge/har-playwright-fixture.json','python scripts/runtime_evidence_bridge.py --availability-check','输出 HAR、截图、trace、role/tenant asset diff，不做破坏性请求','禁用 bridge 并回退到 static-only'),
        ('P0-2PASS-04','拆分严重 JS 漏洞 detector，不再共享候选规则','scripts/detectors/js_*_detector.py','fixtures/detectors/{positive,negative,blocked,needs_review}.json','python scripts/detector_harness.py --all','每个 detector 输出 evidence manifest 与降级原因','保留模板，禁用 detector 注册'),
        ('P0-2PASS-05','把 detector→manifest→quality→report→dashboard 闭环打通','scripts/report_mapping_checker.py','tests/end-to-end/detector-to-report.json','python scripts/report_mapping_checker.py .','每条 verified 都能映射到 report section 与 quality decision','回滚 dashboard/report mapping，不删知识库/模板')]
    p1=[
        ('P1-2PASS-01','补 30 个 JS 收集点真实 fixture','fixtures/js-collection/','tests/js-collection-matrix.json','python scripts/collection_harness.py --fixtures fixtures/js-collection','每个收集点至少 1 正样本和 1 失败处理样本','保留原 data，删除新增 fixture 注册'),
        ('P1-2PASS-02','补 role/tenant/chunk diff replay','fixtures/runtime-role-tenant/','tests/runtime-role-tenant-replay.json','python scripts/runtime_diff_harness.py --fixtures fixtures/runtime-role-tenant','输出登录前/后、多角色、多租户 asset 与 endpoint diff','禁用 runtime diff harness'),
        ('P1-2PASS-03','补偏门 40 点 needs_review 流程','data/second_pass_unconventional_js_audit_points.json','fixtures/second-pass-needs-review/*.json','python scripts/second_pass_reverse_audit.py .','偏门点不能 silent miss，至少进入 needs_review','回滚新增偏门 fixtures'),
        ('P1-2PASS-04','补知识库/template index checker','scripts/index_binding_checker.py','tests/index-binding.json','python scripts/index_binding_checker.py .','knowledge/template/schema/report 全部有引用与冲突处理','禁用 checker，不删除知识库/模板')]
    p2=[
        ('P2-2PASS-01','补 dashboard 文件级 drill-down','dashboard/index.html','tests/dashboard-smoke.json','python scripts/dashboard_generator.py --self-test','展示 File→Finding→Evidence→Quality→Report','回滚 dashboard 文件'),
        ('P2-2PASS-02','补评分防虚高说明与二次反审模板','docs/SECOND_PASS_REVERSE_AUDIT.md','tests/last-second-pass-review.md','python scripts/second_pass_reverse_audit.py . --markdown tests/last-second-pass-review.md','评分中明确 doc-only/candidate-only/未动态验证','保留旧评分但标记过期')]
    for item in p0+p1+p2:
        num,prob,mod,test,cmd,acc,rollback=item
        fixes.append([num,'是',f'需要新增/修改 {mod}；测试 {test}；命令 {cmd}；回滚 {rollback}','修改文件/新增文件/测试/验收/回滚已列出；必须声明不删除知识库和漏洞模板、不削弱原有 Skills 能力'])
    result['fix_executability_rows']=fixes

    # 8. Unconventional points
    rows=[]
    for item in load_json(root,'data/second_pass_unconventional_js_audit_points.json'):
        st,hits,real,tests=evidence_status(root,item['name'],'obscure')
        rows.append([item['name'],'否/未充分覆盖' if st=='missing' else '可能仅文档覆盖',st,'; '.join(item['add_to_files']),'新增 needs_review fixture + role/tenant/runtime replay'])
    result['unconventional_rows']=rows

    # 9. Final corrected assessment
    result['final_assessment']={
        'corrected_total_score':corr['总分'],
        'is_world_class':'否',
        'core_defects':['缺真实 Babel/TypeScript/tree-sitter parser backend','缺 Playwright/Burp/HAR runtime evidence bridge','缺 source-sink/dataflow/auth/tenant-aware detector','缺严重 JS 漏洞 detector 级正负阻断复核样本','缺多角色、多租户 replay','缺真实 OSS replay','缺 dashboard/report 强绑定','第一轮评分将文档矩阵计入实现强度，存在虚高'],
        'p0':['parser backend','sourcemap parser','runtime bridge','detector split','evidence/report/dashboard closure'],
        'p1':['JS 收集 fixture 矩阵','role/tenant replay','偏门 needs_review','knowledge/template index checker'],
        'p2':['dashboard drill-down','评分防虚高文档'],
        'top_false_negatives':['role-only chunk','tenant-only endpoint','stale sourcemap','GraphQL hidden mutation','WebSocket authz bypass','postMessage token leak','Service Worker stale cache poisoning','Electron preload IPC','Browser extension externally_connectable','mobile WebView bridge'],
        'top_false_positives':['客户端隐藏 endpoint 误报为越权','前端 role flag 误报为后端权限绕过','source map 暴露误报为 secret 泄露','DOM sink 未确认可控输入','CORS header 未确认可利用','GraphQL mutation 未确认鉴权缺陷','WebSocket send 未确认跨用户访问','open redirect 未形成 OAuth chain','package risk 未确认依赖来源','feature flag 未确认生产可达'],
        'top_hallucination_positions':['README 愿景','SKILL.md 工具依赖声明','data 能力矩阵','templates 漏洞报告字段','tests trigger 通过','fixtures 示例存在','Playwright/Burp/HAR 词汇出现','Babel/TS/tree-sitter 词汇出现','quality gate 文档','last-extreme-review 自动分数'],
        'shortest_path':'先补 parser backend、runtime bridge、detector harness、evidence schema/report mapping，再补 role/tenant replay 与真实 OSS replay。'
    }
    return result


def markdown(root: Path, result):
    fa=result['final_assessment']; sc=result['corrected_scores']
    parts=[]
    parts.append('# 第二轮反向审查与纠错报告')
    parts.append('\n## 0. 执行摘要\n')
    parts.append(f"修正后总分：{fa['corrected_total_score']}/100。是否达到世界顶级标准：{fa['is_world_class']}。本报告按“无文件证据写未证实、只有文档写 doc-only、regex 写 candidate-only、无动态验证写未动态验证、无 role/tenant replay 写缺少 role/tenant replay”的规则降级第一轮结论。")
    parts.append('\n## 1. 逐条反查第一轮结论\n')
    parts.append(table(['原评估结论','是否有文件证据','是否有测试证据','是否可能幻觉','修正后结论','需要补充的证据'], result['conclusion_recheck_rows']))
    parts.append('\n## 2. JS 收集覆盖反查\n')
    parts.append(table(['JS 收集点','原评估是否覆盖','是否有真实文件证据','是否漏评','补充结论'], result['js_collection_reverse_rows']))
    parts.append('\n## 3. JS 审计语义保真反查\n')
    parts.append(table(['审计能力','原评估判断','真实证据','是否高估','修正判断','必须修复'], result['js_audit_reverse_rows']))
    parts.append('\n## 4. 严重 JS 漏洞链反查\n')
    parts.append(table(['漏洞链','原评估是否覆盖','是否有 detector','是否有动态验证','是否有证据模板','漏报风险修正'], result['severe_chain_reverse_rows']))
    parts.append('\n## 5. 文件级覆盖率反查\n')
    parts.append(table(['文件/目录','是否已审查','原评估是否引用','可能遗漏','补充发现'], result['file_coverage_rows']))
    parts.append('\n## 6. 评分虚高反查\n')
    parts.append(table(['原评分项','原分数','是否虚高','应扣分原因','修正分数'], result['score_reverse_rows']))
    parts.append('\n## 7. P0/P1/P2 可执行性反查\n')
    parts.append(table(['修复项','是否可执行','缺失内容','修正后的修复项'], result['fix_executability_rows']))
    parts.append('\n## 8. 偏门、冷门、剑走偏锋 JS 审计点反查\n')
    parts.append(table(['偏门审计点','原评估是否覆盖','当前 Skills 是否支持','应加入哪个文件','应加入什么测试'], result['unconventional_rows']))
    parts.append('\n## 9. 修正后的最终评估\n')
    parts.append(f"修正后的总分：{fa['corrected_total_score']}/100。")
    parts.append('\n### 核心缺陷\n' + '\n'.join(f'- {x}' for x in fa['core_defects']))
    parts.append('\n### 修正后的 P0 修复清单\n' + '\n'.join(f'- {x}' for x in fa['p0']))
    parts.append('\n### 修正后的 P1 修复清单\n' + '\n'.join(f'- {x}' for x in fa['p1']))
    parts.append('\n### 修正后的 P2 修复清单\n' + '\n'.join(f'- {x}' for x in fa['p2']))
    parts.append('\n### 当前最容易漏报的 10 类严重 JS 漏洞\n' + '\n'.join(f'- {x}' for x in fa['top_false_negatives']))
    parts.append('\n### 当前最容易误报的 10 类 JS 漏洞\n' + '\n'.join(f'- {x}' for x in fa['top_false_positives']))
    parts.append('\n### 当前最容易造成 AI 幻觉的 10 个位置\n' + '\n'.join(f'- {x}' for x in fa['top_hallucination_positions']))
    parts.append('\n### 最短补强路径\n' + fa['shortest_path'])
    parts.append('\n### 是否达到世界顶级标准\n否。当前包已经具备二次反审、矩阵、模板、schema 和自检承载，但缺少真实 parser backend、动态运行态桥接、detector 级证据闭环和真实 replay。')
    return '\n'.join(parts)+'\n'


def main():
    ap=argparse.ArgumentParser(description='Second-pass reverse auditor for JS security Claude Skills assessment fidelity')
    ap.add_argument('root', nargs='?', default='.')
    ap.add_argument('--json-out')
    ap.add_argument('--markdown')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    if not root.exists():
        print(json.dumps({'ok':False,'error':f'root not found: {root}'}, ensure_ascii=False)); return 2
    result=build(root)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    if args.markdown:
        Path(args.markdown).write_text(markdown(root,result), encoding='utf-8')
    print(json.dumps({'ok':True,'root':str(root),'corrected_total_score':result['final_assessment']['corrected_total_score'],'json_out':args.json_out,'markdown':args.markdown,'parser_backend_evidence':result['runtime_evidence']['parser_backend'],'runtime_bridge_evidence':result['runtime_evidence']['runtime_bridge'],'detector_evidence':result['runtime_evidence']['detectors']}, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
