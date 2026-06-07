# Local Auth Gate Audit 输出模板

## 0. 运行清单

| 字段 | 内容 |
|---|---|
| 项目名称 |  |
| project_root |  |
| base_url |  |
| 授权边界 |  |
| 执行时间 |  |
| 技术栈 |  |
| start_command |  |
| test_db_setup |  |
| seed/fixture 方式 |  |
| evidence_dir | `evidence/` |
| service_started | true / false |
| service_start_failure |  |
| 工具限制 |  |
| 本次是否允许写操作 | yes / no |
| 写操作回滚方式 |  |

## 1. 项目认证架构摘要

| 项 | 结论 | 证据路径 |
|---|---|---|
| 语言/框架 |  |  |
| 入口文件 |  |  |
| 启动方式 |  |  |
| 路由注册位置 |  |  |
| middleware 链 |  |  |
| 认证模块 |  |  |
| 权限模块 |  |  |
| session/token 模块 |  |  |
| User/Role/Permission 模型 |  |  |
| Tenant/Org/Team 模型 |  |  |
| Session/Token/APIKey 模型 |  |  |
| Invite/ResetPassword/EmailBinding/OAuthAccount 模型 |  |  |
| 前端权限入口 |  |  |
| HTTP/GraphQL/WebSocket/RPC 入口 |  |  |
| 文件/导入/导出/异步任务入口 |  |  |
| 认证、会话、权限、路由相关依赖 |  |  |

## 2. 将读取的文件清单

| 类别 | 路径/模式 | 目的 | 实际结果 |
|---|---|---|---|
| 启动说明 | README*, docs/* | 找启动命令 |  |
| 依赖 | package.json / pyproject.toml / pom.xml / go.mod / Cargo.toml | 识别框架和认证依赖 |  |
| 环境 | .env.example / config/* / docker-compose* | 找本地环境和 DB |  |
| 路由 | routes/** / controllers/** / app/** / src/** | 识别入口 |  |
| 认证 | auth/** / middleware/** / guards/** / policies/** | 识别门禁 |  |
| 模型 | models/** / prisma/** / migrations/** / entities/** | 识别账号、角色、租户、token |  |
| 前端 | src/** / pages/** / router/** / api/** | 识别隐藏入口和前端判断 |  |
| GraphQL | schema* / resolvers/** / graphql/** | 识别 resolver 和字段权限 |  |
| WebSocket | ws/** / socket/** / channels/** | 识别连接和消息权限 |  |
| 文件/导出/任务 | upload/** / files/** / jobs/** / workers/** | 识别文件与异步入口 |  |
| 测试 | test/** / tests/** / fixtures/** / seed/** | 识别测试账号和测试 DB |  |

## 3. 暴露面矩阵

| 入口名称 | 文件路径 | 方法/事件 | 是否需要登录 | 需要的角色/权限/租户 | 代码中的校验位置 | 动态验证方式 | 预期允许账号 | 预期拒绝账号 | 风险假设 | 证据需求 |
|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |

## 4. 动态验证环境

| 项 | 内容 | 证据 |
|---|---|---|
| 服务启动命令 |  |  |
| 服务地址 |  |  |
| 数据库模式 | 测试 DB / fixture / seed / transaction / blocked |  |
| 写操作回滚方式 |  |  |
| Playwright 可用性 | 可用 / 不可用 / 未使用 |  |
| API 测试方式 | supertest / pytest / requests / httpx / curl / REST client / 其他 |  |
| GraphQL 测试方式 |  |  |
| WebSocket 测试方式 |  |  |
| 日志位置 |  |  |
| 证据保存限制 |  |  |

## 5. 测试账号和角色矩阵

| 账号引用名 | 角色 | 租户 | 状态 | 资源样本 | 凭据保存方式 | 用途 |
|---|---|---|---|---|---|---|
| anonymous | 未登录 | 无 | 未登录 | 无 | 无 | 受保护入口反向测试 |
| user_a | 普通用户 | tenant_a | active |  |  | 本用户/本租户正向测试 |
| user_b | 普通用户 | tenant_b | active |  |  | 跨用户/跨租户反向测试 |
| manager_a | 管理员或中权限 | tenant_a | active |  |  | 管理接口边界测试 |
| admin | 系统管理员 | system | active |  |  | 管理接口正向测试 |
| disabled_user | 普通用户 |  | disabled/frozen |  |  | 禁用状态反向测试 |
| unverified_user | 普通用户 |  | unverified |  |  | 邮箱未验证反向测试 |
| expired_session_user | 普通用户 |  | expired |  |  | 过期会话反向测试 |

## 6. replay_results.json 记录模板

```json
[
  {
    "case_id": "AUTH-001",
    "entry": "",
    "account": "",
    "tenant": "",
    "sample_type": "positive_or_negative",
    "request": {
      "method": "",
      "url": "",
      "headers_ref": "",
      "body_ref": ""
    },
    "expected": {
      "status": [],
      "effect": ""
    },
    "actual": {
      "status": null,
      "key_fields": {},
      "effect": ""
    },
    "evidence_files": [],
    "verdict": "candidate",
    "reason": ""
  }
]
```

## 7. 已验证安全通过项

| case_id | 入口 | 反向样本 | 实际结果 | 证据文件 | 结论 |
|---|---|---|---|---|---|
|  |  |  |  |  | false_positive / 安全通过 |

## 8. confirmed 高影响缺陷

没有动态请求证据、正反对照、异常成功或越权效果、可复现步骤时，本节必须为空。

```markdown
## AUTH-XXX：<缺陷名称>

- 结论等级：confirmed
- 影响范围：
- 受影响接口/文件/函数：
- 触发前置条件：
- 测试账号和测试资源：
- 正向请求和预期成功结果：
- 反向请求和实际异常成功结果：
- HTTP 状态码：
- 响应关键字段：
- 数据库变化或日志证据：
- Playwright trace / HAR / 截图 / curl / 测试用例：
- 为什么这是认证/门禁缺陷，而不是测试误差：
- 最小修复建议：
- 修复后的 negative test：
- 严重性判断依据：
- 跨用户/跨角色/跨租户/跨状态/跨认证方式：
```

## 9. candidate 高风险线索

```markdown
## AUTH-CAND-XXX：<线索名称>

- 结论等级：candidate
- 风险假设：
- 受影响入口：
- 静态依据：
- 已执行验证：
- 缺失证据：
- 不能确认为 confirmed 的原因：
- 最小动态复现实验：
- 需要的测试账号/资源：
- 预期证据文件：
```

## 10. false positive 排除项

```markdown
## AUTH-FP-XXX：<排除项>

- 原风险假设：
- 正向测试：
- 反向测试：
- 实际结果：
- 排除依据：
- 证据文件：
```

## 11. blocked 项及阻塞原因

```markdown
## AUTH-BLOCK-XXX：<阻塞项>

- 阻塞原因：
- 已查找位置：
- 缺失输入：
- 本地补齐方式：
- 补齐后第一条验证命令：
- 当前允许结论：blocked
```

## 12. 小众/偏门路径专项结果

| 类别 | 测试入口 | 测试账号 | 正向样本 | 反向样本 | 请求构造 | 预期结果 | 实际结果 | 证据文件 | 结论等级 | 修复建议 |
|---|---|---|---|---|---|---|---|---|---|---|
| 路由顺序 |  |  |  |  |  |  |  |  |  |  |
| 中间件遗漏 |  |  |  |  |  |  |  |  |  |  |
| 方法差异 |  |  |  |  |  |  |  |  |  |  |
| 内容类型差异 |  |  |  |  |  |  |  |  |  |  |
| 参数来源差异 |  |  |  |  |  |  |  |  |  |  |
| 批量接口 |  |  |  |  |  |  |  |  |  |  |
| 软删除和状态机 |  |  |  |  |  |  |  |  |  |  |
| 邀请与重置流程 |  |  |  |  |  |  |  |  |  |  |
| 多租户隔离 |  |  |  |  |  |  |  |  |  |  |
| 本地缓存 |  |  |  |  |  |  |  |  |  |  |
| 异步任务 |  |  |  |  |  |  |  |  |  |  |
| 文件资源 |  |  |  |  |  |  |  |  |  |  |
| GraphQL |  |  |  |  |  |  |  |  |  |  |
| WebSocket |  |  |  |  |  |  |  |  |  |  |
| 依赖默认行为 |  |  |  |  |  |  |  |  |  |  |

## 13. 30 类非常规认证门禁测试计划

| # | 类别 | 测试入口 | 测试账号 | 正向样本 | 反向样本 | 请求构造 | 预期结果 | 实际结果 | 证据文件 | 结论等级 | 修复建议 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 路由混淆 |  |  |  |  | 尾斜杠、大小写、URL 编码、重复斜杠、空路径参数、后缀、locale、版本前缀 |  |  |  |  |  |
| 2 | 方法覆盖 |  |  |  |  | X-HTTP-Method-Override、_method、method fallback |  |  |  |  |  |
| 3 | 内容解析差异 |  |  |  |  | JSON、form、multipart、text/plain、空 body、重复 key、数组 key、嵌套对象 |  |  |  |  |  |
| 4 | 参数污染 |  |  |  |  | query/body、path/body、header/body 同名参数 |  |  |  |  |  |
| 5 | 默认值风险 |  |  |  |  | 缺 tenant_id、owner_id、role |  |  |  |  |  |
| 6 | ORM 查询风险 |  |  |  |  | where/filter/include/expand/select/order/group |  |  |  |  |  |
| 7 | 批处理风险 |  |  |  |  | 批量 ids 混入其他用户资源 |  |  |  |  |  |
| 8 | 导出风险 |  |  |  |  | 创建导出与下载导出分别验证 |  |  |  |  |  |
| 9 | 临时链接风险 |  |  |  |  | 预签名 URL、本地临时文件、附件 token |  |  |  |  |  |
| 10 | 缓存风险 |  |  |  |  | 本地应用缓存按用户、租户、权限隔离 |  |  |  |  |  |
| 11 | 状态流风险 |  |  |  |  | draft/pending/cancelled/deleted/archived |  |  |  |  |  |
| 12 | 邀请风险 |  |  |  |  | 跨邮箱、跨租户、重复使用 |  |  |  |  |  |
| 13 | 重置风险 |  |  |  |  | 密码重置后旧 session、reset token 一次性 |  |  |  |  |  |
| 14 | 邮箱绑定风险 |  |  |  |  | bind token 绑定到错误账号 |  |  |  |  |  |
| 15 | OAuth 绑定风险 |  |  |  |  | 绑定、解绑、重复绑定、state 校验 |  |  |  |  |  |
| 16 | WebSocket 风险 |  |  |  |  | 连接后切换 room/tenant/user_id |  |  |  |  |  |
| 17 | GraphQL 风险 |  |  |  |  | nested resolver、alias、fragment、batch query |  |  |  |  |  |
| 18 | 管理后台风险 |  |  |  |  | 菜单隐藏、按钮禁用但接口接受请求 |  |  |  |  |  |
| 19 | 错误处理风险 |  |  |  |  | 认证模块异常时 fallback allow |  |  |  |  |  |
| 20 | 测试/开发配置风险 |  |  |  |  | dev mode、mock auth、debug user、seed admin |  |  |  |  |  |
| 21 | 依赖升级风险 |  |  |  |  | 认证库、session、JWT、路由历史默认行为 |  |  |  |  |  |
| 22 | 多入口风险 |  |  |  |  | Web、API、移动端、后台、CLI、worker、webhook |  |  |  |  |  |
| 23 | 旧接口风险 |  |  |  |  | v1/v2、deprecated、legacy、compat route |  |  |  |  |  |
| 24 | 异步 worker 风险 |  |  |  |  | 入队时校验，执行时重新校验 |  |  |  |  |  |
| 25 | 审计日志风险 |  |  |  |  | 越权尝试是否有日志 |  |  |  |  |  |
| 26 | ID 生成风险 |  |  |  |  | 自增 ID、短 ID、可枚举 ID |  |  |  |  |  |
| 27 | 文件预览风险 |  |  |  |  | 缩略图、转码文件、缓存副本 |  |  |  |  |  |
| 28 | 软删除风险 |  |  |  |  | deleted_at 后 detail/export/download |  |  |  |  |  |
| 29 | 角色变更风险 |  |  |  |  | 降权后旧 session 权限 |  |  |  |  |  |
| 30 | 租户切换风险 |  |  |  |  | 多租户切换后的旧缓存或资源 |  |  |  |  |  |

## 14. 依赖与框架默认行为风险

| 依赖/框架 | 认证相关默认行为 | 项目配置 | 验证方式 | 结论等级 | 证据 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 15. 修复建议

| finding_id | 修复位置 | 最小修复建议 | 回归 negative test | 责任模块 |
|---|---|---|---|---|
|  |  |  |  |  |

## 16. 回归测试脚本清单

| 脚本路径 | 运行命令 | 覆盖入口 | 预期结果 | 证据输出 |
|---|---|---|---|---|
| tests/security/ |  |  |  |  |

## 17. 下一轮验证清单

- [ ] 补齐 blocked 中缺失的启动命令、测试账号、测试 DB 或环境变量。
- [ ] 对 candidate 执行最小动态复现实验。
- [ ] 对 confirmed 修复后执行 negative test。
- [ ] 对未覆盖入口补充正反样本。
- [ ] 复核 evidence/ 是否能独立复现结论。

## 18. 最终验收问答

1. 哪些认证门禁缺陷已经动态确认？
   - 
2. 哪些只是候选，为什么还不能确认？
   - 
3. 哪些路径没有覆盖，原因是什么？
   - 
4. 是否真实启动了服务并执行了请求？
   - 
5. 是否生成了可复跑测试？
   - 
6. 是否保留了 HAR、trace、截图、日志或测试输出？
   - 
7. 是否把所有 confirmed 都配了修复建议和回归测试？
   - 
8. 如果明天换一个审计人员，只根据 evidence/ 目录，能否复现结论？
   - 
```
