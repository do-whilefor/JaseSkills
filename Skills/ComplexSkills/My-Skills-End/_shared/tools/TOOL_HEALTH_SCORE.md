# TOOL_HEALTH_SCORE - post confirmation cleaned


- generated_at: `2026-06-05T02:23:34.659434+00:00`
- mode: `post_user_confirmation`
- note: 工具安装状态由用户确认；本聊天容器未直接访问用户本机重新检测，因此不伪造本机探测输出。
- score: `96/100`
- ready: `22/23`

| 工具 | 类别 | 状态 | 说明 | 影响范围 | 替代路径 |
|---|---|---|---|---|---|
| Python runtime | language | ready | /opt/pyvenv/bin/python3 | 所有自检、dashboard、manifest 脚本受影响 | 使用系统 python 或手工校验 JSON |
| Node runtime | language | ready | /opt/nvm/versions/node/v22.16.0/bin/node | Babel/TypeScript/JS 解析受影响 | 使用 preserved JS 脚本或 tree-sitter/grep 候选，但不得降证据要求 |
| Java runtime | language | ready | /usr/bin/java | JavaParser/Spring 分析受影响 | 先做文本/配置索引并标记 parser_missing |
| PHP runtime | language | ready | /usr/bin/php | PHP-Parser/Laravel/Symfony 分析受影响 | 先做 composer/router 文本索引并标记 parser_missing |
| Go runtime | language | ready | /usr/local/go/bin/go | Go parser/Gin/Echo/Fiber 分析受影响 | 先做 go.mod 和 route pattern 索引 |
| Rust/Cargo | language | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=missing; actual_local_runtime_not_rechecked_in_chat_container | Rust syn/Axum/Actix/Rocket 分析受影响 | 先做 Cargo.toml 和 macro/route pattern 索引 |
| Playwright Python package | dynamic | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=ready; actual_local_runtime_not_rechecked_in_chat_container | 浏览器动态验证受影响 | 使用 HAR/Burp/手工浏览器导出，不降低动态证据字段 |
| Browser executable | dynamic | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=missing; actual_local_runtime_not_rechecked_in_chat_container | 真实浏览器证据受影响 | 尝试 chromium/msedge/firefox 或标记 environment_missing |
| Burp proxy localhost:8080 | dynamic | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=ready; actual_local_runtime_not_rechecked_in_chat_container | Burp 联动受影响 | 使用 HAR/日志/Playwright 捕获，不降低 request/response 证据 |
| MCP config | dynamic | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=missing; actual_local_runtime_not_rechecked_in_chat_container | MCP 调用不可确认 | 标记 manual_required，使用脚本/文件接口替代 |
| Babel parser | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=manual_required; actual_local_runtime_not_rechecked_in_chat_container | JS AST 精细解析受影响 | Node 可用时安装/调用；否则降为候选生成不确认 |
| TypeScript Compiler API | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=manual_required; actual_local_runtime_not_rechecked_in_chat_container | TS import/export/call graph 精度受影响 | 用 tsconfig/package 映射 + 文本索引 |
| tree-sitter | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=missing; actual_local_runtime_not_rechecked_in_chat_container | 多语言 AST 解析受影响 | 语言专用 parser 或文本候选 |
| Python ast | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=ready; actual_local_runtime_not_rechecked_in_chat_container | Python AST 解析受影响 | 基本不应缺失；缺失则 failed |
| libcst | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; previous_status=missing; actual_local_runtime_not_rechecked_in_chat_container | Python 保真 AST 受影响 | 使用 ast 并标记 degraded |
| dashboard generator writable | output | ready | /mnt/data/local_authorized_security_audit_system_v1/authorized_security_audit_system/_shared | dashboard 不可生成 | 输出 JSON/MD 索引 |
| evidence manifest writable | output | ready | /mnt/data/local_authorized_security_audit_system_v1/authorized_security_audit_system/_shared/evidence | manifest 不可写 | 停止 confirmed，标记 failed |
| regression harness executable | test | missing | /mnt/data/local_authorized_security_audit_system_v1/authorized_security_audit_system/_shared/tests | 回放测试不可执行 | 人工审查测试 JSON expected_status |
| JavaParser | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; JavaParser library / CLI user-confirmed installed | Java AST and Spring route extraction affected | Use Java runtime + text/route extractor as candidate-only fallback; do not confirm without evidence |
| PHP-Parser | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; nikic/PHP-Parser or equivalent user-confirmed installed | PHP/Laravel/Symfony AST extraction affected | Use composer/routes text index as candidate-only fallback |
| Rust syn | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; Rust syn parser user-confirmed installed | Rust macro/route extraction affected | Use Cargo.toml and text patterns as candidate-only fallback |
| TypeScript Compiler API package | ast | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; typescript npm package user-confirmed installed | TS call graph/import/export affected | Use Babel/tree-sitter/text index candidate-only fallback |
| Browser runtime | dynamic | ready | user_confirmed_ready_at_2026-06-05T02:23:34.659434+00:00; browser executable user-confirmed installed | Playwright real-browser evidence affected | Use HAR/Burp/manual export but do not lower evidence standard |
