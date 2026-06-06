# 17-js-browser-lazyload-replay

## 定位

本 Skill 专门解决 AI 常见失败点：只打开首页、不点击、不滚动、不登录、不切换角色、不触发懒加载 chunk、不收集按权限/租户加载的 JS。它生成并执行或审查真实浏览器 replay 计划，所有行为必须限定在授权本机项目、授权测试环境或授权域名内。

## 触发条件

- 任务要求真实浏览器、懒加载、点击、滚动、菜单、弹窗、tab、hover、SPA 路由、移动端/桌面端 viewport。
- 任务要求多角色、多租户、多权限矩阵采集 JS、HAR、截图、trace。
- 需要证明隐藏接口、按角色 chunk、按租户 chunk、service worker、缓存资产、GraphQL/WebSocket 是否被触发。

## 禁止条件

- 未确认授权边界时，不得访问公网目标。
- 默认非破坏性：不得删除、支付、审批、批量导出、批量枚举、真实外部回调。
- 登录失败、浏览器缺失、trace/HAR 缺失时必须降级，不得伪装 ready。

## 输入

- seed URL、本机运行地址、登录状态文件、测试账号角色、租户矩阵、允许交互清单。
- 可选：已有 HAR、Playwright trace、CDP performance log、Burp history。

## 输出

- `js_browser_replay_plan.json`：角色、租户、viewport、locale、交互动作、禁止动作、证据产物清单。
- `playwright_safe_replay.spec.ts`：可人工审查后运行的 Playwright 非破坏性 replay 脚本。
- `js_runtime_evidence.json`：若提供 HAR/trace/screenshot，则桥接到 evidence manifest。

## 必须覆盖的交互

首屏加载、全页面滚动、菜单点击、子菜单展开、tab 切换、搜索框输入、表单打开、弹窗打开、hover 菜单、SPA 路由跳转、前进后退、移动端 viewport、桌面端 viewport、locale 切换、普通用户/管理员/只读用户/未登录用户、租户 A/B、文件上传入口、导入导出入口、设置/账单/成员/权限/审计日志页。

## 质量门槛

- 无浏览器 runtime 或等价 HAR/trace：动态 JS 收集最高 45%。
- 无点击/滚动/hover/路由切换记录：懒加载覆盖最高 40%。
- 无角色/租户矩阵：严重权限类漏洞候选不得 promoted。
- 无 screenshot/HAR/trace/request/response：动态验证不得进入最终报告。

## P0 修复后的强制规则：plan-only 不得计为执行证据

`js_browser_lazyload_replay_plan.py` 只能生成安全交互计划和 Playwright spec。它的 `status=plan-only` 永远不能证明真实浏览器交互、懒加载、动态 chunk 或隐藏接口覆盖。

要提升为执行证据，必须运行或导入 `js_playwright_safe_replay_executor.py` 与 `js_runtime_evidence_bridge.py` 产物，并满足：HAR、Playwright trace、截图、请求/响应元数据、role/tenant mapping 同时存在。否则所有动态浏览器能力必须降级为 `未验证 / candidate-only / needs_review`。
