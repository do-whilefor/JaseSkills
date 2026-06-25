# Blackboard

> 轻量黑板：只记恢复、调度、证据闭环必需状态。每轮结束更新。

## Invariants
- 无黑板记录，不算已验证。
- OutOfScope 不得生成 Intent，除非用户重新授权。
- Intent 必须有目标、方法、成功信号、反证、停止条件。
- Attempt 必须绑定 Intent，并写 evidence_path 或失败原因。
- Verified 必须绑定 Guardian accepted 与 Metacog 未 kill。

## State
```yaml
scope:
  authorized_by:
  targets: []
  identities: []
  allowed_actions: [静态分析, 只读验证, 本地复现]
  forbidden_actions: [写入, 批量, 真实凭证, 第三方扩展]

hints:
  # - {id: H001, effect: boundary|priority|stop|downgrade|focus, content: ""}

out_of_scope:
  # - {id: O001, object: "", reason: "", decision: do_not_touch|need_input}

facts:
  # - {id: F001, type: endpoint|credential|code|behavior|config|response|negative, object: "", summary: "", evidence_path: "evidence/..."}

intents:
  # - {id: I001, chain: C001, source: F001/H001/M001/user, inspiration: "", tags: [], goal: "", method: "", success: "", negative: "", stop: "", status: open|blocked|done|demoted|rejected}

attempts:
  # - {id: A001, intent: I001, action: "", result: "", evidence_path_or_failure: "", next: continue|switch|stop|downgrade}

chains:
  # - {id: C001, theme: "", facts: [], intents: [], attempts: [], status: exploring|blocked|closed, conclusion: ""}

metacog:
  # - {id: M001, target: I001/C001, kill: "", survive: "", branch: "", anti_evidence: "", decision: continue|switch|downgrade|stop}

guardian:
  # - {id: G001, target: I001/C001, result: accepted|demoted|rejected, reason: "", next: report|candidate|stop|re-verify}

current_round:
  intent:
  scope_gate:
  evidence_path:
  negative:
  metacog:
  guardian:
  next:
```
