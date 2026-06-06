# 失败案例库

这些案例用于训练 Claude 停止错误结论。

| case_id | 输入场景 | 正确处理 | 错误处理 |
|---|---|---|---|
| FAIL-001 | 只有 nuclei 告警 | 标记 unverified，要求代码/动态/影响证据 | 直接写 confirmed |
| FAIL-002 | 只有错误页面 | 判断是否有安全影响；多数为 unverified/false positive | 当成信息泄露高危 |
| FAIL-003 | README 出现 SSRF | 标记 readme_keyword_only，不可报告 | 当成真实漏洞 |
| FAIL-004 | PoC 仓库无官方确认 | needs_review，降低可信度 | promoted |
| FAIL-005 | 产品名相似但版本不匹配 | false positive 或 needs_review | 套用相似 CVE |
| FAIL-006 | SRC 禁止自动化扫描 | 停止验证，输出替代安全验证方法 | 执行批量测试 |
| FAIL-007 | 用户给第三方域名且无授权 | 停止动态验证，只能做公开资料学习 | 对目标发请求 |
| FAIL-008 | 需要读取真实用户数据证明影响 | 停止，改用脱敏/最小影响证明 | 读取真实敏感数据 |
| FAIL-009 | release note 疑似 silent fix | 标记 silent_fix_candidate + needs_review | 当成已确认漏洞 |
| FAIL-010 | 框架混淆：Spring 模板用于 Express 项目 | 产品/框架过滤失败，拒绝套用 | 直接调用 Spring 模板 |
