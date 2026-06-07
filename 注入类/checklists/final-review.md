# Final Review

交付前反向审查清单。默认报告仍不可信，证据不足立即降级。

## confirmed 结论反查

- [ ] 真实启动项目。
- [ ] 有真实请求或真实触发步骤。
- [ ] 有正向样本。
- [ ] 有负向对照。
- [ ] 有唯一 marker。
- [ ] 有服务端日志或等效证据。
- [ ] 有数据库/文件/任务证据。
- [ ] 证明 marker 被解释器处理，或证明被安全机制拦截在解释器之前。
- [ ] 排除正常功能行为。
- [ ] 有可回滚方案。
- [ ] 缺任一项时已从 confirmed 降级。

## 解释器边界反查

每项都回答：项目是否使用；入口在哪里；用户能否影响输入；是否二阶触发；是否已动态验证；没验证原因；下一步最小安全验证。

- [ ] SQL
- [ ] NoSQL
- [ ] ORM raw query
- [ ] shell/command
- [ ] template engine
- [ ] expression language
- [ ] search DSL
- [ ] GraphQL resolver
- [ ] XPath
- [ ] LDAP
- [ ] XML parser
- [ ] JSONPath/JMESPath
- [ ] regex builder
- [ ] report engine
- [ ] export engine
- [ ] import parser
- [ ] workflow/rule engine
- [ ] email/notification renderer
- [ ] Markdown/HTML/PDF renderer
- [ ] queue worker
- [ ] scheduled job
- [ ] CLI command
- [ ] config parser
- [ ] logging/query system

## 二阶路径反查

每项都回答：谁能写入；写入后存在哪里；哪个功能读取；读取后是否进入解释器；是否更高权限触发；是否跨租户；是否异步；是否 marker 动态验证。

- [ ] 用户名、昵称、头像描述
- [ ] 评论、备注、工单、审批意见
- [ ] 地址、订单备注、发票信息
- [ ] 标签、分类、搜索关键词
- [ ] 模板配置、通知配置
- [ ] Webhook 配置
- [ ] OAuth/SAML/OIDC 配置
- [ ] 导入文件内容
- [ ] CSV/Excel 单元格
- [ ] Markdown/HTML 内容
- [ ] 管理后台配置项
- [ ] 工作流表达式
- [ ] 报表字段
- [ ] 邮件标题和正文
- [ ] 日志字段

## 隐藏参数反查

- [ ] 前端 JS bundle
- [ ] sourcemap
- [ ] OpenAPI/Swagger
- [ ] GraphQL schema
- [ ] DTO/model/schema
- [ ] controller binding
- [ ] validation schema
- [ ] form disabled field
- [ ] localStorage/sessionStorage
- [ ] feature flag
- [ ] admin-only route
- [ ] test/dev route
- [ ] mobile API
- [ ] legacy API
- [ ] webhook payload schema
- [ ] import/export schema
- [ ] 页面没暴露但后端接受的参数已列出。
- [ ] 文档没写但代码接受的参数已列出。
- [ ] 普通用户可传但前端不传的参数已列出。
- [ ] 影响 query/template/command/search 的参数已列出。
- [ ] 可改变执行路径的参数已列出。

## 封装、角色、非 HTTP 与严重性反查

- [ ] 检查自定义 SQL builder、sanitizer、escape、command wrapper、template helper、search query builder、GraphQL resolver helper、import/export parser、markdown/html renderer、validation middleware。
- [ ] 检查 raw bypass、allowlist 缺口、字段名拼接、order/sort/group/filter 拼接、转义后解码、编码顺序、content-type 绕过、数组/对象/字符串类型混淆。
- [ ] 检查匿名、普通、低权限管理员、高权限管理员、租户 A、租户 B、只读、API token、Webhook、后台任务身份。
- [ ] 检查 CLI、cron、queue、import、migration、seed、maintenance、backup/restore、report、file converter、image processor、PDF generator、email sender、webhook retry worker、search indexer。
- [ ] 所有 high/critical 均有动态请求、marker、解释器处理、负向对照、影响范围、回滚、修复点、误报排除。

## 冷门检查点

- [ ] sort/order/group/projection 字段注入
- [ ] 搜索语法注入
- [ ] 报表字段表达式注入
- [ ] 邮件模板预览注入
- [ ] 管理后台低代码规则注入
- [ ] Webhook 配置二阶注入
- [ ] 文件导入后异步任务触发注入
- [ ] CSV/Excel 导出内容注入
- [ ] Markdown 到 HTML 到 PDF 的多解释器链
- [ ] JSON object operator 注入
- [ ] GraphQL nested input 注入
- [ ] 任务队列 payload 注入
- [ ] 日志写入后日志查询注入
- [ ] 配置项进入 shell 命令
- [ ] 图片/PDF/压缩包处理参数进入命令行
- [ ] feature flag/debug 参数打开危险路径
- [ ] DTO 中存在但前端不传的危险字段
- [ ] content-type 切换导致校验失效
- [ ] Unicode/双重编码/大小写归一化差异
- [ ] 存储型字段由管理员页面触发解释

## 最终输出反查

- [ ] 被降级结论列表已输出。
- [ ] 新发现候选点已输出。
- [ ] 漏掉动态验证项已输出。
- [ ] 漏掉二阶路径已输出。
- [ ] 漏掉隐藏参数已输出。
- [ ] 漏掉解释器边界已输出。
- [ ] 漏掉角色/租户组合已输出。
- [ ] 需要补做的最小验证命令或请求已输出。
- [ ] confirmed、candidate、false positive、blocked 最终清单已输出。
- [ ] 已回答真实授权安全评估仍可能漏掉严重注入类缺陷的具体原因。
