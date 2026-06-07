# 真实动态验证执行器合同

仅用于本机授权目标。默认 `dry_run=true`。默认允许 `localhost`、`127.0.0.1`、`::1`、`file://` 和 `config/authorized_targets.json` 中的目标。禁止第三方非授权目标、破坏性方法、拒绝服务、删除数据和真实第三方数据越权。

新增脚本：`non_destructive_request_guard.py`、`auth_context_manager.py`、`playwright_flow_runner.py`、`burp_repeater_importer.py`、`har_to_evidence_manifest.py`、`tenant_role_matrix_runner.py`。

失败状态：工具缺失、非本机授权、破坏性请求、缺认证上下文、缺租户上下文，必须输出 `validation_blocked`，不能进入 `confirmed`。
