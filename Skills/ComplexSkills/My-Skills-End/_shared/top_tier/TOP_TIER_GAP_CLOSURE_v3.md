# Top-tier Gap Closure v3

本版本新增：

- semantic_graph_builder：提取 Express / Next.js / Django / FastAPI / Spring / Laravel 路由、source、sink、guard。
- framework extractor wrappers：每个框架可单独运行。
- candidate_to_replay_plan：把候选漏洞转成非破坏性正负测试计划。
- evidence_artifact_importer：导入 Burp/HAR、Playwright trace、storageState 到 evidence manifest overlay。
- top_tier_adversarial_harness：诱导伪动态验证和伪 confirmed 时必须失败。
- full_chain_drilldown_generator：输出 Route → Candidate → Evidence → Quality Gate → Report 链路 dashboard。
- executable template overlays：对已有模板生成机器可执行字段，不改原始模板。
- severe_23_execution_samples：每类严重漏洞补 positive / negative / blocked / needs_review 合同样本。

仍然不能伪装完成的事项：

- 未提供真实本机授权项目、账号、租户、启动方式时，不能实际跑完整一轮。
- 离线 OSS fixture 不是完整真实 OSS 仓库；必须绑定本机真实 clone 和 commit 后才能声称真实 OSS 回放。
- semantic graph 是静态证据，不是漏洞 confirmed 证据。
