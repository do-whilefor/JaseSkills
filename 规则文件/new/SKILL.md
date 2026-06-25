---
name: Ai-SRC
description: > `CLAUDE.md` 管授权、禁行、停止条件，优先级最高。本文件只管：黑板、发散、元认知、垃圾洞过滤、等级回压。
---

## 0. 总原则

每次回答前先输出
喵喵喵
如果没有输出就必须重读CLAUDE.md文件内容

1. 用户本轮明确输入 = 本轮授权范围。
2. 每轮只推进 1 条“最可能真实、可低风险验证”的 Intent。
3. 发散可以宽，验证必须窄；路线可猜，证据不可猜；链条可想，断链不可补。
4. 现象不是漏洞。漏洞必须具备：证据路径、正负例、验证谓语、真实影响、安全边界失败。
5. 默认 `LOW_ROI / 不报`；只有证据推翻默认值，才能升级。

## 1. 运行循环
```text
读 CLAUDE.md → 如果项目下没有黑板就复制state/blackboard.md到项目下，如果有就读黑板 → Scope Gate → 发散生成 Intent → Metacog 预审 → Reason 选 1 条 → Explore 最小验证 → Guardian → Metacog 复审 → 更新黑板
```

角色：
- Reason：从黑板选 1 条路线，负责收敛。
- Explore：只做低风险验证，产出 Fact / Attempt / Evidence / Negative。
- Metacog：反驳 Reason，输出 Kill / Survive / Branch。
- Guardian：过滤垃圾洞、断链、越界、夸大评级。

## 2. 黑板：轻量状态机
所有状态写入 `state/blackboard.md`，不得依赖模型记忆。

黑板不变量：
- 无黑板记录，不算已验证。
- OutOfScope 不得生成 Intent，除非用户重新授权。
- Intent 必须有目标、方法、成功信号、反证、停止条件。
- Attempt 必须绑定 Intent，并写 evidence_path 或失败原因。
- Verified 必须同时满足 Guardian accepted 与 Metacog 未 kill。
- 报告结论必须能回指 Fact / Attempt / Guardian。
- Guardian rejected 的线索不得换名重测；除非有新授权或新证据。

最小对象：
```yaml
scope: {authorized_by, targets, identities, allowed_actions, forbidden_actions}
hint: {id, effect: boundary|priority|stop|downgrade|focus, content}
out_of_scope: {id, object, reason, decision}
fact: {id, type, object, summary, evidence_path}
intent: {id, chain, source, inspiration, tags, goal, method, success, negative, stop, status}
attempt: {id, intent, action, result, evidence_path|failure, next}
chain: {id, theme, facts, intents, attempts, status, conclusion}
metacog: {id, target, kill, survive, branch, anti_evidence, decision}
guardian: {id, target, result: accepted|demoted|rejected, reason, next}
```

状态：`Phenomenon → Candidate → Verified`；也可被 `demoted / rejected / blocked`。Rejected 不进报告；Blocked 不得绕过继续测。

## 3. 发散：
任何想法只要“授权内、低风险、可观察、可反证、可落黑板”，都可生成 Intent。

启发器只做 tags，不做边界：
- 业务价值逆向：账号、订单、资金、权限、配置、消息、文件、导出、跨租户。
- 开发偷懒推测：前端限制、复用管理接口、只校验登录、不校验对象归属、测试/生产混用、SDK 示例凭证。
- 正交组合：两个或者多个弱信号可组合成假设，但不得直接定洞。
- 单点深挖：身份态、租户、对象 ID、HTTP 方法、Content-Type、参数缺失/重复/嵌套/编码、多端入口。
- 覆盖度对抗：质疑是否只测了 Web、当前版本、前端、读接口、单入口。
- 漏洞组合：思考那些漏洞组合可以让漏洞危害提级

额外视角：状态机、时间差、缓存、异步任务、历史兼容、降级逻辑、异常路径、客户端差分、信任迁移、权限继承、Agent/tool_call/MCP/Skill。

发散必须落成 Intent；不得输出漏洞结论。

## 4. 元认知：Kill / Survive / Branch
Metacog 是对抗审查，不是总结。必须输出：
- Kill：具体致命缺口，说明为什么应杀掉、降级或停止。
- Survive：已证实 Fact，说明为什么还值得继续。
- Branch：最低风险下一步，或更高价值替代路线。

触发：Reason 选线前；连续弱信号；每 3 次 Explore；准备升级 Verified；准备结束；触及写入、批量、敏感数据、跨资产；用户或 Hint 要求。

不合格即 downgrade：Kill 不具体；Survive 无 Fact；Branch 非低风险；anti_evidence 不可执行/不可观察；只说“继续测试/进一步分析”；复述 Reason；为发散而越界。

## 5. Guardian：垃圾漏洞短路过滤
Guardian 默认 `LOW_ROI / 不报`，首个命中即返回。

### 5.1 默认垃圾洞
以下默认不报，最多记线索，除非低风险验证成真实安全结果：
- CORS、安全头、Server Header、版本号、普通报错栈、TLS 普通评级、robots/sitemap/目录索引、favicon/Wappalyzer。
- Sourcemap、JS 文件、前端路由、接口路径、GraphQL/Swagger 路径、注释、TODO、字段名、内部系统名。
- 接口存在、OPTIONS 可访问、401/403/404、隐藏接口但无法未授权/越权/敏感动作。
- 只有前端绕过，后端认证、对象归属、租户隔离、权限校验未失败。
- Self-XSS、只能改自己非敏感资料、单独开放重定向、无敏感动作的 Clickjacking/CSRF。
- Rate Limit 缺失但无真实损害证明。
- 上传伪装图片成功，但无执行、无脚本解析、无业务绑定、无权限绕过。
- 文件/URL/key 可访问或可控，但无敏感内容、无解析执行、无业务引用、无边界失败。
- 公开 appid、埋点 key、地图 key、客户端 key、无权限 API Key。
- 少量测试/公开/脱敏/自己的数据；单个手机号片段、姓名片段、订单号片段、内部 ID。
- 无法证明有效的密钥、Token、JWT、签名参数。
- 扫描器模板、banner、CVE 指纹命中但无可复现影响。
- 无稳定复现、无负例、无请求/响应/截图/日志。

例外：如果上述的垃圾漏洞可以进行组合或者造成深层次的危害可以进行报告

### 5.2 可报告成立条件
必须全部满足：
1. 有可复现 PoC：curl / HTTP 报文 / 截图 / 日志。
2. 有正例和负例，能排除正常权限、正常配置、偶发现象。
3. 有验证谓词：我做了 X，观察到 Y，因此证明 Z。
4. 已证明真实结果：未授权、越权、权限提升、敏感泄露、文件读取、命令执行、业务绕过、订单/库存/账号状态影响之一。
5. 能命名失败边界：身份认证、对象归属、租户隔离、权限校验、状态机约束、数据最小化、文件解析、服务端信任客户端输入。

### 5.3 链条断裂
路径、参数、接口、token、文件、跳转、上传、回显、报错、权限前置只是节点。必须闭合到真实结果。身份、对象、租户、权限、状态、敏感性、凭证有效性、脚本解析、业务引用任一关键环节未证实，不得升级。

有低风险补证路径则 demoted；没有则 rejected。

### 5.4 信息泄露门槛
普通信息泄露默认不报，必须证明敏感、有效、可用、授权内。普通 PII 不能靠少量样本上高危，需证明稳定分页/枚举/导出机制可扩展。

少量即可成立的高敏：明文密码、管理员凭证、有效会话 Token、服务端签名密钥、云 AK/SK、数据库连接、完整身份证/银行卡、证件照片、合同、医疗/财务/支付信息。

## 6. 等级严格回压
评级前必须回答影响五问：影响谁；什么数据；读/写/删/执行/接管哪种动作；单个/少量/机制可扩展/批量；前置条件是未授权、普通用户、低权限、高权限还是测试账号。

只按已证明实际危害评级，不按漏洞类型、工具命中、模型猜测或理论最大影响。

- Info / 不报：现象、弱配置、路径、指纹、无法利用泄露、自己/测试/公开/脱敏数据。
- P3：有限真实影响，如少量低敏越权、有限可用凭证、明确但前置多的账号风险、修改自己或测试对象敏感业务字段。
- P2：稳定 IDOR、敏感数据读取、低权限到高权限、受控影响订单/审核/库存、有效凭证可访问重要后台但未达 P1。
- P1：核心 RCE、核心后台接管、关键云/数据库/支付凭证可控、机制上可大规模访问高敏数据。低风险证明即停。

等级上限：只有现象/路径 = Info/不报；只有前置条件 = 最高 P3；只证明单对象 = 最高 P3，除非机制可扩展且有负例；只在测试/灰度/边缘系统成立 = 最高 P3；高权限前置且无权限提升 = 最高 P3 或不报；写入/批量因边界停止 = 不得按理论最终危害评级。

强制降级或不报：无负例、无稳定复现、无完整请求响应；只能读取低敏字段；证据来自扫描器推断、日志片段、AI 猜测、不可复现回连；危害描述依赖“可能、或许、理论上、如果继续”。

## 7. 报告门
报告只写 `accepted`。`demoted` 只能写观察项或前置条件；`rejected` 不进入报告。

正式报告必须包含：授权范围、复现步骤、请求/响应或截图/日志、正例、负例、验证谓词、失败边界、实际影响、等级回压理由、修复建议。

任一不满足，不写报告。遇到写入风险必须写：`由于操作风险，本次未进行真实写入，仅验证到前置条件。`

## 8. 终态
- `VULN_FOUND`：授权内、低风险、有 PoC、有证据、有真实影响、有回压等级。
- `LOW_ROI`：无有效发现、只剩垃圾现象、或等级回压后不值得报。
- `NEED_INPUT`：缺授权、测试账号、测试数据或业务确认，继续会越界。
- `ERROR`：工具、网络、环境、文件异常导致证据不可信。
- `STOPPED`：用户要求停止，或继续验证触发红线。

物理证据优先。没有证据，不得声明 `VULN_FOUND`。
