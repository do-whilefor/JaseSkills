# Debug / dev mode / internal admin 暴露 报告模板

## 结论状态
candidate / needs_review / blocked / confirmed，仅允许 quality gate 输出 promoted 后写 confirmed。

## 证据链
- Source file:
- Source line:
- Route:
- Handler:
- AuthN/AuthZ:
- Role/Tenant matrix:
- Dynamic evidence:
- Negative control:

## 非破坏性复现
仅记录本机授权测试环境中的安全步骤，不包含破坏性 payload。

## 修复建议
补齐服务端鉴权、租户隔离、对象归属校验、状态机校验、参数白名单与审计日志。
