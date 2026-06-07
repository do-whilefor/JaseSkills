#!/usr/bin/env python3
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    manifest_path=ROOT/'outputs/evidence_manifest.json'
    if not manifest_path.exists():
        print(json.dumps({'status':'blocked','reason':'evidence_manifest_missing'}, ensure_ascii=False, indent=2)); return 2
    data=json.loads(manifest_path.read_text(encoding='utf-8'))
    outdir=ROOT/'outputs/reports'; outdir.mkdir(parents=True, exist_ok=True)
    index=[]
    for c in data.get('candidates',[]):
        status=c.get('state')
        section='confirmed' if status=='confirmed' and c.get('quality_gate_result')=='pass' else 'observation'
        md=f"""# {section.upper()}：{c.get('vulnerability_type')} / {c.get('candidate_id')}

- 状态：{c.get('state')}
- Quality gate：{c.get('quality_gate_score')} / {c.get('quality_gate_result')}
- 代码位置：{c.get('source_file')}:{c.get('source_line')}
- 路由：{c.get('method')} {c.get('route')}
- 参数：{c.get('parameter')}
- 认证/租户/角色：{c.get('auth_context')} / {c.get('tenant_context')} / {c.get('role_context')}
- 请求摘要：{c.get('request_summary')}
- 响应摘要：{c.get('response_summary')}
- 负样本：{c.get('negative_control')}
- 复现次数：{c.get('reproduction_count')}

## 影响
{c.get('impact')}

## 修复建议
{c.get('fix_guidance')}
"""
        p=outdir/f"{c.get('candidate_id','candidate')}.md"; p.write_text(md, encoding='utf-8')
        index.append({'candidate_id':c.get('candidate_id'), 'report':str(p.relative_to(ROOT)), 'section':section})
    (ROOT/'outputs/report_index.json').write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status':'pass','reports':len(index)}, ensure_ascii=False, indent=2)); return 0
if __name__ == '__main__':
    raise SystemExit(main())
