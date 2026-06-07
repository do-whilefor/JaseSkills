# 10 最终 Web 安全验证报告格式

最终报告必须使用以下结构。

## 1. Executive Summary

- confirmed_high_count
- likely_high_count
- candidate_count
- rejected_count
- max_confirmed_impact
- max_likely_impact
- highest_priority_fix
- strongest_confirmed_impact_path
- biggest_remaining_gap

## 2. Web Surface Exposure Map

表格字段：

- entry_id
- entry_type
- page_url
- frontend_route
- ui_element
- network_request
- auth_boundary
- role_boundary
- tenant_boundary
- object_boundary
- browser_state
- request_params
- response_summary
- evidence_required
- validation_method
- priority

## 3. Confirmed Findings

每项必须包含：

- finding_id
- title
- severity
- affected_pages
- affected_urls
- affected_network_requests
- affected_roles
- affected_tenants
- affected_objects
- root_cause
- security_boundary
- precondition
- browser_action
- modified_input
- request_or_sequence
- expected_result
- actual_result
- evidence
- impact
- fix_recommendation
- regression_test

## 4. Likely Findings

每项包含：

- finding_id
- title
- affected_pages
- affected_urls
- affected_network_requests
- browser_or_network_evidence
- why_likely
- missing_evidence
- next_validation_step

## 5. Candidate Findings

每项包含：

- candidate_id
- risk_area
- page_or_url_or_request
- hypothesis
- validation_plan
- priority

## 6. Rejected Findings

每项包含：

- rejected_id
- hypothesis
- test_performed
- evidence
- rejection_reason

## 7. Impact Paths

每项包含：

- path_id
- starting_page
- starting_actor
- browser_action
- network_request
- steps
- confirmed_steps
- likely_steps
- candidate_steps
- final_impact
- evidence
- classification

## 8. Evidence Manifest

必须包含：

- browser_trace
- screenshot
- console_log
- network_log
- request_log
- response_log
- cookie_snapshot_before
- cookie_snapshot_after
- storage_snapshot_before
- storage_snapshot_after
- service_worker_snapshot
- cache_snapshot
- service_log
- db_snapshot_before
- db_snapshot_after
- file_marker
- callback_log
- mock_service_log
- reproduction_steps

## 9. Fix Plan

- P0：立即修复项
- P1：短期修复项
- P2：中期加固项

## 10. Regression Test Plan

每个 confirmed finding 必须包含：

- test_name
- setup
- actor
- browser_action
- request_input
- expected_secure_behavior
- assertion
- cleanup

报告中禁止出现没有证据的夸张描述。只输出 Web 事实、验证过程、证据、影响、修复和测试。
