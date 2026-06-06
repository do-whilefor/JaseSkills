# 顶级信息收集报告模板

## 1. 授权范围
- scope_id：
- 授权根目录：
- 禁止路径 / 禁止目标：
- 网络策略：默认 `--no-network`，仅本机授权目标。

## 2. 项目指纹
- 项目结构：
- 语言：
- 框架：
- 包管理器 / 构建工具：
- 运行时：

## 3. 技术栈
| 类型 | 名称 | 证据 | 置信度 | 备注 |
|---|---|---|---|---|

## 4. 入口点总览
| 类型 | 数量 | 高价值候选 | 需人工复核 | 证据索引 |
|---|---:|---:|---:|---|

## 5. 路由/API 清单
| 方法 | 路径/操作 | 来源文件 | 行号 | 前端/后端/规格 | 证据 ID |
|---|---|---|---:|---|---|

## 6. 前端 JS 信息
- bundle / chunk：
- source map：
- service worker：
- manifest：
- feature flag / 实验功能：
- GraphQL operation：

## 7. 配置与部署信息
- env / config：
- Docker / Compose / K8s / Helm：
- Terraform / IaC：
- CI/CD：
- 日志 / 监控 / analytics：

## 8. 认证与鉴权信息
- 认证入口：
- 鉴权中间件 / guard / policy：
- session / JWT / OAuth / SAML / OIDC：

## 9. 角色与租户信息
- 角色字段：
- 租户 / 组织 / workspace 字段：
- owner / admin / permission / scope / policy 线索：

## 10. 第三方服务信息
| 服务 | 配置位置 | 暴露字段 | 已脱敏 | 证据 ID |
|---|---|---|---|---|

## 11. 隐藏信息清单
| 类型 | 候选值（脱敏） | 来源 | 漏洞关联价值 | 状态 | 证据 ID |
|---|---|---|---|---|---|

## 12. 高价值攻击面
| 攻击面 | 关联 Endpoint | Auth | Role | Tenant | Data Object | Evidence |
|---|---|---|---|---|---|---|

## 13. 需要人工复核的信息
| review_id | 原因 | 证据 ID | 推荐动作 |
|---|---|---|---|

## 14. 已脱敏敏感信息
- 不展示完整 secret、token、cookie、私钥、密码。
- 只保留 `discovered_item_value_redacted` 与 `raw_value_hash`。

## 15. 信息收集质量评分
- 总分：
- 缺失区块：
- 失败原因：

## 16. 未覆盖区域
| 区域 | 原因 | planned/partial/missing | 修复动作 |
|---|---|---|---|

## 17. 下一步漏洞挖掘建议
- 仅基于授权范围和证据链推进。
- candidate 不得直接写成 confirmed finding。

## 18. 证据索引
| evidence_id | collector | source_file | line | type | linked_report_section |
|---|---|---|---:|---|---|
