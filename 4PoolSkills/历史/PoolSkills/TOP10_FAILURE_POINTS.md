# 明日真实授权项目最可能失败的 10 个地方

| 失败点 | 为什么会失败 | 会漏掉什么严重漏洞 | 如何证明当前仍有风险 | 如何修复到生产可信 |
|---|---|---|---|---|
| 真实 AST/source-sink/dataflow 不完整 | 当前依赖桥接和 fallback，工具链缺失会降级 | RCE、注入、任意文件、权限绕过 | `outputs/current/toolchain_availability_ultimate.json` | 强制安装并执行 Babel/TS/libcst/tree-sitter/JavaParser/PHP-Parser/Rust syn，失败即 blocked |
| Playwright 登录态 replay 未证明 | runner 存在但未证明浏览器、storageState、HAR、截图 | IDOR、多租户绕过、状态机绕过 | `scripts/playwright_flow_runner.py`, toolchain 输出 | 新增真实登录矩阵 fixture 与 HAR/screenshot 断言 |
| 多角色/多租户矩阵缺真实账号 | 计划存在，真实 credential_ref 与响应 diff 不存在 | BOLA、组织切换、管理员权限提升 | `outputs/current/selftest_replay_plan.json` | 添加 role_tenant_matrix schema、seed users、diff report |
| detector 仍以 regex/static pattern 为主 | pattern 命中不能证明可达链 | 业务逻辑、二阶注入、复杂权限链 | `scripts/detectors/detector_runner.py` | 每类漏洞独立 source-sink-auth/tenant-aware detector |
| JS wrapper/header/body 参数解析不足 | wrapper 只做信号识别 | hidden params、mass assignment、debug/dryRun | `tools/js_asset_extractor.py` | Babel/TS AST resolver + wrapper fixture |
| sourcemap 仅检测引用 | 不证明源码还原 | 老接口、隐藏管理接口 | `outputs/current/selftest_js_assets.json` | sourcemap resolver 输出 sourceContent/function mapping |
| 信息收集未全部进入 detector/replay | 部分资产停留在线索 | debug/internal/admin、secret 供应链 | orchestrator 输出与知识库规则对比 | normalized asset schema + detector adapter |
| dashboard 不是生产运行态审计台 | 读取 JSON 不证明 JSON 来源真实 | fixture 被误读成真实证据 | `tools/dashboard_builder.py` | 显示 run_id、manifest hash、命令输出、toolchain status |
| 报告复现性依赖证据质量 | confirmed 模板必须靠动态证据 | 严重级别误报、影响范围夸大 | `tools/quality_gate.py` | confirmed 模板强制 request/response、role diff、tenant diff |
| 真实 OSS replay 不存在 | benchmarks 不等于 30+ 真实可运行项目 | 框架特有鉴权/ORM/构建边界 | `benchmarks/` 目录 | 新增 docker compose、seed、HAR baseline、expected findings |
