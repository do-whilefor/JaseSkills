# 03 Web 暴露面矩阵

请输出 web_exposure_matrix。不要只列 URL，要建立可验证矩阵。

字段必须包含：

- entry_id
- entry_type
- page_url
- frontend_route
- visible_state
- required_auth_state
- required_role
- tenant_boundary
- object_boundary
- ui_element
- form_fields
- network_request
- request_method
- request_params
- response_summary
- browser_storage_used
- cookie_used
- cache_behavior
- sensitive_params
- normal_expected_behavior
- risk_hypothesis
- dynamic_test_method
- evidence_required
- priority
- status

entry_type 至少覆盖：

1. public_page。
2. auth_page。
3. user_page。
4. admin_page。
5. settings_page。
6. profile_page。
7. tenant_page。
8. project_page。
9. workspace_page。
10. list_page。
11. detail_page。
12. search_page。
13. report_page。
14. upload_page。
15. preview_page。
16. download_entry。
17. export_entry。
18. import_entry。
19. invite_page。
20. reset_page。
21. verify_page。
22. callback_page。
23. redirect_flow。
24. GraphQL_request。
25. WebSocket_connect。
26. WebSocket_subscribe。
27. SSE_stream。
28. API_request。
29. static_asset。
30. JS_bundle。
31. sourcemap。
32. service_worker。
33. browser_storage。
34. cookie。
35. error_page。
36. debug_page。
37. health_page。
38. metrics_page。
39. internal_page。
40. legacy_page。
41. example_page。
