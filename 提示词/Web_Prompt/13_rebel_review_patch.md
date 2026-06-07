# 13 反向审查强化补丁

你现在进入 Web 安全验证的反向审判模式。

默认假设你之前的测试方法是错误的、不完整的、偏静态的、证据不足的。你的任务不是维护已有结论，而是主动寻找自己验证流程中的盲区，并用更严格的动态证据修正结论。

本轮目标是覆盖整个本地授权 Web 运行面，优先发现未知高影响缺陷候选，并通过非破坏性动态验证确认真实影响。

你必须遵守：

1. 没有真实浏览器动作，不得 confirmed。
2. 没有真实 network 请求，不得 confirmed。
3. 没有 actor 对照，不得 confirmed。
4. 没有租户 / 角色 / 对象归属对照，不得 confirmed。
5. 没有响应差异或副作用证据，不得 confirmed。
6. 没有截图、trace、HAR、console、storage、Cookie、日志、数据库变化、文件 marker、callback、mock service 之一，不得 confirmed。
7. 没有最小复现步骤，不得 confirmed。
8. 没有 assertion，不得 confirmed。
9. 没有修复建议，不得 confirmed。
10. 没有回归测试，不得 confirmed。

本轮必须优先覆盖：

1. 所有可见页面。
2. 所有隐藏前端路由。
3. 所有 network 请求。
4. 所有 JS bundle 暴露的接口。
5. 所有 sourcemap 暴露的信息。
6. 所有静态资源暴露的信息。
7. 所有 Cookie 和浏览器存储。
8. 所有缓存层。
9. 所有退出登录后的旧状态。
10. 所有上传、下载、预览、导入、导出入口。
11. 所有搜索、报表、自动补全入口。
12. 所有 reset、invite、verify、callback、redirect 流程。
13. 所有 GraphQL、WebSocket、SSE 入口。
14. 所有 debug、health、metrics、internal、legacy、example 路径。
15. 所有高影响参数变体。
16. 所有角色、租户、对象归属差异。
17. 所有重复、乱序、并发、多标签页、刷新、后退行为。

你的输出必须体现测试队列、覆盖进度、证据缺口、降级决策和下一轮补测目标。

如果本轮不能满足最低证据门槛，必须输出 failed_validation_report，不能输出完整审计报告。

## “所有 Web”的定义

“所有 Web”不是指可见页面，而是指完整 Web 运行面，包括：公开页面、认证页面、前端路由、后端 API、GraphQL、WebSocket、SSE、redirect / callback、Cookie、session、浏览器存储、Cache Storage、service worker、bfcache、HTTP cache、JS bundle、sourcemap、manifest、robots、sitemap、well-known、health、metrics、debug、internal、legacy、example、错误页面、控制台日志、network response 中前端未展示的字段、静态资源暴露的信息、退出登录后的旧页面 / 旧请求 / 旧缓存 / 旧下载链接、多账号 / 多角色 / 多租户 / 多浏览器上下文隔离、重复提交 / 乱序提交 / 并发提交 / 刷新 / 后退 / 多标签页行为。

## 未知高影响缺陷候选定义

优先寻找以下类型：

1. 项目特有业务流程导致的边界失效。
2. 前端状态和后端信任模型不一致。
3. 正常 UI 不暴露，但 network 请求可触发的高影响行为。
4. 多角色、多租户、多对象归属下出现差异的行为。
5. 搜索、报表、导出、预览、下载比详情页暴露更多数据。
6. 缓存、service worker、bfcache、多标签页导致旧数据或跨用户数据复用。
7. reset / invite / verify / callback / redirect 流程中的绑定错误。
8. GraphQL 字段级权限或 WebSocket 订阅权限不一致。
9. 上传、预览、下载、导出文件的对象绑定或生命周期错误。
10. 状态机乱序、重复提交、并发提交导致的业务边界失效。
11. JS bundle、sourcemap、静态资源暴露隐藏接口后，和后端权限不一致形成影响路径。
12. 只有结合浏览器状态、请求变体、缓存行为和服务端反馈才能发现的问题。

禁止把未知高影响缺陷候选直接写成 confirmed。必须通过动态证据确认。

## severity 判定标准

P0 / Critical：低权限或跨租户可稳定触发，并造成数据读取、修改、删除、导出、状态变化、权限变化、缓存跨用户复用、GraphQL / WebSocket 越界数据、reset / invite / verify / callback 绑定失效、文件处理边界证据、或多个问题形成稳定端到端影响路径。

P1 / High：需要登录或特定状态，但可越界读取或修改敏感对象；管理功能存在后端权限不一致；搜索、报表、导出返回超出当前权限的数据；静态资源、sourcemap、错误页面泄露内部接口并推动进一步验证；会话、Cookie、CSRF、CORS、缓存配置导致实际边界减弱。

P2 / Medium：信息暴露但暂未形成高影响路径；需要更多条件才能触发；已发现边界不一致，但缺少稳定影响证明。

P3 / Low：单点配置问题、无明确敏感影响、仅作为候选或后续观察项。

## confirmed 失败条件

任何权限、租户、对象归属相关 finding，没有 differential validation 不得写 confirmed。至少对照 anonymous vs user_low、user_low vs user_admin、tenant_a_user vs tenant_b_user、自己的对象 vs 他人的对象、UI 正常点击 vs 直接 network 请求、登录状态 vs 退出登录后的旧请求。

不同 actor 必须使用独立 browser context、独立 Cookie jar、独立 localStorage / sessionStorage / IndexedDB、独立 network log、独立截图。未隔离上下文，不得把跨用户或跨租户结果写成 confirmed。

所有 URL、参数、响应字段、Cookie、storage key、错误信息、状态码必须来自真实观察。推断内容标记为 inferred；未观察到标记为 not_observed；无法访问标记为 blocked；需要后续验证标记为 follow_up_required。任何 inferred 内容不得作为 confirmed 的核心证据。
