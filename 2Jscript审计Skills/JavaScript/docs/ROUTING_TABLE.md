# 触发路由表

| Skill | 高置信触发词 | 低置信触发词 | 禁止触发 | 误触发样例 | 漏触发样例 |
|---|---|---|---|---|---|
| 00 | JS 审计、复现、反思、证据、报告 | 整理、看一下、继续 | 普通开发问题 | 写 React 组件 | 上传 JS 源码但只说“看看” |
| 01 | 授权、边界、质量门槛 | 开始、先做 | 普通问答 | 解释 cookie | 直接要求挖漏洞未提授权 |
| 02 | 目录、架构、语言识别、入口 | 分析项目 | 已有完整候选只复现 | 介绍 Express | 只传源码压缩包 |
| 03 | 参数、source-to-sink、调用链、权限矩阵 | 查接口 | 无源码 | 画概念图 | 用户说“检查参数流” |
| 04 | 配置、依赖、CVE、供应链、框架 | package | 未给版本却要最新 CVE | 问 npm install | 只传 package.json |
| 05 | 前端、source map、storage、签名、DOM XSS | dist、build | 无前端资产 | 写页面 | 只传 sourcemap |
| 06 | 高危、0day、业务漏洞、链式漏洞 | 深挖 | 只复现已有候选 | 泛泛安全建议 | 用户说“找严重问题” |
| 07 | 复现、动态验证、三次复现、反证 | 跑一下 | 破坏性操作 | 压测接口 | 用户说“确认真假” |
| 08 | manifest、证据、质量门禁、不可报告 | 整理证据 | 伪造路径 | 写漂亮报告 | 用户给 evidence 目录 |
| 09 | 反思、误报、漏报、0day 链 | 复盘 | 堆数量 | 继续扫描 | 用户说“别默认正确” |
| 10 | 最终报告、修复建议 | 汇总 | 未过 08 | 写营销文案 | 用户说“给最终版” |
| 11 | 小程序、Electron、Extension | manifest | 普通 Web | 写 Chrome 插件 | 项目含 manifest.json |
| 12 | skills 评审、JS 收集评审、JS 审计评审、严重 JS 漏洞发现、fake-ready、doc-only、parser backend、Playwright/Burp/HAR、多角色/多租户 | 打分、清理、修复压缩包 | 普通业务项目漏洞挖掘、未授权测试 | 直接攻击公网目标 | 用户上传 skills 包并说“评审是否顶级” |

| 13 | 二次审查、逐条反查、评分虚高、JS 审计保真度、candidate-only、未动态验证、缺少 role/tenant replay、偏门审计点 | 再审一遍、纠错 | 普通漏洞挖掘、未授权目标 | 继续美化上一轮结论 | 用户说“不要默认你的评估正确，输出新压缩包” |


| 终极反向审判 / 证据法庭 / 失职追责 / 伪 ready 追责 / 高危漏报清算 | 00 → 01 → 14 → 13 → 12 → 08 → 10 | 禁止维护原结论；无证据必须降级；禁止把模板/fixture/README 当实现 |


| 顶级 JS 收集/分析/审计、chunk/source map/runtime/HAR/role tenant diff | `15-js-top-tier-collection-analysis-audit` | `00 -> 01 -> 15 -> 08 -> 10 -> 14` | 未提供 parser/runtime/role-tenant 证据时必须降级 |


| 触发意图 | 必须链路 | 禁止事项 |
| --- | --- | --- |
| 隐藏接口、隐藏参数、前端不传但后端可能接受 | 00 → 01 → 15 → 16 → 18 → 19 → 08 → 20 | 不得把 JS 字符串候选写成后端已接受 |
| 懒加载、真实浏览器、点击/滚动/hover/SPA、多角色/多租户 | 00 → 01 → 17 → 07 → 08 → 20 | 未运行或未提供 HAR/trace 时不得 verified |
| Mass Assignment、Over-posting、role/isAdmin/tenantId/status/price/quota 等字段 | 00 → 01 → 16 → 18 → 19 → 07 → 08 | 无请求响应差异不得声称漏洞成立 |
