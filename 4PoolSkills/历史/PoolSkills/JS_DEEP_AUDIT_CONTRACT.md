# JS 深度审计链路合同

目标：source map 还原、bundle 模块识别、GraphQL/WebSocket/API SDK 提取、feature/debug flag、前端 guard、签名函数候选，并与后端 route graph 对齐。

硬规则：JS 发现的接口、secret、source map、feature flag 只能作为 candidate 或 observation。没有后端证据、动态证据和负样本，禁止 confirmed。
