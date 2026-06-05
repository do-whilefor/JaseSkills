# 工具能力边界

工具只产生候选、摘要或证据材料；最终结论必须由 07 质量门禁决定。工具缺失时必须写“未覆盖原因”，不得编造结果。

| 脚本 | 允许 | 禁止 | 输出状态 |
|---|---|---|---|
| local-runtime-inventory.sh | 本机端口/进程/容器摘要 | 扫公网、改服务 | 入口候选 |
| route-artifact-extract.py | 只读源码/配置提取 | 把静态命中当结论 | 静态候选 |
| exposure-probe-safe.sh | HEAD/GET/OPTIONS、Accept/尾斜杠差异、1-3 次复现 | 爆破、压测、修改数据、跟随非授权跳转 | 动态证据摘要 |
| browser-storage-collect-playwright.mjs | 授权页面浏览器存储摘要 | 输出完整值、盗用 session、访问非授权域 | 浏览器证据候选 |
| docker-readonly-archaeology.sh | Docker 元数据摘要 | 读 volume 内容、exec 容器、导出镜像层 | 容器候选 |
| deployment-readonly-inventory.sh | 部署文件只读摘要 | 连接外部部署系统、修改配置 | 部署候选 |
| package-artifact-readonly-inventory.py | 包元数据和已存在归档只读解析 | 执行 build/install/pack 脚本 | 包候选 |
| graphql-nondestructive-probe.sh | OPTIONS、__typename、错误响应 | mutation、introspection 默认执行、字段爆破 | GraphQL 候选 |
| shadow-ledger-diff.py | 四表差集 | 把差集当漏洞 | 下一轮验证清单 |
| qg-finding-score.py | 结构化 QG 评分 | 替代人工事实判断 | 交付门槛辅助 |

工具缺失输出：工具、是否存在、未覆盖能力、影响、替代最小验证、是否影响最终交付。

## 工具契约补充

- `grpcurl` 可用于 gRPC reflection list/describe；默认不得调用业务方法。
- `protoc`、`buf` 可用于本地 schema 解析；不得生成并执行会访问真实服务的客户端。
- Playwright MCP 工具名可能因环境不同而变化；只能使用实际可用工具，不能编造 MCP 执行结果。
- `report-to-manifest.py` 只索引本地证据文件，不联网、不验证 secret、不修改证据。
- `skill-selftest.py` 只检查结构完整性，不证明技能质量，也不能替代文档保真度审查。
