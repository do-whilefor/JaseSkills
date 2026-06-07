# 原始文档关键规则镜像映射

| 原始关键规则 | 固化位置 | 验收方法 |
|---|---|---|
| 只分析当前本机项目、授权目录、授权服务、授权端口、授权账号 | 00/01/02、tooling-contract | 输入确认中必须有授权范围 |
| 不访问第三方真实业务系统，不调用真实 token 外部 API | 00、anti-hallucination、tooling-contract | QG-01、QG-07 检查 |
| 不输出完整敏感信息，只输出脱敏样本、长度、类型、上下文、位置、hash、影响判断 | 07、redaction-rules、所有脚本 | 报告不得有 raw secret |
| 关键词命中、报错页面、工具告警、状态码变化不能直接当信息暴露 | 00/03/04/07 | 候选状态必须回流动态验证 |
| 开始前读取根目录、运行方式、端口、Base URL、账号角色、禁止范围 | 01 | 审计输入确认表 |
| 同时做静态线、运行线、角色线、反证线 | 00、03、04、05、07 | 报告反思结果和资产表 |
| 阶段 0 建立资产账本 | asset-ledger | 资产表字段完整 |
| 阶段 3 动态验证 10 种方式 | 04、exposure-probe-safe、browser template | 动态验证表体现变体 |
| 阶段 5 偏门方向 | 06、second-pass runbook、package/deployment/protocol templates | 偏门补漏表 |
| 三轮反思 | 06/07/reflection templates | 输出遗漏/误报/剑走偏锋 |
| 每个有效发现 16 个字段 | finding-detail | 高风险详情完整 |
| 最终报告 A-G | final-report | quality-gate-check |
