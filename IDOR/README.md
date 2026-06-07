# local-object-access-audit

## 用途

`local-object-access-audit` 将 TXT 中的“本地对象引用访问控制动态验证”流程复刻为 Claude 可调用的 Skill。它只处理本地授权测试环境，不处理公网目标，不扫描第三方资产，不读取真实隐私数据，不破坏数据库，不删除业务数据。

## 使用条件

调用前必须准备：

1. 本地项目路径或仓库目录。
2. 本地服务地址，例如 `http://127.0.0.1:3000`。
3. `user_a`、`user_b`、`manager_a`、`admin_local`、`anonymous`。
4. `tenant_a`、`tenant_b` 及每类关键资源的 marker 测试数据。
5. 可回滚方式。
6. 证据输出目录。

## 交付物

执行后输出：

1. 访问控制暴露面矩阵。
2. 测试身份与测试资源清单。
3. 资源归属证明。
4. 真实请求清单。
5. 动态验证结果。
6. `confirmed` / `blocked` / `candidate` / `false_positive` 四类结果。
7. 反向审计回答。
8. 遗漏路径清单。
9. 非常规路径补测结果。
10. 修复优先级。
11. 回归测试脚本或脚本模板。

## 文件说明

| 文件 | 作用 | 来源类型 |
|---|---|---|
| `SKILL.md` | Claude 调用 Skill 时执行的主规则 | 原文复刻 + 工程化补强 |
| `templates/output-template.md` | 最终报告模板 | 原文输出要求 + 工程化补强 |
| `checklists/quality-gate.md` | 执行中质量门禁 | 原文纪律 + 工程化补强 |
| `checklists/final-review.md` | 交付前追责反查清单 | 原文反向审计 + 工程化补强 |
| `examples/basic-example.md` | 单接口对象越界验证示例 | 工程化补强，贴合原文主题 |
| `examples/full-example.md` | 完整运行示例 | 工程化补强，贴合原文主题 |
| `tests/skill-quality-tests.md` | 检查 Skill 是否偏离 TXT 的测试集 | 工程化补强 |

## 关键原则

1. `confirmed` 必须有动态请求证据。
2. `confirmed` 必须有资源归属证明。
3. 只有状态码 200 不代表越界成功。
4. 前端隐藏按钮不代表后端缺陷。
5. 管理员设计允许的访问不是漏洞。
6. 没执行就写 `not_run`。
7. 不确定就降级为 `candidate`。
8. 非常规路径必须补测，不能执行时写明 `not_run`、`blocked` 或 `failed`。

## 推荐调用语句

```text
请使用 local-object-access-audit Skill，对本地项目 <project_path> 和本地服务 <local_base_url> 做对象引用访问控制动态验证。测试账号为 user_a、user_b、manager_a、admin_local、anonymous。所有证据写入 <evidence_dir>，只使用 marker 测试数据，不访问公网，不读取真实隐私数据。
```

## 安全边界

若目标不是本地授权环境，或无法证明授权，本 Skill 必须停止动态验证，并输出缺失项与原因。
