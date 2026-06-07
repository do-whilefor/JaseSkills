# 12 下一轮补充验证

继续下一轮补充验证。

请只针对以下五类内容继续，不要重复已经完成的内容：

1. 已有 confirmed finding 能否组成更高影响路径。
2. likely finding 中最接近 confirmed 的前 10 个。
3. web_exposure_matrix 中 priority 高但尚未验证的前 15 个入口。
4. Web 页面中已发现但证据最薄弱的前 10 个 network 请求。
5. evidence_manifest 中缺少截图、trace、console、network 或服务端反馈的部分。

要求：

- 每个新测试都必须有 test_id。
- 每个测试都必须明确 actor、page、target、input、expected、actual、evidence。
- 没有执行条件的，必须说明 blocking_issue。
- 有条件执行的，不允许只写计划。
- 新增问题必须进入 confirmed / likely / candidate / rejected。
- 已有问题如果证据不足，必须降级。
- 发现重复问题必须合并。
- 最终输出 delta_report，不要重写完整报告。
