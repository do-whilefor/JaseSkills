# Import Real OSS Project Contract

本环境不能联网下载真实 OSS 仓库，因此包内提供的是离线最小 fixture 和绑定合同。要把它升级为真实 OSS 回放，必须在本机授权目录放入真实开源项目 clone，并记录：

1. repository URL 或本地来源说明。
2. commit hash。
3. license。
4. 本机运行命令。
5. 测试账号/角色/租户。
6. semantic_graph 输出。
7. 浏览器/HAR/trace/storageState 输出。
8. positive / negative / blocked / needs_review 结果。
9. final_claim_guard 输出。

没有这些字段时，dashboard 必须显示 real_oss_bound=false，禁止声称“真实 OSS 已回放完成”。
