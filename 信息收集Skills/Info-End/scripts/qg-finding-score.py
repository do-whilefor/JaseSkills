#!/usr/bin/env python3
from __future__ import annotations
import argparse, re
from pathlib import Path
RAW_SECRET=[
    re.compile(r'sk_live_[A-Za-z0-9]{12,}'),
    re.compile(r'eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----'),
    re.compile(r'(?:mysql|postgres|postgresql|mongodb|redis)://[^\s:]+:[^\s@]+@',re.I),
    re.compile(r'(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{20,}')
]
NEG={
 'no_dynamic': re.compile(r'(无动态证据|未动态验证|只有静态|静态候选|关键词命中|运行态不可访问)'),
 'no_repro': re.compile(r'(无法稳定复现|未复现|复现次数[:：]\s*(0|1)\b|只复现\s*1)'),
 'out_scope': re.compile(r'(超出授权|公网未知|非授权|第三方真实业务)'),
 'no_impact': re.compile(r'(无实际影响|缺少影响证明|没有安全影响)'),
}
def has_any(text, words): return any(w.lower() in text.lower() for w in words)
def has_regex(text, pat): return bool(re.search(pat, text, re.I|re.S))
def split_findings(text):
    pat=re.compile(r'(?m)^#{2,4}\s+(?:F[-_ ]?\d+|发现\s*\d*|Finding\s*\d*|高风险|中风险|低风险|候选)[^\n]*')
    ms=list(pat.finditer(text))
    if not ms: return [('REPORT', text)]
    return [(m.group(0).strip('# ').strip(), text[m.start():(ms[i+1].start() if i+1<len(ms) else len(text))]) for i,m in enumerate(ms)]
def eval_one(body):
    rows=[]
    if NEG['out_scope'].search(body): rows.append(('QG-01 授权范围','FAIL','出现超出授权/公网未知/第三方真实业务信号'))
    elif has_any(body,['授权范围','本机','localhost','127.0.0.1','项目根目录','Base URL','授权容器网络']): rows.append(('QG-01 授权范围','PASS','存在范围字段或本机/授权证据'))
    else: rows.append(('QG-01 授权范围','UNKNOWN','未看到明确授权范围'))
    if NEG['no_dynamic'].search(body): rows.append(('QG-02 动态证据','FAIL','文本显示缺少动态验证或只有静态候选'))
    elif has_any(body,['运行态访问路径','动态证据','请求摘要','响应摘要','状态码','Content-Type','响应大小']) and has_regex(body,r'https?://|/[^\s`]+'): rows.append(('QG-02 动态证据','PASS','存在运行态路径和请求/响应摘要字段'))
    else: rows.append(('QG-02 动态证据','UNKNOWN','缺少运行态路径或请求/响应摘要'))
    if NEG['no_repro'].search(body): rows.append(('QG-03 可复现','FAIL','复现不足或无法稳定复现'))
    elif has_regex(body,r'复现次数[:：]?\s*[23]\b|重复验证.*[23]|至少复现\s*[23]'): rows.append(('QG-03 可复现','PASS','复现次数达到 2-3 次'))
    else: rows.append(('QG-03 可复现','UNKNOWN','未明确复现次数'))
    if has_any(body,['未认证','低权限','非预期可见','角色要求','认证要求','角色差异']) and '管理员预期可见' not in body: rows.append(('QG-04 非预期可见','PASS','存在认证/角色/非预期可见判断'))
    elif '管理员预期可见' in body: rows.append(('QG-04 非预期可见','FAIL','仅管理员预期可见，默认不可报告'))
    else: rows.append(('QG-04 非预期可见','UNKNOWN','缺少认证或角色要求'))
    if has_any(body,['脱敏证据','信息暴露类型','关键字段','字段名','响应摘要','长度','SHA256','敏感']) and not has_any(body,['没有敏感内容','空页面']): rows.append(('QG-05 实际信息','PASS','存在实际信息内容或脱敏证据字段'))
    else: rows.append(('QG-05 实际信息','UNKNOWN','未证明包含实际信息内容'))
    if NEG['no_impact'].search(body): rows.append(('QG-06 影响判断','FAIL','文本显示缺少影响证明'))
    elif has_any(body,['影响分析','影响对象','安全影响','风险等级','风险']): rows.append(('QG-06 影响判断','PASS','存在影响和风险字段'))
    else: rows.append(('QG-06 影响判断','UNKNOWN','缺少影响判断'))
    if any(p.search(body) for p in RAW_SECRET): rows.append(('QG-07 证据脱敏','FAIL','疑似完整敏感值未脱敏'))
    elif has_any(body,['脱敏','SHA256','长度','****','hash','指纹']): rows.append(('QG-07 证据脱敏','PASS','存在脱敏/长度/hash 字段'))
    else: rows.append(('QG-07 证据脱敏','UNKNOWN','未看到脱敏证据'))
    if has_any(body,['代码证据','配置来源','代码或配置来源','源码','文件：','前端产物','部署','Docker','compose']): rows.append(('QG-08 来源关联','PASS','存在代码/配置/部署/前端来源'))
    else: rows.append(('QG-08 来源关联','UNKNOWN','缺少来源关联'))
    if has_any(body,['反证','误报','测试数据','开发环境','预期可见','不可报告原因','为什么现在能报告','为什么现在不能报告']): rows.append(('QG-09 反证完成','PASS','存在反证或不可报告判断'))
    else: rows.append(('QG-09 反证完成','UNKNOWN','缺少反证判断'))
    if has_any(body,['遗漏反思','误报反思','剑走偏锋','反思结果','下一轮最小动态验证']): rows.append(('QG-10 反思完成','PASS','存在反思字段'))
    else: rows.append(('QG-10 反思完成','UNKNOWN','缺少三轮反思或补充验证'))
    fail=sum(1 for _,s,_ in rows if s=='FAIL'); unk=sum(1 for _,s,_ in rows if s=='UNKNOWN')
    verdict='FAIL：不可交付/不可报告，必须修复 FAIL 项或降级' if fail else ('UNKNOWN：降级为待确认，补齐 UNKNOWN 项后再复核' if unk else 'PASS：证据结构满足门槛，但仍需人工复核真实性')
    return rows, verdict
def main():
    ap=argparse.ArgumentParser(description='Per-finding QG-01..QG-10 scorer. Structural aid only; does not prove vulnerability.')
    ap.add_argument('report'); ap.add_argument('-o','--out',default='qg-finding-score.md')
    args=ap.parse_args(); text=Path(args.report).read_text(errors='ignore')
    out=['# QG-01 到 QG-10 逐发现评分\n','说明：该脚本是结构化评分辅助，不替代人工判断。FAIL 必须修复；UNKNOWN 必须补证或降级待确认。\n']
    for title,body in split_findings(text):
        rows,verdict=eval_one(body); out += [f'## {title}\n',f'- 总评：{verdict}\n','| 门禁 | 结果 | 原因 |','|---|---|---|']
        out += [f'| {q} | {s} | {r} |' for q,s,r in rows]; out.append('')
    Path(args.out).write_text('\n'.join(out),encoding='utf-8'); print(f'Wrote {args.out}')
if __name__=='__main__': main()
