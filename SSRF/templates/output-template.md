# SSRF 动态验证报告模板

> 所有动态验证只允许指向本地 canary、测试容器网络或测试目录 marker 服务。没有 canary 回连不得 confirmed。没有复现步骤不得输出漏洞结论。

## 报告元信息

| 字段 | 内容 |
|---|---|
| 项目名称 |  |
| project_root |  |
| app_start_command |  |
| app_base_url |  |
| canary_base_url |  |
| evidence_dir | evidence/ssrf/ |
| authorization_scope |  |
| prohibited_targets | 真实公网敏感地址、云 metadata、真实内网资产、公司内网、第三方服务、生产服务 |
| 测试时间 |  |
| 测试人员/执行者 |  |
| 报告状态 | draft / reviewed / final |

## 一、项目 SSRF 暴露面总览

| 类别 | 已检查数量 | candidate | confirmed | blocked | needs_review | 证据路径 |
|---|---:|---:|---:|---:|---:|---|
| 用户可控 URL 参数 |  |  |  |  |  |  |
| 隐藏入口 |  |  |  |  |  |  |
| 依赖层暴露面 |  |  |  |  |  |  |
| 服务端请求 sink |  |  |  |  |  |  |
| 异步/worker/定时任务 |  |  |  |  |  |  |
| 渲染/导入/预览链路 |  |  |  |  |  |  |
| 跨角色/跨租户链路 |  |  |  |  |  |  |

## 二、SSRF source → sink 数据流图

```text
[source: 用户输入/导入文件/后台配置/异步任务]
  -> [入口路由/任务入口]
  -> [参数解析/DTO/model/文件解析]
  -> [校验逻辑]
  -> [redirect/DNS/IP/协议处理]
  -> [sink: HTTP client/render/webhook/worker]
  -> [本地 canary marker]
```

| 编号 | source | 入口 | 中间处理 | sink | 最终地址校验 | 证据路径 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

## 三、动态验证环境说明

| 项 | 内容 | 证据路径 | 通过/失败 |
|---|---|---|---|
| 授权边界 |  |  |  |
| 本地应用启动 |  |  |  |
| 应用日志采集 |  |  |  |
| worker 日志采集 |  |  |  |
| canary 服务 |  |  |  |
| baseline 反例 | 浏览器/curl 直连 canary，不计为 SSRF |  |  |
| 禁止目标检查 | 未访问真实公网敏感地址、云 metadata、真实内网、公司内网、第三方服务、生产服务 |  |  |

## 四、canary 服务说明

| 字段 | 记录值/说明 |
|---|---|
| request_time |  |
| path |  |
| method |  |
| headers |  |
| body_digest |  |
| source_ip |  |
| User-Agent |  |
| from_target_server | yes / no / unknown |
| marker_id | `/ssrf-marker/<route>/<param>/<case-id>` |
| 日志文件 |  |

## 五、候选点矩阵

| 编号 | 路由/入口/功能 | 用户可控参数 | 参数来源 | 代码文件 | 调用链 | sink | 是否服务端请求 | 是否跟随跳转 | 是否有协议限制 | 是否有 host/IP 限制 | 是否有 DNS 解析校验 | 是否存在解析差异风险 | 是否异步触发 | 是否需要登录 | 需要的角色 | 初始风险等级 | 动态验证计划 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  | query/body/header/file/import/worker |  |  |  | yes/no/unknown | yes/no/unknown | yes/no/unknown | yes/no/unknown | yes/no/unknown | yes/no/unknown | yes/no | yes/no |  |  |  | candidate/confirmed/blocked/needs_review |

## 六、已确认漏洞列表

> 任一强制字段缺失时，不得写入本节，必须降级到 candidate 或 needs_review。

### CONFIRMED-<case-id>：<漏洞标题>

| 字段 | 内容 |
|---|---|
| 漏洞标题 |  |
| 影响功能 |  |
| 入口路由 |  |
| 需要权限 |  |
| 触发参数 |  |
| 完整请求样本 | `evidence/ssrf/<case-id>/request.http` |
| canary marker 日志 | `evidence/ssrf/<case-id>/canary.log` |
| 应用服务端日志 | `evidence/ssrf/<case-id>/app.log` |
| 调用链代码位置 | `evidence/ssrf/<case-id>/code-chain.md` |
| 为什么证明是服务端请求 |  |
| 正例 | `evidence/ssrf/<case-id>/positive.md` |
| 反例 | `evidence/ssrf/<case-id>/negative.md` |
| blocked case | `evidence/ssrf/<case-id>/blocked.md` |
| 是否可跨角色/跨租户 |  |
| 风险等级 | critical/high/medium/low/informational |
| 修复建议 |  |
| 最小补丁方向 |  |
| 回归测试用例 | `evidence/ssrf/<case-id>/regression.md` |
| 复现命令 |  |
| 证据文件路径 | `evidence/ssrf/<case-id>/` |

## 七、被阻断的安全用例

| case-id | 入口 | 阻断目标类型 | 请求样本 | 应用响应 | canary 行为 | blocked 证据 | 结论 |
|---|---|---|---|---|---|---|---|
|  |  | 本地受控非法 scheme / 本地受控阻断目标 / redirect 后阻断 |  |  | 未收到/收到但被拒绝 |  | blocked |

## 八、误报排除列表

| case-id | 误报类型 | 触发来源 | 排除证据 | 降级后状态 |
|---|---|---|---|---|
|  | 浏览器直连 canary / 测试工具请求 / redirector 自身请求 / 前端请求 / 只保存未触发 / 只有错误提示 |  |  | candidate/needs_review/blocked |

## 九、高危链路深挖结果

| case-id | 高危条件 | 动态证据 | 是否满足高危/严重 | 降级原因 |
|---|---|---|---|---|
|  | 低权限触发 / 绕过限制 / 跳转链 / worker / 管理员预览 / 跨租户 / 测试 marker 服务 / 业务状态影响 |  | yes/no |  |

## 十、跨角色 / 跨租户 SSRF 组合风险

| case-id | 触发者角色 | 执行者角色 | 租户 | 是否可跨角色 | 是否可跨租户 | 证据路径 | 结论 |
|---|---|---|---|---|---|---|---|
|  |  |  | A/B/不适用 | yes/no/unknown | yes/no/unknown |  |  |

## 十一、修复优先级

| 优先级 | case-id/问题 | 具体修复措施 | 最小补丁方向 | 回归测试 | 状态 |
|---|---|---|---|---|---|
| P0 |  | 协议白名单、危险 scheme 禁止、解析后校验、跳转后最终地址校验、DNS/IP 校验、tenant 绑定 |  |  | open |
| P1 |  | webhook 白名单/签名/限速/审计，远程资源禁用或隔离代理，异步任务审计 |  |  | open |
| P2 |  | 日志、限速、可观测性、单元/集成/动态回归测试 |  |  | open |

## 十二、可直接执行的回归测试计划

| case-id | 入口 | 角色 | 租户 | 参数 | canary marker | 触发步骤 | 预期 canary 行为 | 预期应用行为 | 反例 | blocked case | 成功判定标准 | 失败判定标准 | 证据路径 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  | 收到/不收到 marker |  |  |  |  |  |  |

## 十三、证据文件索引

| case-id | request.http | response.txt | canary.log | app.log | code-chain.md | positive.md | negative.md | blocked.md | repro.md | regression.md | verdict.md |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no |

## 十四、仍未覆盖的盲区

| 盲区 | 原因 | 风险 | 下一步 | 是否影响结论 |
|---|---|---|---|---|
|  | 缺账号/缺 worker/缺日志/项目不支持/未启动/未覆盖变体 |  |  | yes/no |

## 十五、下一轮深挖路线

| 优先级 | 入口/链路 | 补测原因 | 需要资源 | 预期证据 |
|---|---|---|---|---|
| P0 | 低权限、worker、管理员预览、webhook、PDF/HTML/图片渲染、redirect、多租户 |  |  | canary + app log + request + code-chain |
| P1 | 导入文件、RSS/OG、GraphQL/WebSocket/multipart、OAuth/OIDC/SAML、对象存储 endpoint、旧版/隐藏 API |  |  |  |
| P2 | 缓存、重试、错误处理、日志泄露、限速、可观测性、回归测试 |  |  |  |

## 附录：原文复刻 / 工程化补强声明

| 内容 | 类型 | 说明 |
|---|---|---|
| 硬边界、canary、marker、candidate/confirmed/blocked/needs_review、十五节报告、证据链、反向审判、最终追责 | 原文复刻 | 来自 TXT |
| case-id 格式、证据文件名、严重性枚举、门禁执行顺序 | 工程化补强 | 为可执行和可验收新增 |
