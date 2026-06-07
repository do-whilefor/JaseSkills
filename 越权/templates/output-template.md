# 输出模板：本地授权越权动态验证报告

## 0. 审计依据与元数据

| 字段 | 内容 |
|---|---|
| TXT 来源 | 《越权提示词转skills.txt》 |
| 项目名称 |  |
| 项目路径 |  |
| 授权范围 |  |
| 本地 base URL |  |
| 测试数据库 |  |
| 执行时间 |  |
| evidence 目录 | `evidence/` |
| 结论等级范围 | confirmed / candidate / blocked / false_positive / needs_review |

## 1. 项目越权风险架构摘要

| 字段 | 内容 | 证据文件 |
|---|---|---|
| 编程语言 |  |  |
| 框架 |  |  |
| 入口文件 |  |  |
| 启动命令 |  |  |
| 路由注册方式 |  |  |
| 鉴权机制 |  |  |
| 会话/token 机制 |  |  |
| 用户模型 |  |  |
| 角色模型 |  |  |
| 租户/组织/团队模型 |  |  |
| 资源归属字段 |  |  |
| 权限校验集中位置 |  |  |
| 可能分散的校验位置 |  |  |
| 高风险入口概览 |  |  |
| blocked 项概览 |  |  |

## 2. 越权暴露面矩阵

| 入口名称 | 请求方法或事件名 | 路径 / resolver / handler | 代码文件 | 资源类型 | 资源归属字段 | 预期访问角色 | 预期禁止角色 | 预期租户边界 | 权限校验位置 | 可能缺失的校验点 | 动态验证方法 | 正向样本 | 反向样本 | 证据需求 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | untested |

允许状态：untested / candidate / confirmed / false_positive / blocked / needs_review。

## 3. 多角色 / 多租户测试矩阵

### 3.1 测试身份

| 账号标识 | 角色 | 租户 | 状态 | cookie/token 来源 | 创建方式 | 证据文件 | blocked 原因 |
|---|---|---|---|---|---|---|---|
| anonymous | 未登录 | 无 | 未登录 | 无 | 内置 |  |  |
| user_a | 普通用户 | tenant_a | 启用 |  |  |  |  |
| user_b | 普通用户 | tenant_b | 启用 |  |  |  |  |
| manager_a | tenant_a 管理员或中权限用户 | tenant_a | 启用 |  |  |  |  |
| manager_b | tenant_b 管理员或中权限用户 | tenant_b | 启用 |  |  |  |  |
| admin | 系统管理员 | 全局或管理租户 | 启用 |  |  |  |  |
| disabled_user | 禁用用户 | 任意测试租户 | 禁用 |  |  |  |  |
| readonly_user | 只读用户 | 任意测试租户 | 启用 |  |  |  |  |
| unverified_user | 未完成验证用户 | 任意测试租户 | 未验证 |  |  |  |  |
| role_changed_user | 降权测试用户 | 任意测试租户 | 已降权 | 旧 session / 旧 token |  |  |  |

### 3.2 测试资源

| 资源标识 | 资源类型 | 所属用户 | 所属租户 | 状态 | 创建方式 | 证据文件 | blocked 原因 |
|---|---|---|---|---|---|---|---|
| user_a_resource |  | user_a | tenant_a | active |  |  |  |
| user_b_resource |  | user_b | tenant_b | active |  |  |  |
| tenant_a_private_resource |  |  | tenant_a | private |  |  |  |
| tenant_b_private_resource |  |  | tenant_b | private |  |  |  |
| tenant_a_file | file |  | tenant_a | active |  |  |  |
| tenant_b_file | file |  | tenant_b | active |  |  |  |
| tenant_a_export_job | export_job |  | tenant_a | completed |  |  |  |
| tenant_b_export_job | export_job |  | tenant_b | completed |  |  |  |
| pending_resource |  |  |  | pending |  |  |  |
| approved_resource |  |  |  | approved |  |  |  |
| deleted_resource |  |  |  | deleted |  |  |  |
| archived_resource |  |  |  | archived |  |  |  |
| draft_resource |  |  |  | draft |  |  |  |

## 4. 动态验证环境说明

| 项 | 内容 | 证据文件 |
|---|---|---|
| 启动命令 |  | `evidence/logs/startup.log` |
| 数据库初始化命令 |  |  |
| seed / fixture 命令 |  |  |
| 登录方式 |  |  |
| token/cookie 保存位置 |  |  |
| 测试工具 | Playwright / curl / httpx / requests / supertest / pytest / Postman / GraphQL client / WebSocket client |  |
| 环境 blocked 项 |  | `evidence/blocked.md` |

## 5. 已确认高影响越权问题

### AUTHZ-YYYYMMDD-NNN：漏洞标题

| 字段 | 内容 |
|---|---|
| 漏洞标题 |  |
| 类型 | 水平越权 / 垂直越权 / 多租户越权 / 文件越权 / GraphQL 越权 / WebSocket 越权 / 业务流越权 |
| 影响接口 |  |
| 影响文件 |  |
| 影响角色 |  |
| 影响租户 |  |
| 影响资源 |  |
| 触发条件 |  |
| 正向请求 |  |
| 反向请求 |  |
| 实际异常成功结果 |  |
| 状态码 |  |
| 响应关键字段 |  |
| 数据库或日志证据 |  |
| HAR / trace / screenshot / curl / test output 路径 |  |
| 可复现步骤 |  |
| 最小修复建议 |  |
| 修复后的回归测试 |  |
| 严重性判断 |  |
| 结论等级 | confirmed |

## 6. 候选高风险线索

| 编号 | 入口 | 可疑代码文件 | 可疑点 | 缺失的动态证据 | 最小动态复现计划 | 当前结论 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  | candidate |

## 7. 已排除误报

| 编号 | 入口 | 怀疑点 | 动态请求 | 拒绝结果 | 排除依据 | 证据文件 | 结论 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  | false_positive |

## 8. 阻塞项和补齐办法

| 编号 | 阻塞对象 | 阻塞原因 | 缺少什么 | 本地补齐方法 | 影响范围 | 当前结论 |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  | blocked |

## 9. 小众 / 偏门路径专项结果

| 测试编号 | 测试主题 | 测试入口 | 测试账号 | 测试资源 | 请求构造 | 预期结果 | 实际结果 | 证据文件 | 结论等级 | 修复建议 |
|---|---|---|---|---|---|---|---|---|---|---|
| UC-01 | 尾斜杠差异：/api/a 与 /api/a/ |  |  |  |  | 权限一致，不绕过 guard |  |  |  |  |
| UC-02 | 大小写差异：/Admin 与 /admin |  |  |  |  | 权限一致，不绕过 guard |  |  |  |  |
| UC-03 | URL 编码差异：%2f、%2e、双重编码 |  |  |  |  | 不绕过 guard |  |  |  |  |
| UC-04 | 重复斜杠：/api//admin |  |  |  |  | 不绕过 guard |  |  |  |  |
| UC-05 | 路径参数为空或特殊值：0、-1、null、undefined、me、self、current |  |  |  |  | 不越界解析资源 |  |  |  |  |
| UC-06 | 后缀格式：.json、.csv、.download、.preview |  |  |  |  | 权限一致 |  |  |  |  |
| UC-07 | 版本前缀：/v1、/v2、/legacy、/internal |  |  |  |  | 旧接口权限一致 |  |  |  |  |
| UC-08 | locale 前缀：/en/admin、/zh/admin |  |  |  |  | 不绕过 guard |  |  |  |  |
| UC-09 | X-HTTP-Method-Override |  |  |  |  | 不提升方法权限 |  |  |  |  |
| UC-10 | _method 参数覆盖 |  |  |  |  | 不提升方法权限 |  |  |  |  |
| UC-11 | query/body 同名参数污染 |  |  |  |  | 不信任客户端身份字段 |  |  |  |  |
| UC-12 | path/body 同名参数污染 |  |  |  |  | 路径资源与 body 归属一致校验 |  |  |  |  |
| UC-13 | header/body 同名参数污染 |  |  |  |  | 不信任 header 身份字段 |  |  |  |  |
| UC-14 | tenant_id 缺失时是否默认全局查询 |  |  |  |  | 不默认全局查询 |  |  |  |  |
| UC-15 | owner_id 缺失时是否默认返回首条资源 |  |  |  |  | 不返回首条越界资源 |  |  |  |  |
| UC-16 | role 缺失时是否走默认 allow |  |  |  |  | 默认拒绝 |  |  |  |  |
| UC-17 | include/expand 泄露关联对象 |  |  |  |  | 关联对象带 scope |  |  |  |  |
| UC-18 | fields/select 返回隐藏字段 |  |  |  |  | 字段级权限有效 |  |  |  |  |
| UC-19 | sort/group/filter 影响查询范围 |  |  |  |  | 查询范围不越界 |  |  |  |  |
| UC-20 | 批量 ids 混入其他用户资源 |  |  |  |  | 失败或只返回合法部分且不泄露 |  |  |  |  |
| UC-21 | 批量操作部分成功导致信息泄露 |  |  |  |  | 不泄露非法 id 状态 |  |  |  |  |
| UC-22 | 导出任务创建者和下载者不一致 |  |  |  |  | 下载时重新校验 |  |  |  |  |
| UC-23 | 临时文件 URL 不绑定用户 |  |  |  |  | URL 绑定用户或二次校验 |  |  |  |  |
| UC-24 | 缩略图绕开原文件权限 |  |  |  |  | 缩略图权限一致 |  |  |  |  |
| UC-25 | 预览接口绕开下载权限 |  |  |  |  | 预览权限一致 |  |  |  |  |
| UC-26 | 归档资源仍可 detail |  |  |  |  | 状态机校验一致 |  |  |  |  |
| UC-27 | deleted_at 资源仍可 export |  |  |  |  | 删除态不可越权导出 |  |  |  |  |
| UC-28 | 草稿资源被他人读取 |  |  |  |  | 草稿仅 owner 可读 |  |  |  |  |
| UC-29 | 待审批资源被低权限审批 |  |  |  |  | 审批角色校验有效 |  |  |  |  |
| UC-30 | 已取消订单被继续操作 |  |  |  |  | 取消态不可继续操作 |  |  |  |  |
| UC-31 | 降权后旧 token 仍有旧权限 |  |  |  |  | 旧 token 权限失效或重新校验 |  |  |  |  |
| UC-32 | 移出租户后旧 session 仍能访问租户资源 |  |  |  |  | membership 变化即时生效 |  |  |  |  |
| UC-33 | WebSocket 连接后切换 tenant_id |  |  |  |  | message 层重新校验 |  |  |  |  |
| UC-34 | WebSocket 订阅他人 room |  |  |  |  | room 归属校验有效 |  |  |  |  |
| UC-35 | GraphQL alias 读取隐藏字段 |  |  |  |  | 字段级校验有效 |  |  |  |  |
| UC-36 | GraphQL fragment 组合绕过字段级校验 |  |  |  |  | fragment 不绕过校验 |  |  |  |  |
| UC-37 | GraphQL nested resolver 泄露关联资源 |  |  |  |  | nested resolver 带 scope |  |  |  |  |
| UC-38 | GraphQL batch query 混入越权对象 |  |  |  |  | 批量对象逐项校验 |  |  |  |  |
| UC-39 | 管理菜单隐藏但 API 可访问 |  |  |  |  | 后端拒绝普通用户 |  |  |  |  |
| UC-40 | 前端禁用按钮但后端接受请求 |  |  |  |  | 后端拒绝非法写操作 |  |  |  |  |
| UC-41 | mobile API 权限弱于 web API |  |  |  |  | 多端权限一致 |  |  |  |  |
| UC-42 | worker 执行时不重新校验资源归属 |  |  |  |  | worker 执行前重新校验 |  |  |  |  |
| UC-43 | webhook 重放导致跨租户状态变化 |  |  |  |  | webhook 验签、幂等、租户绑定 |  |  |  |  |
| UC-44 | invite token 跨邮箱使用 |  |  |  |  | token 绑定邮箱和租户 |  |  |  |  |
| UC-45 | reset token 使用后仍有效 |  |  |  |  | token 一次性失效 |  |  |  |  |
| UC-46 | email binding token 绑定到错误账号 |  |  |  |  | token 绑定账号 |  |  |  |  |
| UC-47 | OAuth bind state 与当前用户不一致 |  |  |  |  | state 绑定会话 |  |  |  |  |
| UC-48 | API key 权限大于所属用户 |  |  |  |  | API key 权限不超过主体 |  |  |  |  |
| UC-49 | service account 越权访问租户数据 |  |  |  |  | service account 限制租户范围 |  |  |  |  |
| UC-50 | 本地缓存按接口缓存但未按用户隔离 |  |  |  |  | 缓存键包含用户/租户权限上下文 |  |  |  |  |

## 10. 依赖和框架默认行为风险

| 依赖/框架 | 相关文件 | 默认行为 | 风险点 | 动态验证方法 | 结论等级 | 证据 |
|---|---|---|---|---|---|---|
|  |  | 默认 allow / trust header / debug user / mock auth / ORM scope 缺失 |  |  |  |  |

## 11. 修复建议

| 编号 | 问题 | 缺失校验位置 | 校验对象 | 校验条件 | 失败返回 | 最小修复建议 | 回归测试 |
|---|---|---|---|---|---|---|---|
|  |  |  | user / role / tenant / owner / state / token / file ownership |  | 403/404 或业务规定拒绝 |  |  |

## 12. 回归测试清单

| 编号 | 覆盖漏洞 | 测试文件 | 正向断言 | 反向断言 | 执行命令 |
|---|---|---|---|---|---|
|  |  | `evidence/tests/...` |  |  |  |

## 13. 下一轮深挖计划

| 优先级 | 入口 | 原因 | 所需账号/资源 | 所需证据 | 预计结论 |
|---|---|---|---|---|---|
| P0 |  |  |  |  | candidate / blocked |

# evidence 文件内容模板

## evidence/replay_plan.md

| 编号 | 入口 | 计划请求 | 账号 | 资源 | 预期 | 所需证据 | 当前状态 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  | planned |

## evidence/replay_results.json

```json
[
  {
    "id": "AUTHZ-YYYYMMDD-NNN",
    "entry": "",
    "account": "",
    "resource": "",
    "request": {"method": "", "path": "", "params": {}, "body": {}, "token_source": ""},
    "expected": "",
    "actual": {"status": 0, "key_fields": {}, "db_change": "", "log": ""},
    "evidence_files": [],
    "conclusion": "candidate"
  }
]
```

## evidence/blocked.md

| 编号 | 阻塞对象 | 缺少什么 | 错误或证据 | 本地补齐方法 | 影响入口 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
