# TOOL_AVAILABILITY_CHECK

用途：为所有 skill 提供统一的本机工具可用性检查口径。

强制规则：

1. 任何工具状态必须来自 `_shared/tools/tool_health_check.py` 的运行时探测，或显式标记为 `manual_required`。
2. `tool_health_score.json` 只是最近一次探测快照，不得替代当前运行时探测。
3. 用户确认安装的工具可以记录为 `user_confirmed`，但不能等同于当前机器可执行。
4. 动态验证、AST 解析、浏览器、Burp、MCP 缺失时，只能降级为 `validation_blocked`、`parser_missing` 或 `manual_required`，不得降低漏洞确认门槛。
5. 每次生成 evidence manifest 时必须把工具快照写入 `tool_snapshot` 字段。

推荐命令：

```bash
python3 _shared/tools/tool_health_check.py --write _shared/tools/tool_health_score.json
```

输出字段：`score`、`ready_count`、`total_checks`、`checks[]`、`generated_at`、`verification_mode`。
