# 基础示例：单 REST 资源越权动态验证

## 输入

```text
项目路径：C:\work\local-notes-app
授权范围：仅限本机项目、本地 SQLite 测试数据库、本地测试账号。
本地 base URL：http://127.0.0.1:3000
目标入口：GET /api/notes/:id
```

## 暴露面矩阵行

| 入口名称 | 请求方法或事件名 | 路径 / resolver / handler | 代码文件 | 资源类型 | 资源归属字段 | 预期访问角色 | 预期禁止角色 | 预期租户边界 | 权限校验位置 | 可能缺失的校验点 | 动态验证方法 | 正向样本 | 反向样本 | 证据需求 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| note detail | GET | `/api/notes/:id` / `getNoteById` | `src/routes/notes.ts` | note | `owner_id` | owner, admin | anonymous, non-owner | 无租户 | `authRequired` | owner_id 校验 | curl | user_a -> user_a_note | user_a -> user_b_note | curl、响应体、服务端日志 | candidate |

## 动态验证

### 正向样本

```text
curl -i -H "Cookie: session=<user_a_cookie>" http://127.0.0.1:3000/api/notes/note_a
```

预期：200，响应中的 `owner_id` 为 user_a。

### 反向样本

```text
curl -i -H "Cookie: session=<user_a_cookie>" http://127.0.0.1:3000/api/notes/note_b
```

预期：403 或 404，不返回 user_b_note 内容。

## 分级示例

### confirmed

只有当反向样本返回 200，且响应体包含 `id=note_b`、`owner_id=user_b`、正文内容等越界数据，并且证据保存到 `evidence/curl/AUTHZ-20260607-001.txt`，才能写：

```text
结论等级：confirmed
原因：user_a 可读取 user_b_resource；反向样本出现异常成功；响应包含越界资源 owner_id=user_b。
```

### candidate

如果只看到 `getNoteById` 没有 owner 校验，但没有启动服务或没有请求证据，只能写：

```text
结论等级：candidate
原因：代码路径疑似缺少 owner_id scope，但缺少动态请求、正反对照和证据文件。
最小复现计划：启动本地服务，创建 user_a/user_b 与各自 note，执行正反 curl。
```

### false_positive

如果反向请求返回 403，且日志显示 `Forbidden: owner mismatch`，写：

```text
结论等级：false_positive
排除依据：动态验证证明后端拒绝 non-owner 访问。
证据文件：evidence/curl/AUTHZ-20260607-001-negative.txt
```

### blocked

如果服务无法启动，写：

```text
结论等级：blocked
阻塞原因：本地服务启动失败。
缺少什么：可运行的依赖或数据库配置。
本地补齐方法：修复 .env.test 后重新执行启动命令并保存 startup.log。
```
