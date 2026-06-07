# 报告模板：任意文件写入（arbitrary_file_write）

## 结论状态
- 允许值：`confirmed` / `needs_human_review` / `needs_review` / `rejected` / `validation_blocked`。
- `confirmed` 仅允许来自 manifest v4 + hard quality gate pass。

## 证据映射
- Manifest candidate id:
- Route / Handler / Middleware:
- AuthN / AuthZ / Tenant boundary:
- Source → Sink:
- JS / sourcemap / frontend route evidence:
- Dynamic evidence id:
- Negative control id:

## 影响证明
- 本机授权范围：
- 非破坏性验证方法：
- 权限/租户/对象边界差异：

## 误报排除
- temp-only fixed path, overwrite denied

## 修复建议
- 在对应 handler、policy、guard、schema validator、sink wrapper 或 dependency/plugin boundary 中修复。
- 修复后必须增加正/负 replay fixture，并重新运行 hard quality gate。

## 禁止内容
- 不包含真实第三方目标攻击步骤。
- 不包含破坏性 payload。
- 不把工具告警或前端猜测直接写成漏洞确认。
