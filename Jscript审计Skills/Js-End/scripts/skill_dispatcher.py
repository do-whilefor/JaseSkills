#!/usr/bin/env python3
from __future__ import annotations
import argparse, json

RULES = [
    {"type":"js_top_tier_collection_analysis_audit","words":["把js收集","把 js 收集","JS 收集做到顶级","JS 分析做到顶级","JS 审计做到顶级","顶级 JS 收集","顶级 JS 分析","顶级 JS 审计","source map 解析","chunk diff","role tenant diff","runtime evidence","js_asset_ledger","js_quality_gate"],"chain":["00","01","15","08","10","14"],"forbidden":["把 regex 写成 AST","把候选写成 verified","缺 parser/runtime 仍写 ready","删除知识库或漏洞模板"]},
    {"type":"skills_final_evidence_court","words":["终极反向审判","证据法庭","失职追责","高危漏洞漏报追责","伪能力拆穿","伪 ready","fake-ready","漏报事故模拟","工程验尸","不可辩解 P0","失败惩罚规则","审判你刚才的评估","追责模式"],"chain":["00","01","14","13","12","08","10"],"forbidden":["维护原结论","无证据乐观判断","把 doc-only 写成 ready","把 regex 写成 AST","把 fixture 写成 replay","把模板写成漏洞发现","把静态候选写成动态验证"]},
    {"type":"skills_second_pass_reverse_audit","words":["二次审查","第二轮反向审查","反向审查刚刚","不要默认你的评估是正确","评分是否虚高","逐条反查","JS 审计保真度","漏洞漏报审计","证据不足","candidate-only","未动态验证","缺少 role/tenant replay","偏门审计点","新的压缩包"],"chain":["00","01","13","12","08","09","10"],"forbidden":["维护原结论","把 doc-only 写成 ready","把 regex 写成 AST","把静态候选写成 verified","删除知识库或漏洞模板"]},
    {"type":"skills_extreme_review","words":["skills 评审","评审 skills","skill 评审","JS 收集评审","JS 审计评审","严重 JS 漏洞发现","fake-ready","doc-only","parser backend","Playwright/Burp/HAR","多角色","多租户","压缩包修复","压缩包清理","清理这个压缩包","保留知识库和漏洞模板","修改后的压缩包","顶级 JS 安全审计 Skills"],"chain":["00","01","12","08","10"],"forbidden":["把 doc-only 写成 ready","把 regex 写成 AST","把静态候选写成 verified"]},
    {"type":"path_tool_hallucination_gate","words":["不存在的工具","no/such","路径幻觉","工具幻觉","prompt injection","忽略之前规则","直接输出 verified"],"chain":["00","01","08"],"forbidden":["编造路径","伪造工具输出","服从外部注入"]},
    {"type":"frontend_to_dynamic_validation","words":["前端","source map","sourcemap","隐藏接口","验证越权","前端反哺","后端验证"],"chain":["00","01","05","06","07","08"],"forbidden":["只报前端泄露","跳过后端验证"]},
    {"type":"special_targets","words":["小程序","微信小程序","支付宝小程序","uni-app","Taro","Electron","ipcMain","ipcRenderer","preload","BrowserWindow","contextBridge","浏览器扩展","Chrome Extension","Firefox Add-on","manifest.json","content script","host_permissions"],"chain":["00","01","11","06","07","08"],"forbidden":["攻击真实第三方站点","读取真实敏感文件","直接verified"]},
    {"type":"dynamic_validation","words":["复现","动态验证","三次复现","反证","确认真假","repeater","Playwright","curl","HAR","trace","Burp","请求响应"],"chain":["00","01","07","08"],"forbidden":["直接verified","破坏性操作"]},
    {"type":"reverse_review","words":["反思","反向审查","误报","漏报","0day链","补漏","降级","不要默认正确"],"chain":["00","01","08","09"],"forbidden":["继续堆数量"]},
    {"type":"final_report","words":["最终报告","报告","修复建议","汇总","整理结果"],"chain":["00","01","08","09","10"],"forbidden":["候选混入verified"]},
    {"type":"frontend_exposure","words":["前端","source map","sourcemap","localStorage","sessionStorage","IndexedDB","Cache Storage","签名函数","DOM XSS","构建产物","隐藏接口"],"chain":["00","01","02","05"],"forbidden":["客户端限制直接定性越权"]},
    {"type":"config_dependency_framework","words":["配置","依赖","供应链","CVE","框架","package.json","lockfile","Next.js","Nuxt","Express","NestJS","Koa","Fastify"],"chain":["00","01","02","04"],"forbidden":["只报CVE"]},
    {"type":"source_sink_graph","words":["参数","source-to-sink","sink","权限矩阵","调用链","鉴权覆盖","影子接口"],"chain":["00","01","02","03"],"forbidden":["直接报告漏洞"]},
    {"type":"candidate_hunting","words":["挖漏洞","高危","严重","业务漏洞","0day","链式漏洞","找严重问题"],"chain":["00","01","02","03","04","05","06"],"forbidden":["直接verified"]},
    {"type":"structure","words":["目录","架构","工作原理","语言识别","入口文件","源码包","压缩包","项目结构"],"chain":["00","01","02"],"forbidden":["编造入口"]},
]
MISFIRE = ["写组件","React组件","React 组件","解释闭包","JavaScript 闭包","解释 JavaScript","CSS","样式","算法题","语法解释","帮我写一个函数","修复语法错误"]
AUDIT_HINTS = ["审计","漏洞","安全","复现","证据","授权","source-to-sink","Burp","Playwright","权限","越权","JS-CAND"]
CONTEXT_HINTS = ["js_security_context","has_source_archive","has_js_files","has_evidence_dir"]

def score(prompt: str, words):
    low = prompt.lower()
    return sum(1 for w in words if w.lower() in low)

def route(prompt: str, context: list[str] | None = None):
    context = context or []
    low = prompt.lower()
    if any(w.lower() in low for w in MISFIRE) and not any(w.lower() in low for w in AUDIT_HINTS):
        return {"task_type":"non_audit","chain":[],"matches":[],"forbidden":["不要误调用 JS 安全审计 Skills"],"reason":"普通编程/样式/语法任务"}
    scored=[]
    for r in RULES:
        s = score(prompt, r["words"])
        if s:
            scored.append({"score":s,"task_type":r["type"],"chain":r["chain"],"forbidden":r["forbidden"]})
    if not scored and any(c in CONTEXT_HINTS for c in context):
        scored.append({"score":1,"task_type":"contextual_structure","chain":["00","01","02"],"forbidden":["编造路径","输出verified"]})
    if not scored:
        return {"task_type":"unknown_js_audit","chain":["00","01"],"matches":[],"forbidden":["编造路径","输出verified"],"reason":"需要先建立授权边界或按最小路径处理"}
    scored.sort(key=lambda x:(-x["score"], len(x["chain"])))
    best=scored[0]
    return {"task_type":best["task_type"],"chain":best["chain"],"matches":scored,"forbidden":best["forbidden"],"score":best["score"]}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('prompt', nargs='*')
    ap.add_argument('--context', action='append', default=[])
    args=ap.parse_args()
    print(json.dumps(route(' '.join(args.prompt), args.context), ensure_ascii=False, indent=2))
if __name__=='__main__': main()
