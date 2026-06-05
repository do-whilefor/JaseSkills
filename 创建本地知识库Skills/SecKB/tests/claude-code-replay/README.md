# Claude Code 端到端触发回放测试

本目录用于验证 Claude Code 在空任务、模糊任务、负样本、误触发、框架混淆场景下是否稳定触发正确 Skill。

## 测试目标

1. 空任务不得编造任务。
2. 模糊任务必须先进入总控分类。
3. 负样本必须触发边界停止。
4. 误触发任务不得强行调用 SecKB Skills。
5. 框架混淆任务必须进入 RAG 精确过滤，不得套错模板。

## 运行方式

干运行：

```powershell
python .\scripts\claude_code_replay.py .	ests\claude-code-replayeplay-cases.json .eports\claude-code-replay-dryrun.json
```

真实 Claude Code 回放，要求本机已安装 `claude` 命令：

```powershell
python .\scripts\claude_code_replay.py .	ests\claude-code-replayeplay-cases.json .eports\claude-code-replay-live.json --execute
```

真实回放不会尝试利用目标，只验证触发、路由、拒绝、停止、不可报告原因等输出是否出现。
