#!/usr/bin/env python3
import sys,json
from pathlib import Path
REQ=['漏洞定义','典型代码模式','典型配置风险','典型路由/参数特征','source/sink 规则','静态候选规则','动态验证规则','非破坏性边界','误报排除','影响证明','代码证据要求','请求/响应证据要求','negative control','evidence manifest 字段','quality gate 分数','报告模板','框架差异化规则']
r=Path(sys.argv[1] if len(sys.argv)>1 else '.'); res=[]
for p in sorted((r/'vulnerability_templates').glob('*.md')):
 t=p.read_text(encoding='utf-8').lower(); miss=[x for x in REQ if x.lower() not in t]; res.append({'file':str(p.relative_to(r)),'ok':not miss,'missing':miss})
print(json.dumps(res,ensure_ascii=False,indent=2)); sys.exit(0 if len(res)==23 and all(x['ok'] for x in res) else 2)
