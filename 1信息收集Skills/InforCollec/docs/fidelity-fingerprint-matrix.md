# 文档指纹映射矩阵

| 指纹 | 原文能力 | 对应文件 | 对应规则/步骤 | 验收方法 | 缺失时影响 |
|---|---|---|---|---|---|
| FP-BOUNDARY | 本机授权范围；禁止第三方、外部 token 验证、破坏、DoS、MITM、完整敏感信息输出 | 00,01,07,templates/redaction-rules.md | 禁止调用、硬质量门禁、脱敏规则 | 输入确认和报告均列出范围与禁止项 | 可能越界或泄露敏感数据 |
| FP-INPUT | 根目录、运行方式、端口、Base URL、账号角色、禁止范围 | 01 | 审计输入确认表 | 缺字段时不得动态下结论 | 初始范围不稳 |
| FP-FOUR-LINES | 静态线、运行线、角色线、反证线 | 00,03,04,05,07 | 调度链和质量门禁 | 每个发现有四线状态 | 容易静态误报 |
| FP-LEDGER | 资产类型、来源、静态位置、运行态路径、认证、角色、信息类型、状态、证据、风险、不可报告原因 | templates/asset-ledger.md | 资产账本模板 | 字段完整 | 候选无法追踪 |
| FP-RUNTIME | 端口、Docker、代理、前后端、DB 管理面板、文件、metrics/health/debug、队列缓存、文档服务 | 02,scripts/local-runtime-inventory.sh | 入口枚举 | 运行态入口表 | 漏真实入口 |
| FP-ROUTES | 后端路由、Controller、OpenAPI、GraphQL、前端请求、测试集合、docs/examples、代理配置、compose volume | 03,scripts/route-artifact-extract.py | 静态候选 | 候选状态为待验证 | 漏隐藏接口 |
| FP-DYNAMIC | 未认证、低权限、角色、HEAD/GET/OPTIONS、Accept、尾斜杠、浏览器/curl、清 Cookie、2-3 次 | 04,05 | 动态验证和角色差分 | 动态证据编号 EV/RD | 工具命中变误报 |
| FP-TYPES | 凭证、基础设施、业务数据、安全机制、版本指纹 | 04,07,templates/finding-detail.md | 信息类型分类 | 每个发现标类型 | 风险判断不准 |
| FP-EDGE | source map、包产物、缓存、错误面、文档面、业务边角、角色差异、协议差异 | 06 | 深度执行路径 | 文档指纹覆盖表 | 偏门入口遗漏 |
| FP-REFLECTION | 遗漏、误报、剑走偏锋三轮反思 | 06,07,templates/reflection-checklist.md | 反思结果 | 报告 F 部分完整 | 结束过早 |
| FP-EVIDENCE | 标题、类型、影响对象、认证、角色、路径、复现、请求、响应、脱敏、代码、次数、影响、风险、修复、不可报告 | 07,templates/finding-detail.md | 发现详情模板 | 字段完整 | 报告无法交付 |
| FP-FINAL | 总览、资产表、高风险、中低风险、待确认、反思、下一步 | 07,templates/final-report.md | 最终报告模板 | A-G/H 部分完整 | 输出格式不稳定 |

##

“指纹”是新增校验方法，只用于验证保真度，不改变原文档能力。
