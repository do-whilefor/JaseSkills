# 质量门禁清单

> 任一必须项未通过，不得交付最终 SSRF 动态验证报告。

## A. TXT 复刻门禁

- [ ] 已读取原始 TXT，不是只根据标题或记忆生成。
- [ ] 已建立 TXT 到 Skill 映射，覆盖角色与目标、硬边界、动态环境、暴露面、动态验证、变体、严重性、证据链、修复建议、最终输出、反向审判、最终追责。
- [ ] 已明确区分“原文复刻”和“工程化补强”。
- [ ] 未把 case-id 格式、证据文件名、严重性枚举等补强内容伪装成 TXT 原文。
- [ ] 未把 TXT 改成摘要式说明；关键术语保留：canary、marker、candidate、confirmed、blocked、needs_review、source → sink、worker、反例、blocked case。

## B. 边界门禁

- [ ] 只测试当前本地授权项目。
- [ ] 只访问本机 canary、测试容器网络或测试目录 marker 服务。
- [ ] 未访问真实公网敏感地址、云 metadata、真实内网资产、公司内网、第三方服务、生产服务。
- [ ] 未执行 DoS、DDoS、爆破、端口扫描、批量内网探测、破坏数据库、删除数据或影响业务运行的动作。
- [ ] 未做中间人攻击类型验证。
- [ ] 所有验证低频、可回滚、可复现、可证明。

## C. 环境门禁

- [ ] 已识别语言、框架、入口、路由、任务队列、配置、依赖、HTTP 客户端、文件/图片/PDF/HTML/Webhook 模块。
- [ ] 已找到并执行本地启动方式。
- [ ] 已建立本地 canary。
- [ ] canary 至少记录请求时间、路径、方法、请求头、请求体摘要、来源 IP、User-Agent、是否来自目标应用服务端、marker id。
- [ ] 已建立浏览器或 curl 直连 canary 的 baseline 反例。
- [ ] `evidence/ssrf/` 可写入。

## D. 暴露面门禁

- [ ] 未只 grep `url`。
- [ ] 已从业务语义、依赖、代码路径、数据流四个角度梳理。
- [ ] 已检查用户可控 URL 参数：url、uri、link、callback、redirect、webhook、avatar、image、logo、icon、importUrl、feed、rss、target、endpoint、host、domain、proxy、next、return、source、fileUrl、downloadUrl、previewUrl。
- [ ] 已检查隐藏入口：后端隐藏字段、JSON/GraphQL/WebSocket/multipart/YAML/JSON/XML、Markdown/HTML、OpenGraph、图片代理、头像远程拉取、PDF、webhook 测试、OAuth/OIDC/SAML、插件/模板/主题、RSS/Atom、Git 导入、数据源连接、邮件模板、管理后台连接测试、异步 fetch。
- [ ] 已检查依赖层：HTTP client、URL parser、redirect 库、image fetcher、HTML/PDF renderer、XML parser、cloud SDK、webhook SDK、proxy middleware、SSR rendering、headless browser、file importer、archive extractor。
- [ ] 已检查服务端请求 sink。
- [ ] 候选点矩阵字段完整，且每个 candidate 有动态验证计划。

## E. 动态证据门禁

- [ ] 每个 candidate 都有唯一 case-id 和 marker。
- [ ] 每个 confirmed 都有 canary 回连。
- [ ] 每个 confirmed 都能证明回连来自目标应用服务端，而不是浏览器、测试工具或 redirector。
- [ ] 每个 confirmed 的请求时间与触发时间对应。
- [ ] 每个 confirmed 的应用日志与同一 case-id 或同一触发窗口对应。
- [ ] 每个 confirmed 有完整请求样本、响应样本、canary 日志、应用日志、代码调用链。
- [ ] 每个 confirmed 有正例、反例、blocked case。
- [ ] 每个 confirmed 有最小复现步骤和可执行回归测试。
- [ ] 参数保存但未触发服务端请求的 case 未被写成 confirmed。
- [ ] 只有错误提示、超时、DNS 解析或前端请求的 case 未被写成 confirmed。

## F. 严重性门禁

- [ ] 未因只有 URL 参数、HTTP client、前端请求、错误、超时、DNS、理论推测、无 canary 回连而判高危。
- [ ] high/critical 只用于已 confirmed 且满足高危/严重条件的 case。
- [ ] 跨角色、跨租户、worker、管理员预览、后台任务等结论均有动态证据。

## G. 修复与回归门禁

- [ ] 修复建议不是“过滤 URL”一句话。
- [ ] 修复建议覆盖协议白名单、危险 scheme、解析后校验、跳转后校验、DNS/IP 校验、防 DNS rebinding、网段限制、白名单资源 id、webhook 安全、隔离代理、异步审计、tenant 绑定、单元/集成/动态回归测试。
- [ ] 回归测试包含 case-id、入口、角色、租户、参数、marker、触发步骤、预期 canary 行为、预期应用行为、反例、blocked case、成功/失败标准、证据路径。

## H. Skill 工程门禁

- [ ] 只保留 1 个主 Skill。
- [ ] 文件夹名是小写英文短横线，能对应 SSRF canary audit 主题。
- [ ] 不存在空壳目录、空壳文件、重复文件。
- [ ] SKILL.md 包含适用范围、不适用范围、输入要求、输出要求、原文复刻规则、工程化补强规则、核心工作流、分阶段执行步骤、质量门禁、幻觉控制、失败处理、输出格式、自检清单、TXT 映射说明。
- [ ] 模板有可填写字段。
- [ ] checklist 可实际验收。
- [ ] examples 贴近本地 SSRF canary 审计主题。
- [ ] tests 能发现漏复刻、摘要化、幻觉扩展、命名失败、目录臃肿、输入输出缺失、质量门禁缺失、失败处理缺失、映射缺失、补强伪装。
