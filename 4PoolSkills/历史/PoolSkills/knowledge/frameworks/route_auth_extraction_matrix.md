# Framework Route/Auth Extraction Matrix

覆盖 Express/Next/Nest/FastAPI/Django/Spring/Laravel/Rails/Go Gin/Fiber/Chi/Rust Axum/Actix。

每条路由必须尽力抽取：method、path、file、line、handler、middleware、authn hint、authz hint、parameters。正则提取标记为 candidate，AST bridge 成功时才可作为语义图谱证据；即使 AST ready，也不能替代动态验证。
