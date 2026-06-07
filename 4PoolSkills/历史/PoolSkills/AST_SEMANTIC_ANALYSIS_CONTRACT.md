# AST 级安全语义分析执行合同

目标：把原有 route / JS / knowledge graph 的文本候选提取升级为真实解析器优先的语义分析链路。任何插件缺失时必须标记为 `degraded`、`missing` 或 `manual_required`，禁止把 regex fallback 伪装成 AST ready。

必须输出链路：`Route → Handler → Middleware → AuthN → AuthZ → Parameter → Model → Sink → Evidence`

落点：`config/semantic_ast_plugins.json`、`ast_plugins/`、`scripts/semantic_ast_analyzer.py`、`scripts/semantic_route_extractor.py`、`scripts/security_graph_validator.py`、`outputs/security_graph.json`。

触发：源码审计、路由提取、权限边界、数据流、危险函数、source/sink、框架审计、严重漏洞候选生成。

禁止：未给本机授权项目路径、路径不存在、非本机文件系统、第三方非授权目标。

失败处理：插件缺失不降权为“完成”，只能输出 `validation_blocked` 或 `degraded`，并写明影响范围和替代路径。
