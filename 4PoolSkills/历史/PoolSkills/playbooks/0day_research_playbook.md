# 0day Research Playbook（仅本机授权项目）

流程：架构理解 → trust boundary 建模 → source-sink 数据流 → 权限模型 → 多租户模型 → 状态机模型 → parser/deserializer/template/expression engine 审计 → 文件处理链 → webhook/callback/integration → 插件/扩展 → sandbox/policy/rule engine → cache/queue/async job → 版本/补丁/默认配置差分 → 本地非破坏性 fuzz/property/state-machine 测试 → 组合漏洞复核 → 证据链与 responsible disclosure。

确认规则：任何 0day 线索在没有本地动态请求、响应、截图/DOM、negative control、role/tenant 上下文、脱敏 evidence manifest 和 quality gate 通过前，只能是 candidate。

非破坏性 reproduction：不得写入真实业务数据，不得扫描第三方目标，不得使用破坏性 payload；所有 fuzz 输入限制在本地 fixture、解析器函数、临时目录和测试数据库。

Responsible disclosure 模板：标题、影响范围、版本、复现环境、非破坏性步骤、sanitized evidence、negative control、修复建议、时间线、限制说明。
