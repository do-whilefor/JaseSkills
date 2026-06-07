# full-example

本示例展示反查后的最终版结构。示例项目为虚构本地项目，所有样本均为无害 marker。

## 1. 执行摘要示例

- 项目语言：Node.js
- 框架：Express + Bull worker
- 运行方式：`npm test`、`npm run dev`、`npm run worker:test`
- 反序列化相关依赖：js-yaml、cookie-session、node-serialize
- 高风险入口数量：2
- confirmed 数量：0
- candidate 数量：2
- blocked 数量：1
- not reachable 数量：0
- dependency-only 数量：1
- false positive 数量：0
- 最高风险点：DS-001 admin import YAML 解析候选路径
- 尚未覆盖原因：未提供真实本地 admin token；worker 队列测试权限未确认

## 2. 依赖与框架风险映射示例

| 编号 | 依赖/模块 | 版本 | 相关反序列化能力 | 是否被项目调用 | 调用路径 | 输入来源 | 是否可动态验证 | 风险等级 | 证据 |
|---|---|---|---|---|---|---|---|---|---|
| DEP-001 | js-yaml | 4.x | YAML load / tag parsing | 是 | `services/ruleImport.js` | admin import file | 是 | 中 | SNK-001、SRC-010 |
| DEP-002 | cookie-session | 2.x | session deserialize wrapper | 是 | `middleware/session.js` | cookie | 是 | 低 | 本地签名阻断 |
| DEP-003 | node-serialize | 0.x | object deserialize | 否 | 无 | 无 | 否 | 无 | 仅 lockfile 存在 |

## 3. 暴露面总表示例

| ID | 入口 | 数据来源 | 格式 | sink | 依赖/函数 | 权限要求 | 动态验证状态 | 结论 |
|---|---|---|---|---|---|---|---|---|
| DS-001 | `/admin/import-rules` | multipart file | YAML | `yaml.load` | js-yaml | admin | 未执行 | candidate |
| DS-002 | Bull retry worker | Redis queue | JSON blob | custom hydrate | app worker | worker | 未执行 | candidate |
| DS-003 | remember-me cookie | cookie | signed token | session wrapper | cookie-session | user | 已阻断 | blocked |
| DS-004 | lockfile dependency | 无 | 无 | node-serialize | node-serialize | 无 | 未调用 | dependency-only |

## 4. 动态验证执行记录示例

| 命令 ID | 工作目录 | 命令 | 输入样本 | 输出/日志 | 退出码 | 结论影响 |
|---|---|---|---|---|---:|---|
| CMD-001 | `C:\lab\demo-app` | `npm test -- tests/session-signature.spec.js` | `fixtures/local-lab/tampered-cookie.txt` | `test-output/logs/session-test.log` | 0 | DS-003 blocked |

| 请求 ID | 类型 | 目标 | 方法/协议 | 样本文件 | 响应证据 | 结论影响 |
|---|---|---|---|---|---|---|
| REQ-001 | HTTP | `http://127.0.0.1:3000/api/session/remember` | GET | `fixtures/local-lab/tampered-cookie.txt` | 401 + `invalid signature` | DS-003 blocked |

| Marker ID | 路径/位置 | 触发方式 | 内容摘要 | 清理命令 | 清理结果 |
|---|---|---|---|---|---|
| MARKER-001 | `test-output/deserialization-markers/session.txt` | 签名前置测试 | 未生成 marker，说明解析前阻断 | `Remove-Item -Force test-output/deserialization-markers/session.txt -ErrorAction SilentlyContinue` | 不存在 |

## 5. 降级清单示例

| 原结论 | 降级后结论 | Finding ID | 降级原因 | 缺少证据 | 后续补测 |
|---|---|---|---|---|---|
| confirmed | candidate | DS-001 | 只有 source/sink/调用链，无本地 marker | 本地请求、marker、日志、清理记录 | 执行 admin import 无害样本 |
| confirmed | candidate | DS-002 | worker 未启动，queue payload 未消费 | worker 日志、queue 消费断言、marker | 启动本地 worker 后投递测试消息 |

## 6. 补测清单示例

| Candidate ID | 测试入口 | 测试账号/权限 | 输入样本 | marker 设计 | 正向样本 | 负向样本 | 阻断样本 | 运行命令 | 观测位置 | 清理命令 | 预期结果 | 当前缺口 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DS-001 | admin import | admin_a | `fixtures/local-lab/rule-marker.yml` | 写入 `test-output/deserialization-markers/DS-001.txt` 或日志 marker | 合法 rule YAML | 低权限、错误类型、未知字段、非预期 content-type | 未知 tag 被拒绝 | `npm test -- tests/admin-rules-import.spec.js` | test-output、应用日志 | `Remove-Item -Recurse test-output/deserialization-markers` | marker 只在合法样本出现，未知 tag 被拒绝 | 未执行 |
| DS-002 | Bull retry worker | worker | `fixtures/local-lab/job-marker.json` | worker 日志 marker | 合法 job payload | 跨租户、过期签名、错误版本 | 签名不匹配被拒绝 | `npm run worker:test` | worker test log | 清空 Redis test DB 15 | worker 只处理已签名 schema payload | 缺 Redis 测试权限 |

## 7. 漏报追查清单示例

| 隐藏面 | 是否检查 | 证据 | 发现 | 未覆盖原因 |
|---|---:|---|---|---|
| session | 是 | `middleware/session.js` | 签名前置阻断 | 无 |
| remember-me | 是 | `auth/remember.js` | 使用签名 token，未见对象解析 | 需验证签名前后顺序 |
| dead-letter | 否 | 无 | 未覆盖 | 未提供测试队列权限 |
| database serialized column | 是 | migration 搜索 | `job_payload` JSON blob 二次解析候选 | 进入 DS-002 |
| compressed/base64 nested payload | 是 | parser 搜索 | 未见 gzip/base64 fallback | 无 |

## 8. 最终结论示例

本轮不应输出 confirmed。DS-001 和 DS-002 缺少本地 marker 与执行证据，保持 candidate。DS-003 有签名前置阻断证据，标记 blocked。DS-004 只有依赖存在无调用，标记 dependency-only。
