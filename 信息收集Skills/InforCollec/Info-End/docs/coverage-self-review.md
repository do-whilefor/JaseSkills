# 覆盖率自评

当前是“设计映射覆盖”，不是对任何真实项目的实际覆盖承诺。真实项目覆盖率取决于服务是否运行、账号是否可用、工具是否存在、授权范围是否明确。

| 原文能力 | 设计覆盖 | 主要位置 |
|---|---|---|
| 授权边界 | 已覆盖 | 00/01/07/tooling-contract |
| 输入确认 | 已覆盖 | 01 |
| 四线交叉 | 已覆盖 | 00/03/04/05/07 |
| 资产账本 | 已覆盖 | templates/asset-ledger.md |
| 运行态入口 | 已覆盖 | 02 |
| 代码驱动路由 | 已覆盖 | 03/route-artifact-extract.py |
| 动态验证 | 已覆盖 | 04/exposure-probe-safe.sh |
| 信息类型分类 | 已覆盖 | info-type-reverse-checklist.md |
| 小众偏门信息面 | 已覆盖 | 06/second-pass-reflection-runbook.md |
| 部署信息 | 修复后覆盖 | deployment-surface-checklist.md/deployment-readonly-inventory.sh |
| 包产物 | 修复后覆盖 | package-artifact-readonly-inventory.py |
| 协议差异 | 修复后覆盖 | protocol-surface-validation.md |
| 三轮反思 | 已覆盖 | 06/07/reflection-checklist.md |
| 证据标准 | 已覆盖 | finding-detail.md |
| 最终报告 | 已覆盖 | final-report.md |
| 质量门槛 | 已覆盖 | 07/qg-finding-score.py |

剩余非满分原因：真实浏览器 MCP 依赖用户环境；Docker/Kubernetes/CI/CD 运行态权限不一定存在；gRPC/RPC 深度验证需要具体客户端或 schema；QG 脚本只能做结构化评分，不能替代人工事实判断。
