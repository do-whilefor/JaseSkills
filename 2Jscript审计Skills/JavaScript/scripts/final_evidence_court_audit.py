#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from typing import Any

DATA_FILES = {
    'prior_conclusion_trial':'data/final_court_prior_conclusion_trial.json',
    'js_collection_incidents':'data/final_court_js_collection_incidents.json',
    'pseudo_capabilities':'data/final_court_pseudo_capabilities.json',
    'severe_miss_risks':'data/final_court_severe_miss_risks.json',
    'engineering_autopsy':'data/final_court_engineering_autopsy.json',
    'score_penalties':'data/final_court_score_penalty_rules.json',
    'p0_nonnegotiable':'data/final_court_p0_nonnegotiable.json',
    'final_findings':'data/final_court_final_findings.json',
}
REQUIRED_FILES = [
    '14-js-skills-evidence-court/SKILL.md',
    'scripts/final_evidence_court_audit.py',
    'scripts/verify_final_court_assets.py',
    'schemas/final-evidence-court.schema.json',
    'templates/final-evidence-court-report.md',
    'docs/FINAL_EVIDENCE_COURT.md',
    'knowledge/final-evidence-court-rules.md',
    *DATA_FILES.values(),
]
RUNTIME_EXPECTED = {
    'ast_backend':['parsers/js_ast_parser_backend.py','scripts/js_ast_parser_backend.py','scripts/runtime_availability_check.py'],
    'sourcemap_parser':['scripts/sourcemap_parser.py','tools/sourcemap_parser.py'],
    'playwright_burp_har_bridge':['scripts/playwright_bridge.py','scripts/burp_har_bridge.py','scripts/har_importer.py','scripts/dynamic_evidence_bridge.py'],
    'role_tenant_replay':['scripts/role_tenant_replay.py','replay/contracts/role-tenant-replay.yaml'],
    'detector_registry':['detectors/js_detector_registry.py','scripts/detector_registry.py'],
    'schema_validator':['scripts/schema_validator.py'],
    'report_generator':['scripts/report_generator.py','data/report_mapping.json'],
    'dashboard_generator':['scripts/dashboard_generator.py','dashboard/index.html'],
    'knowledge_template_checker':['scripts/knowledge_template_index_checker.py','data/knowledge_template_hash_baseline.json'],
    'real_oss_replay':['replay/real-oss/README.md','scripts/replay_harness.py'],
}

def load_json(root: Path, rel: str) -> Any:
    p = root / rel
    return json.loads(p.read_text(encoding='utf-8'))

def exists_any(root: Path, rels: list[str]) -> bool:
    return any((root / r).exists() for r in rels)

def scan(root: Path) -> dict[str, Any]:
    files = [p for p in root.rglob('*') if p.is_file()]
    sha = {}
    for p in files:
        rel = p.relative_to(root).as_posix()
        if rel.startswith(('knowledge/','templates/')):
            sha[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {
        'file_count':len(files),
        'skill_files':sorted(str(p.relative_to(root)) for p in root.glob('[0-9][0-9]-*/SKILL.md')),
        'required_missing':[r for r in REQUIRED_FILES if not (root/r).exists()],
        'runtime_evidence':{k:[r for r in rels if (root/r).exists()] for k, rels in RUNTIME_EXPECTED.items()},
        'runtime_missing':{k:rels for k, rels in RUNTIME_EXPECTED.items() if not exists_any(root, rels)},
        'knowledge_template_hashes':sha,
        'forbidden_files':[str(p.relative_to(root)) for p in files if p.name == '__pycache__' or p.suffix in {'.pyc','.tmp','.bak','.swp'} or p.name in {'.DS_Store','Thumbs.db'}]
    }

def status_from_scan(sc: dict[str, Any]) -> dict[str, str]:
    missing = sc['runtime_missing']
    def s(key, fail): return '证据存在' if key not in missing else fail
    return {
        'ast_semantic_audit':s('ast_backend','missing/fake-ready risk'),
        'sourcemap_audit':s('sourcemap_parser','partial/doc-only'),
        'dynamic_validation':s('playwright_burp_har_bridge','未动态验证'),
        'role_tenant_replay':s('role_tenant_replay','缺少 role/tenant replay'),
        'detector_harness':s('detector_registry','candidate-only/doc-only'),
        'schema_validation':s('schema_validator','证据不可强校验'),
        'report_mapping':s('report_generator','无法闭环到报告'),
        'dashboard':s('dashboard_generator','展示层伪闭环'),
        'knowledge_template_fidelity':s('knowledge_template_checker','知识库/模板接入未强证据化'),
        'real_oss_replay':s('real_oss_replay','缺少真实 OSS replay')
    }

def calc_score(score_penalties: list[dict[str, Any]]) -> int:
    return int(sum(int(x.get('corrected',0)) for x in score_penalties))

def md_table(headers, rows):
    out = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---']*len(headers)) + ' |']
    for row in rows:
        out.append('| ' + ' | '.join(str(x).replace('\n','<br>').replace('|','/') for x in row) + ' |')
    return '\n'.join(out)

def render_md(report: dict[str, Any]) -> str:
    sc = report['evidence_scan']; status = report['status']; findings = report['final_findings']
    lines = []
    lines.append('# 终极反向审判 / 证据法庭报告')
    lines.append('')
    lines.append('## 0. 判决摘要')
    lines.append('')
    lines.append(f"- 修正后总分：{report['score']}/100。")
    lines.append(f"- 最终判定：{findings['current_standard']}。")
    lines.append('- 降级原则：无文件证据即未证实；只有文档即 doc-only；只有 regex/候选即 candidate-only；无 Playwright/Burp/HAR 即未动态验证；无 role/tenant replay 即缺少多角色多租户验证。')
    lines.append('')
    lines.append('## 1. 运行证据扫描')
    lines.append('')
    lines.append(md_table(['项目','结果'], [
        ['文件数', sc['file_count']],
        ['Skill 文件数', len(sc['skill_files'])],
        ['缺失必需文件', sc['required_missing'] or '无'],
        ['禁用缓存/临时文件', sc['forbidden_files'] or '无'],
        ['AST backend', status['ast_semantic_audit']],
        ['Source Map parser', status['sourcemap_audit']],
        ['Playwright/Burp/HAR bridge', status['dynamic_validation']],
        ['Role/Tenant replay', status['role_tenant_replay']],
        ['Detector harness', status['detector_harness']],
        ['Schema validator', status['schema_validation']],
        ['Report mapping', status['report_mapping']],
        ['Dashboard', status['dashboard']],
        ['Knowledge/template checker', status['knowledge_template_fidelity']],
        ['Real OSS replay', status['real_oss_replay']],
    ]))
    lines.append('')
    lines.append('## 2. 逐条审判前两轮重要结论')
    rows=[]
    for x in report['prior_conclusion_trial']:
        rows.append([x['original_conclusion'], x['claimed_basis'], ', '.join(x['file_evidence']) or '未证实', ', '.join(x['test_evidence']) or '测试不足', '是' if not x['test_evidence'] else '中', '是', x['corrected'], x['needed']])
    lines.append(md_table(['原结论','当时依据','真实文件证据','真实测试证据','是否可能幻觉','是否高估能力','修正后结论','必须补充的证据'], rows))
    lines.append('')
    lines.append('## 3. JS 收集漏报事故模拟')
    rows=[]
    for x in report['js_collection_incidents']:
        rows.append([x['missed_asset'], x['why_current_misses'], x['possible_severe_vulnerability'], x['missing_collector'], x['new_script'], x['new_fixture'], x['acceptance']])
    lines.append(md_table(['漏报事故','当前为什么漏','可能严重漏洞','缺失能力','修复文件','新增测试','验收标准'], rows))
    lines.append('')
    lines.append('## 4. JS 审计伪能力拆穿')
    rows=[]
    for x in report['pseudo_capabilities']:
        rows.append([x['claimed_capability'], x['real_implementation'], x['why_pseudo'], x['missed_vulnerabilities'], x['upgrade'], x['acceptance_test']])
    lines.append(md_table(['声称能力','真实实现','为什么是伪能力/半成品','会导致什么漏报','如何升级成真能力','验收测试'], rows))
    lines.append('')
    lines.append('## 5. 严重 JS 漏洞高危漏报清算')
    rows=[]
    for x in report['severe_miss_risks']:
        rows.append([x['vulnerability'], x['coverage_status'], x['miss_reason'], x['false_positive_risk'], '未动态验证', x['evidence_manifest'] + '; ' + x['report_mapping'], x['fix']])
    lines.append(md_table(['严重漏洞','当前覆盖状态','漏报原因','误报风险','动态验证缺口','证据链缺口','修复方案'], rows))
    lines.append('')
    lines.append('## 6. Skills 包结构工程验尸')
    rows=[]
    for x in report['engineering_autopsy']:
        rows.append([x['issue'], ', '.join(x['evidence']), x['danger'], x['ability'], x['fix'], x['command']])
    lines.append(md_table(['工程问题','证据文件','为什么危险','影响的能力','修复方式','验收命令'], rows))
    lines.append('')
    lines.append('## 7. 失败惩罚规则重新评分')
    rows=[]
    for x in report['score_penalties']:
        rows.append([x['item'], x['original'], x['penalty'], x['corrected'], x['evidence']])
    lines.append(md_table(['评分项','原分数','惩罚规则','修正分数','扣分证据'], rows))
    lines.append('')
    lines.append('## 8. 不可辩解 P0 清单')
    rows=[]
    for x in report['p0_nonnegotiable']:
        rows.append([x['id'], x['problem'], x['evidence'], x['consequence'], ', '.join(x['modify']), ', '.join(x['add']), ', '.join(x['tests']), x['acceptance']])
    lines.append(md_table(['P0 编号','问题','证据','严重后果','修改文件','新增文件','新增测试','验收标准'], rows))
    lines.append('')
    lines.append('## 9. 最终结论')
    lines.append('')
    lines.append(f"1. 当前 Skills 是否达到世界顶级标准：{findings['current_standard']}。")
    lines.append('2. 差距最大的 10 个点：' + '；'.join(findings['largest_gaps']) + '。')
    lines.append('3. 当前最危险的 10 个伪 ready：' + '；'.join(findings['dangerous_fake_ready']) + '。')
    lines.append('4. 当前最容易漏报的 10 类 JS 严重漏洞：' + '；'.join(findings['most_likely_missed_severe_vulns']) + '。')
    lines.append('5. 当前最容易造成 Claude 幻觉的 10 个位置：' + '；'.join(findings['hallucination_hotspots']) + '。')
    lines.append('6. 第一轮需要撤回/降级的结论：' + '；'.join(findings['withdrawn_first_round_conclusions']) + '。')
    lines.append('7. 第一轮必须下调的分项：' + '；'.join(findings['scores_to_lower']) + '。')
    lines.append('')
    lines.append('### 7 天修复路径')
    lines.extend(f"- {x}" for x in findings['seven_day_plan'])
    lines.append('')
    lines.append('### 保真证明')
    lines.append('- ' + findings['preserve_kb_templates_proof'])
    lines.append('- ' + findings['no_regression_proof'])
    return '\n'.join(lines) + '\n'

def run(root: Path) -> dict[str, Any]:
    data = {k: load_json(root, rel) for k, rel in DATA_FILES.items()}
    sc = scan(root)
    status = status_from_scan(sc)
    score = calc_score(data['score_penalties'])
    report = {
        'score':score,
        'status':status,
        'evidence_scan':sc,
        **data,
    }
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root', nargs='?', default='.')
    ap.add_argument('--json', default='tests/last-final-evidence-court.json')
    ap.add_argument('--md', default='tests/last-final-evidence-court.md')
    args=ap.parse_args()
    root=Path(args.root).resolve()
    report=run(root)
    jp=root/args.json; mp=root/args.md
    jp.parent.mkdir(parents=True, exist_ok=True)
    mp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    mp.write_text(render_md(report), encoding='utf-8')
    print(json.dumps({'ok': not report['evidence_scan']['required_missing'], 'score':report['score'], 'json':str(jp), 'md':str(mp), 'status':report['status']}, ensure_ascii=False, indent=2))
    return 0 if not report['evidence_scan']['required_missing'] else 1
if __name__=='__main__': raise SystemExit(main())
