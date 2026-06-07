#!/usr/bin/env python3
import argparse,json,sys
from pathlib import Path
REQ=['触发条件','授权和禁止条件','输入要求','输出要求','执行步骤','失败处理','质量门槛','测试样例','交接协议','原始来源映射']
ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--out',default='SELFTEST_RESULT.json'); a=ap.parse_args(); r=Path(a.root); res=[]
for p in sorted((r/'skills').glob('*/SKILL.md')):
 t=p.read_text(encoding='utf-8',errors='ignore'); miss=[x for x in REQ if x not in t]; res.append({'skill':str(p.relative_to(r)),'ok':not miss,'missing':miss})
out={'results':res,'extra':{'skill_count':len(res),'templates_min_23':len(list((r/'vulnerability_templates').glob('*.md')))>=23,'template_count':len(list((r/'vulnerability_templates').glob('*.md'))),'schema_exists':(r/'EVIDENCE_MANIFEST_SCHEMA.json').exists(),'quality_script_exists':(r/'scripts/quality_gate_score.py').exists()},'ok':all(x['ok'] for x in res)}; (r/a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); sys.exit(0 if out['ok'] else 2)
