# 20-js-self-audit-verdict

## 定位

本 Skill 是 JS 审计链路的自我追责官。它不评价“看起来强不强”，只检查是否真的有文件、脚本、schema、fixture、运行输出和质量门槛支撑。

## 必查问题

1. 是否真的检查每个 Skill 文件。
2. 是否覆盖 JS 静态收集、动态 chunk、懒加载、真实浏览器交互、登录态、多角色、多租户、service worker、sourcemap、CDN/历史资产、HAR/Burp、缓存资产。
3. 是否覆盖 REST、GraphQL、WebSocket、SSE、gRPC-web、JSON-RPC、axios/fetch wrapper、interceptor、route-component-api mapping、hidden params、backend accepted extra params、Mass Assignment、DTO/model/schema 对齐。
4. 是否覆盖严重漏洞候选、动态验证、证据 manifest、截图、HAR、请求响应、代码位置、调用链。
5. 是否存在把 regex 候选、doc-only 能力、fixture 样本伪装成 ready。

## 输出

- `js_self_audit_matrix.json`：逐项证据、缺口、状态、降级原因、P0 修复项。
- `js_self_audit_matrix.md`：可读追责报告。

## 硬性结论

没有 parser、browser、evidence、replay、quality gate 的链路，不得称为顶级 JS 审计；最多称为候选发现系统。

## P0 修复后的强制规则：自审必须识别能力伪装

`js_self_audit_matrix.py` v2 必须把以下情况判为 P0：只有浏览器计划但无运行证据；无 HAR/trace/screenshot/request-response；无多角色/多租户授权结果；无后端接受性请求/响应；AST backend 有错误或只有 regex 候选；质量门槛未运行。

任何 README、模板、schema、计划文件、文件名或 regex 命中，都不能单独证明能力 ready。
