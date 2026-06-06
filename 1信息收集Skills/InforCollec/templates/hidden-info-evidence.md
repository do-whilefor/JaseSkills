# 隐藏信息证据记录模板

| 字段 | 内容 |
|---|---|
| 候选编号 | HID-* |
| 隐藏信息类型 | comment / source_map / minified_js / service_worker / manifest / feature_flag / cicd / iac / test_seed / api_spec / ws / grpc / reverse_proxy / well_known |
| 来源文件 | 真实文件路径 |
| 行号 | 真实行号或 1 |
| 脱敏值 | 只允许脱敏样本、类型、长度、hash、key name |
| 漏洞关联价值 | 说明它可能帮助发现何种暴露面，但不能写成已确认漏洞 |
| 当前缺口 | 缺动态证据 / 缺角色矩阵 / 缺租户验证 / 缺代码来源 / 缺影响判断 |
| 下一步最小安全验证 | 只在授权本机范围内执行的非破坏动作 |
| 状态 | candidate / needs_review / not_reportable / confirmed |

硬规则：没有运行态证据、角色/租户上下文、质量门和人工复核时，状态不得超过 `needs_review`。
