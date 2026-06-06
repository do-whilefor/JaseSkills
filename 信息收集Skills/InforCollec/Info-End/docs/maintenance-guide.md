# 维护者说明

## 修改原则

1. 不得删除原始文档中的边界、流程、质量门槛、输出字段、反思机制。
2. 新增能力必须标记“基于文档延伸”。
3. 修改 Skill 触发条件时，必须同步更新 `CAPABILITY_INDEX.md` 和 `docs/task-router.md`。
4. 修改输出字段时，必须同步更新 `templates/` 和 `docs/fidelity-fingerprint-matrix.md`。
5. 修改脚本行为时，必须保证只读、低频、本机/授权范围、非破坏。
6. 不得让脚本默认访问公网或调用外部真实服务验证密钥。
7. 不能把“覆盖率 100%”写成事实，只能写“映射覆盖”或“当前设计覆盖”。

## 发布前检查清单

- [ ] 文档指纹是否仍全部映射？
- [ ] 触发条件是否误调用/漏调用？
- [ ] 每个 Skill 是否有输入、处理、输出、失败处理？
- [ ] 质量门禁是否仍阻止无证据结论？
- [ ] 敏感信息是否默认脱敏？
- [ ] 脚本是否仍是只读非破坏？
- [ ] 新增内容是否标记延伸？

##

本维护说明用于防止后续修改破坏原始能力。

## 维护要求

- 新增或修改 SKILL.md 后必须运行 `scripts/skill-selftest.py`。
- 修改资产字段时必须同步 `schemas/asset-ledger.schema.json`、`docs/asset-ledger-json-contract.md`、`templates/cross-skill-handoff.md`。
- 修改证据清单字段时必须同步 `schemas/evidence-manifest.schema.json` 和 `scripts/report-to-manifest.py`。
- gRPC/RPC 模板不得默认调用业务方法；Playwright MCP 手册不得要求输出完整敏感值。
