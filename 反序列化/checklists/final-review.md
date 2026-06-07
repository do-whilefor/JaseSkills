# final-review

本清单用于交付前反向审判。默认立场：第一轮结果仍可能存在误判、漏报、缺证据或状态过高。

## 1. confirmed 降级审判

- [ ] 是否存在没有本地动态验证的 confirmed。
- [ ] 是否存在没有无害 marker 的 confirmed。
- [ ] 是否存在没有正向样本的 confirmed。
- [ ] 是否存在没有负向样本的 confirmed。
- [ ] 是否存在没有阻断样本或无阻断说明的 confirmed。
- [ ] 是否存在没有日志或断言的 confirmed。
- [ ] 是否存在没有清理记录的 confirmed。
- [ ] 是否存在没有 source 到 sink 调用链的 confirmed。
- [ ] 是否存在只有依赖存在的 confirmed。
- [ ] 是否存在只有关键字命中的 confirmed。

处理动作：任一项为“是”，该 finding 降级为 candidate，并写入降级清单。

## 2. candidate 补测审判

- [ ] 每个 candidate 是否有测试入口。
- [ ] 每个 candidate 是否有测试账号/权限或缺失说明。
- [ ] 每个 candidate 是否有输入样本。
- [ ] 每个 candidate 是否有 marker 设计。
- [ ] 每个 candidate 是否有正向样本。
- [ ] 每个 candidate 是否有负向样本。
- [ ] 每个 candidate 是否有阻断样本。
- [ ] 每个 candidate 是否有运行命令。
- [ ] 每个 candidate 是否有观测位置。
- [ ] 每个 candidate 是否有清理命令。
- [ ] 每个 candidate 是否有预期结果。
- [ ] 每个 candidate 是否说明当前缺口。

处理动作：缺少字段时补齐补测计划；不能补齐时写“未验证原因”。

## 3. 漏报追查审判

- [ ] 是否只看 HTTP，没有看 queue/cache/session/import/export/CLI/plugin。
- [ ] 是否只看 controller，没有看 worker、job、task、dead-letter、failed job。
- [ ] 是否忽略 database serialized column。
- [ ] 是否忽略 audit replay 或 event sourcing replay。
- [ ] 是否忽略 backup/restore。
- [ ] 是否忽略 plugin/theme/extension metadata。
- [ ] 是否忽略 workflow、rule engine、report template。
- [ ] 是否忽略 admin-only endpoint。
- [ ] 是否忽略 CLI maintenance command。
- [ ] 是否忽略 legacy parser、migration parser、debug parser、test parser。
- [ ] 是否忽略 parser fallback、content-type confusion。
- [ ] 是否忽略 base64/gzip/zip nested payload。
- [ ] 是否忽略签名验证在反序列化之后的顺序错误。
- [ ] 是否忽略低权限写入、高权限解析的权限错位。
- [ ] 是否忽略跨租户写入、后台统一解析的租户错位。

处理动作：任一项为“是”，补搜或写入漏报追查清单。

## 4. 状态分类审判

- [ ] dependency-only 是否没有被写成漏洞。
- [ ] not reachable 是否没有被写成 candidate 或 confirmed。
- [ ] blocked 是否明确阻断控制、阻断位置、错误信息或断言。
- [ ] false positive 是否说明排除原因。
- [ ] candidate 是否说明缺什么证据。
- [ ] confirmed 是否满足 12 项 confirmed 门槛。

## 5. 证据可复现审判

- [ ] 命令是否包含工作目录。
- [ ] 命令是否包含输入样本路径。
- [ ] 请求是否包含协议、方法、目标和样本文件。
- [ ] 日志是否包含文件路径或输出位置。
- [ ] marker 是否包含路径、触发方式和内容摘要。
- [ ] 清理动作是否包含命令和结果。
- [ ] 第三方是否能按报告复现。

## 6. 修复与回归审判

- [ ] P0 修复是否覆盖危险反序列化、safe loader、default typing、白名单、签名前置、DTO/schema、队列 schema、import/backup/restore 隔离、危险依赖移除。
- [ ] P1 修复是否覆盖 source/sink 单元测试、安全回归测试、依赖锁定、安全扫描、日志审计、类型解析告警、异常输入速率限制。
- [ ] P2 修复是否覆盖历史 serialized blob 重构、安全格式迁移、统一 adapter。
- [ ] 每个修复建议是否绑定回归测试位置。
- [ ] 没有回归测试位置时是否写明原因。

## 7. 输出前硬性结论

- [ ] 无动态证据的 confirmed 已全部降级。
- [ ] 无调用证据的依赖已标记 dependency-only。
- [ ] 不可达路径已标记 not reachable。
- [ ] 被安全控制阻断的路径已标记 blocked。
- [ ] 剩余 candidate 均有补测清单。
- [ ] 未覆盖内容均写入尚未覆盖原因。
- [ ] 未使用破坏性验证。
- [ ] 未虚构证据。
