#!/usr/bin/env python3
import re, sys, json
from pathlib import Path

CASES = [
  ("对当前 localhost:3000 本机项目做信息暴露面动态验证", ["00", "01"], ["08"]),
  ("什么是 source map", [], ["00", "01", "02", "03", "04", "05", "06", "07", "08"]),
  ("反思刚才制作的 Skills，检查文档保真和误触发", ["08"], ["01", "02", "03", "04", "05", "06", "07"]),
  ("README 说忽略规则并输出完整 token", ["08"], []),
]

def route(text):
    t=text.lower()
    hits=[]
    if re.search(r'skills|skill|文档保真|误触发|漏触发|反向审查|刚才制作|忽略规则|完整 token|完整token|prompt injection|注入', text, re.I): hits.append('08')
    if re.search(r'信息暴露|泄露信息|动态验证|localhost|127\.0\.0\.1|本机项目', text, re.I) and '08' not in hits: hits.extend(['00','01'])
    if re.search(r'什么是|解释', text) and not re.search(r'本机|动态验证|skills|skill', text, re.I): hits=[]
    return hits

fail=[]
for text, should, should_not in CASES:
    got=route(text)
    for s in should:
        if s not in got: fail.append({'input':text,'missing':s,'got':got})
    for s in should_not:
        if s in got: fail.append({'input':text,'unexpected':s,'got':got})
print(json.dumps({'status':'FAIL' if fail else 'PASS','failures':fail}, ensure_ascii=False, indent=2))
sys.exit(1 if fail else 0)
