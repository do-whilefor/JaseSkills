# BLOCKED_AND_HUMAN_REVIEW - post confirmation cleaned

## promoted_by_user_confirmation

- Babel / TypeScript Compiler API / JavaParser / PHP-Parser / Rust syn 等 AST 工具链：用户已确认安装，状态从 `manual_required/tool_missing` 更新为 `ready`。
- Burp / MCP / Playwright / 浏览器：用户已确认本机环境配置，状态从 `manual_required/tool_missing` 更新为 `ready`。
- 10 个原始 `needs_review` skill：用户已确认，状态更新为 `promoted_by_user_confirmation`，允许进入默认映射与回放测试范围。

## still_blocked_until_project_context_exists

- 没有具体本机项目路径、启动方式、测试账号、测试租户和测试数据时，任何候选漏洞仍只能停留在 `validation_blocked` 或 `needs_human_review`，不能进入 `confirmed`。
- 无 evidence manifest 的发现只能进入观察项，不能进入确认漏洞报告。

## unsafe_to_execute

- 删除数据、破坏数据、拒绝服务、大规模压测、访问第三方真实数据、MITM 方向仍禁止执行。

## verification_note

本文件记录的是用户确认后的系统状态，不等同于聊天容器对用户本机的重新探测。实际运行时仍应执行 `_shared/tools/tool_health_check.py` 并把结果写回 manifest 与 dashboard。
