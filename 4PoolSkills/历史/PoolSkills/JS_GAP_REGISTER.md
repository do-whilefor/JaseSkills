# JS_GAP_REGISTER

本文件记录 JS 能力追责结果。没有真实实现、真实样本、真实测试的 JS 能力一律不得 promoted。

| 能力项 | 当前证据路径 | 当前结论 | 缺口 | 状态 |
|---|---|---|---|---|
| HTML script src 收集 | `tools/js_asset_extractor.py`, `outputs/current/selftest_js_assets.json` | 已有候选级实现 | 不证明远程资源可访问性 | promoted_candidate_only |
| 动态加载 chunk 收集 | `tools/js_asset_extractor.py` chunk_lineage | 仅识别 manifest/chunk 线索 | 未执行真实浏览器懒加载、未遍历 dynamic import 图 | needs_review |
| sourcemap 解析还原 | `tools/js_asset_extractor.py`, `scripts/js_sourcemap_resolver.py` | 目前主要证明 sourcemap 引用检测 | 未证明下载、校验、sourceContent 还原、函数级映射 | needs_review |
| minified bundle 还原 | 无稳定测试输出 | 不可 promoted | 缺真实 deobfuscation fixture | blocked |
| wrapper client 解析 | `tools/js_asset_extractor.py` api_wrappers | 只能识别 wrapper 调用信号 | 未用 AST 追踪 axios instance/interceptor/graphql client 参数 | needs_review |
| fetch/axios/graphql/websocket 调用解析 | `outputs/current/selftest_js_assets.json` | 候选级 | headers/body/query/path params 未完整恢复 | needs_review |
| 隐藏参数/废弃参数 | `hidden_parameter_candidates` | 启发式候选 | 未和 backend DTO/model 做强制 diff | needs_review |
| frontend route guard 关联 | `frontend_guards`, `scripts/js_audit_graph_builder.py` | 候选级 | 不能证明后端授权存在或缺失 | needs_review |
| backend handler 推断 | `outputs/current/selftest_js_audit_graph.json` | 只做路径相似相关 | 未做真实 handler dataflow | needs_review |
| service worker 残留接口 | `service_workers` | 信号级 | 未真实 dump cache/runtime | needs_review |
| localStorage/sessionStorage/indexedDB | `storage_uses` | 信号级 | 未动态验证敏感状态泄露/边界 | needs_review |
| postMessage/BroadcastChannel/MessagePort | `post_messages` / `storage_uses` | 信号级 | 缺 origin/source 校验 fixture | needs_review |
| Electron preload / IPC | `platform_bridges` | 信号级 | 缺 Electron fixture 和 IPC runtime 证据 | needs_review |
| extension manifest 权限风险 | `platform_bridges`, manifest 文件识别 | 信号级 | 缺 extension positive/negative fixture | needs_review |
| API 安全图谱 | `scripts/js_audit_graph_builder.py` | 候选图谱 | 不是完整 AST/dataflow/authz graph | promoted_candidate_only |
