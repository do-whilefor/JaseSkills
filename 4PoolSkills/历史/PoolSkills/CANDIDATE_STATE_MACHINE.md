# CANDIDATE_STATE_MACHINE

## 状态集合
`discovered`, `mapped`, `triaged`, `validation_planned`, `validation_blocked`, `reproduced`, `negative_control_passed`, `quality_gate_passed`, `confirmed`, `rejected`, `needs_human_review`

## 硬性规则
- 禁止从 `discovered` 直接跳到 `confirmed`。
- 禁止从 `triaged` 直接跳到 `confirmed`。
- 禁止从 `reproduced` 直接跳到 `confirmed`；必须先通过负样本和 quality gate。
- 工具、环境、数据不足时只能进入 `validation_blocked`、`needs_human_review`、`rejected`，不得伪装为 confirmed。

## 合法流转
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
    "reproduced",
    "validation_blocked",
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
    "needs_human_review"
  ],
  "confirmed": [],
  "rejected": [],
  "needs_human_review": [
    "validation_planned",
    "rejected"
  ]
}
```

## 状态字段要求
```json
{
  "discovered": [
    "candidate_id",
    "vulnerability_type",
    "source_file",
    "source_line",
    "static_reason"
  ],
  "mapped": [
    "route",
    "method",
    "parameter",
    "handler",
    "asset",
    "actor"
  ],
  "triaged": [
    "risk_hypothesis",
    "false_positive_notes",
    "non_destructive_boundary"
  ],
  "validation_planned": [
    "validation_plan_id",
    "auth_context",
    "tenant_context",
    "negative_control_plan"
  ],
  "validation_blocked": [
    "blocked_reason",
    "missing_tool_or_context",
    "next_manual_action"
  ],
  "reproduced": [
    "request_summary",
    "response_summary",
    "dynamic_evidence",
    "reproduction_count"
  ],
  "negative_control_passed": [
    "negative_control",
    "negative_control_result"
  ],
  "quality_gate_passed": [
    "quality_gate_score",
    "quality_gate_result"
  ],
  "confirmed": [
    "impact",
    "risk",
    "report_section",
    "fix_guidance"
  ],
  "rejected": [
    "rejection_reason"
  ],
  "needs_human_review": [
    "review_reason",
    "review_owner_hint"
  ]
}
```

## 执行要求
- 每次状态变化必须写入 `outputs/evidence_manifest.json` 的 `state_history`。
- `scripts/state_machine_validate.py` 必须验证状态流转合法性。
- 报告生成器只能读取 `confirmed` 和 `quality_gate_passed` 的候选；其余进入观察项或人工复核。
