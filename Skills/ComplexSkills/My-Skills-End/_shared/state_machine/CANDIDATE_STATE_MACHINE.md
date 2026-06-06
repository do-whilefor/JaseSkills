
# CANDIDATE_STATE_MACHINE

## 状态

`discovered → mapped → triaged → validation_planned → reproduced → negative_control_passed → quality_gate_passed → confirmed` 是唯一完整确认链。

允许阻塞、误报和人工确认分支：`validation_blocked`、`rejected`、`needs_human_review`。

## 禁止规则

- 禁止从 `discovered` 直接跳到 `confirmed`。
- 禁止只有工具告警进入 `reproduced`。
- 禁止没有负样本进入 `quality_gate_passed`。
- 禁止没有 evidence manifest 进入 `confirmed`。
- 禁止没有代码证据、动态证据、影响证据时进入 `confirmed`。

## 合法转移

```json
{
  "discovered": [
    "mapped",
    "rejected",
    "needs_human_review"
  ],
  "mapped": [
    "triaged",
    "rejected",
    "needs_human_review"
  ],
  "triaged": [
    "validation_planned",
    "validation_blocked",
    "rejected",
    "needs_human_review"
  ],
  "validation_planned": [
    "validation_blocked",
    "reproduced",
    "rejected",
    "needs_human_review"
  ],
  "validation_blocked": [
    "validation_planned",
    "needs_human_review",
    "rejected"
  ],
  "reproduced": [
    "negative_control_passed",
    "rejected",
    "needs_human_review"
  ],
  "negative_control_passed": [
    "quality_gate_passed",
    "rejected",
    "needs_human_review"
  ],
  "quality_gate_passed": [
    "confirmed",
    "rejected",
    "needs_human_review"
  ],
  "confirmed": [],
  "rejected": [],
  "needs_human_review": [
    "validation_planned",
    "validation_blocked",
    "rejected"
  ]
}
```

## 状态写入要求

每次状态变化必须追加 `state_history[]`：

- `from_state`
- `to_state`
- `changed_at`
- `reason`
- `evidence_manifest_path`
- `actor_context`
- `blocking_reason`，仅阻塞时必填
