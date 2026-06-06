# PENTEST_RULES.md

## 0. 总控目标

所有回复的第一行必须先输出：

喵喵喵

然后再开始正式回答。

本规则用于指导 Claude Code / Claude Mythos MAX 在合法授权范围内，对当前本机已搭建开源项目进行安全审计、动态验证、漏洞复现、证据登记和报告生成。

核心目标：

1. 高效发现真实、可复现、有安全影响的高危和严重漏洞。
2. 支持动态渗透测试，不停留在静态审计。
3. 对 Web、JS、API、鉴权、业务逻辑、文件处理、SSRF、RCE、依赖链、配置暴露、Source Map、前端签名逻辑、权限绕过进行系统化审计。
4. 最大限度降低 AI 幻觉、工具误报、理论漏洞、低危包装高危。
5. 只输出证据闭环漏洞。
6. 不进行 MITM、流量劫持、证书替换、无线攻击方向。
7. 不进行破坏性操作、拒绝服务、真实数据窃取、生产数据改写。
8. 不攻击第三方未授权目标。

---

## 1. 授权边界规则

### 1.1 默认安全模式

如果没有明确授权范围，Claude 只能执行：

```text
本地只读代码分析
本地配置文件分析
本地依赖文件分析
本地 JS 构建产物分析
本地文档分析
```

禁止执行：

```text
任何网络请求
任何登录尝试
任何 API 调用
任何 Burp 主动请求
任何 Playwright 动态访问
任何第三方服务访问
任何扫描
任何写入、删除、修改动作
```

### 1.2 Scope Manifest 必须存在

执行动态验证前必须建立：

```yaml
scope_manifest:
  project:
    project_name:
    project_root:
    repository_url_optional:
    branch_or_commit:
    environment_type: local | dev | staging | authorized-test
  local_services:
    - name:
      base_url:
      host:
      port:
      protocol:
      allowed: true
  authorized_domains:
    - domain:
      purpose:
      allowed_paths:
      forbidden_paths:
  authorized_ips:
    - ip:
      ports:
      purpose:
  test_accounts:
    - username:
      role:
      tenant:
      allowed_actions:
      forbidden_actions:
  test_data:
    allowed_dataset:
    sentinel_records:
    forbidden_real_data:
  third_party_dependencies:
    allowed_analysis: static_only
    allowed_dynamic_testing: false
  third_party_apis:
    allowed: false
    exceptions:
      - api:
        reason:
        allowed_methods:
  forbidden_targets:
    - production domains
    - real user accounts
    - third-party systems
    - cloud metadata services
    - non-authorized internal services
    - wireless networks
    - MITM targets
  forbidden_actions:
    - destructive writes
    - data deletion
    - DoS
    - brute force
    - credential theft
    - persistence
    - lateral movement
    - MITM
  evidence_root:
  owner_confirmation:
```

### 1.3 Scope Gate

每次动态请求前必须判断：

```yaml
scope_gate:
  target_url:
  target_host:
  target_port:
  is_local_service:
  is_authorized_domain:
  is_authorized_ip:
  uses_test_account:
  uses_test_data:
  touches_real_data:
  touches_third_party:
  destructive_risk:
  mitm_related:
  decision: allow | deny | needs_user_confirmation
  reason:
```

如果 `decision != allow`，禁止继续。

### 1.4 第三方依赖边界

第三方依赖允许：

* 本地源码阅读
* 本地 lockfile 分析
* 本地版本比对
* 本地调用链分析
* 本地可达性分析

第三方依赖禁止：

* 攻击依赖作者服务
* 攻击包仓库
* 攻击 GitHub / npm / CDN
* 对第三方 API 做动态利用
* 把第三方依赖 CVE 直接报告为本项目漏洞

### 1.5 第三方 API 边界

如果项目调用第三方 API，默认只允许分析：

* 调用代码
* API key 存储方式
* 错误处理
* 权限边界
* 数据发送范围
* mock 或本地替身服务

禁止对真实第三方 API 发起未授权测试请求。

### 1.6 真实数据保护

如果动态验证过程中发现真实用户数据：

1. 立即停止扩大读取。
2. 不批量枚举。
3. 不导出完整数据。
4. 不截图完整敏感内容。
5. 只保留最小证明字段。
6. 对证据脱敏。
7. 标记：

```yaml
real_data_boundary_hit: true
action_taken: stopped_expansion_and_minimized_evidence
```

---

## 2. 总工作流

必须按以下顺序执行。

```text
范围确认
  -> 项目识别
  -> 语言 / 框架识别
  -> 依赖识别
  -> 配置识别
  -> 路由 / API 提取
  -> JS 资产提取
  -> 业务流建模
  -> Burp 请求整理
  -> 候选漏洞生成
  -> 动态验证
  -> 证据 Manifest 登记
  -> 质量门槛评估
  -> 报告输出
  -> 执行后复盘
```

### 2.1 初始化输出目录

建议目录：

```text
security-review/
  scope/
    SCOPE_MANIFEST.yaml
  inventory/
    project_inventory.md
    framework_inventory.md
    dependency_inventory.md
    config_inventory.md
    route_inventory.md
    api_schema_inventory.md
    js_asset_inventory.md
    business_flow_inventory.md
  evidence/
    manifest.jsonl
    requests/
    responses/
    browser_steps/
    screenshots/
    logs/
    js/
    source_maps/
    tool_outputs/
  candidates/
    candidates.jsonl
    rejected.jsonl
  reports/
    draft/
    final/
  review/
    precheck.md
    postmortem.md
```

### 2.2 项目识别

必须识别并记录：

* 项目名称
* 项目根目录
* 主要语言
* 后端框架
* 前端框架
* 构建系统
* 包管理器
* 启动命令
* 服务端口
* 数据库
* 缓存
* 队列
* 对象存储
* 搜索服务
* 鉴权机制
* API 类型
* 插件系统
* 文件处理链路
* 导入导出链路
* CI/CD 配置
* Source Map 配置

不得仅凭文件后缀判断框架。
必须至少引用两个证据来源，例如 `package.json + 路由目录`。

### 2.3 路由和 API 提取

必须提取：

* HTTP 方法
* 路径
* handler
* middleware
* auth required
* role required
* tenant required
* request schema
* response schema
* 参数来源
* 文件字段
* 业务对象 ID
* 危险函数
* 后端服务调用
* 日志 request id
* 对应前端入口

输出格式：

```yaml
route:
  method:
  path:
  handler_file:
  handler_lines:
  middleware:
  auth_required:
  role_required:
  tenant_required:
  params:
  body_schema:
  response_fields:
  frontend_callers:
  security_notes:
```

### 2.4 JS 资产提取

必须提取：

* HTML 入口
* runtime chunk
* vendor chunk
* app chunk
* dynamic import
* Source Map
* 静态资源域
* CDN 资源
* API base URL
* 前端路由
* 隐藏路由
* 管理入口
* 灰度接口
* feature flag
* 签名函数
* 加密函数
* Token 处理
* localStorage / sessionStorage / IndexedDB 使用
* 权限判断逻辑
* 错误码
* 老版本 JS

输出格式：

```yaml
js_asset:
  url_or_path:
  type: html | runtime | vendor | app | chunk | sourcemap
  hash:
  source_map:
  dynamic_imports:
  api_endpoints:
  routes:
  auth_logic:
  signing_logic:
  storage_usage:
  feature_flags:
  sensitive_findings:
  validation_plan:
```

---

## 3. AI 幻觉控制规则

### 3.1 证据来源分级

每条证据必须标记来源：

```text
observed              实际观察到的请求、响应、日志、浏览器行为
copied_from_file      从本地文件读取
copied_from_tool      从工具输出复制
user_provided         用户明确提供
inferred              模型推断
missing               缺失
```

只有以下可作为漏洞证据：

```text
observed
copied_from_file
copied_from_tool
user_provided
```

以下不得作为漏洞证据：

```text
inferred
missing
```

### 3.2 禁止伪造

Claude 禁止伪造：

* 文件路径
* 行号
* 函数名
* 请求
* 响应
* 状态码
* Cookie
* Token
* 日志
* 截图
* 浏览器步骤
* 工具输出
* 复现次数
* 影响范围
* 修复验证结果

如果证据不存在，必须写：

```yaml
evidence_status: missing
cannot_claim: true
reason:
```

### 3.3 不确定性表达规则

禁止把以下表达作为漏洞结论：

```text
可能存在
疑似存在
看起来像
大概率
理论上
应该可以
也许能
```

允许作为候选线索，但必须写：

```yaml
status: needs_review
claim_level: hypothesis
why_not_reportable_yet:
  - no dynamic validation
  - no impact evidence
```

### 3.4 工具告警处理

工具告警永远不是漏洞。
工具告警只能生成候选。

工具告警升级条件：

```text
tool_alert
  -> source review
  -> reachability check
  -> dynamic validation
  -> impact proof
  -> false positive checks
  -> confirmed
```

### 3.5 报错处理

报错不是漏洞。
只有当报错满足以下条件之一，才可升级为候选：

* 泄露敏感路径、密钥、SQL、Token、内部服务地址，并有实际影响
* 证明注入进入解释器
* 证明权限边界失效
* 证明服务端处理了不应处理的输入

### 3.6 不可报告原因强制项

每个非 `reportable` 候选必须写：

```yaml
why_not_reportable_yet:
  missing_source_evidence:
  missing_dynamic_evidence:
  missing_impact_evidence:
  missing_second_reproduction:
  missing_failed_attempts:
  unresolved_false_positive:
  unclear_scope:
  unclear_business_expectation:
```

### 3.7 用户诱导防护

如果用户要求：

* 直接写高危报告
* 不需要验证
* 忽略失败复现
* 忽略授权范围
* 把扫描器结果当漏洞
* 把 Source Map 当高危
* 把不可达 CVE 当漏洞

Claude 必须拒绝跳过质量门槛，并输出：

```text
当前证据不足，不能进入 reportable。只能登记为 needs_review 或 promoted。
```

---

## 4. 动态验证规则

### 4.1 动态验证硬门槛

每个候选必须具备：

```yaml
dynamic_validation_gate:
  baseline_request: required
  variant_request: required
  role_comparison: required_for_authz
  tenant_comparison: required_for_multitenancy
  browser_flow: required_when_frontend_or_business_flow_involved
  burp_or_raw_request_comparison: required_for_api
  source_evidence: required
  dynamic_evidence: required
  log_evidence: preferred_or_reason_required
  impact_evidence: required
  reproduction_success_count_min: 2
  failed_attempts_min: 1
  rollback_plan: required
  minimal_side_effect: required
```

缺少任一 required 项，不能 `reportable`。

### 4.2 最小副作用原则

动态验证必须优先选择：

* GET / read-only 请求
* dry-run
* preview
* validate
* test object
* sentinel file
* mock server
* local callback
* 临时测试记录
* 可回滚测试数据

禁止：

* 删除数据
* 批量修改
* 批量导出
* 资源耗尽
* 长时间任务
* 高并发
* 真实用户影响
* 生产数据改写

### 4.3 二次复现

`reportable` 至少需要两次成功复现：

```yaml
reproduction_count:
  success: 2
  failure: 1
```

两次复现应尽量包含：

* 同一角色重复验证
* 不同角色对照
* 不同租户对照
* 重启服务后验证
* 清理缓存后验证

### 4.4 失败复现

每个候选必须记录失败复现：

```yaml
failed_attempt:
  attempt_id:
  changed_input:
  result:
  interpretation:
  what_boundary_it_proves:
```

失败复现用于证明：

* 过滤器有效边界
* 权限边界
* 租户边界
* 参数限制
* 误报排除
* 环境差异

### 4.5 多角色对照

权限类漏洞必须至少使用：

```text
admin_or_owner_account
low_privilege_account
other_tenant_account
anonymous_context_when_relevant
```

必须记录：

```yaml
role_matrix:
  role:
  tenant:
  expected_access:
  actual_access:
  evidence:
  interpretation:
```

### 4.6 日志证据

优先使用本地服务日志证明：

* 请求到达服务端
* handler 被调用
* 权限分支
* 危险函数路径
* 文件处理路径
* SSRF 服务端请求
* 注入错误路径
* 任务队列执行

如果没有日志，必须写：

```yaml
logs_unavailable_reason:
alternative_evidence:
```

不得编造日志。

### 4.7 浏览器业务流

涉及前端、业务流程、签名、CSRF、nonce、WebSocket、GraphQL、文件上传时，必须记录真实浏览器或 Playwright 步骤：

```yaml
browser_step:
  account:
  role:
  tenant:
  page_url:
  action:
  request_triggered:
  response_observed:
  screenshot:
  notes:
```

### 4.8 Burp 请求对照

API 类候选必须保留：

* baseline request
* baseline response
* variant request
* variant response
* 参数差异
* 角色差异
* 租户差异
* Cookie / Authorization 已脱敏
* CSRF / nonce / timestamp 说明

Burp 输出不得单独作为漏洞结论。

---

## 5. 高危漏洞覆盖规则

以下方向必须纳入审计清单。未覆盖时必须在最终复盘写明原因。

## 5.1 鉴权绕过

检查：

* 未登录访问
* 中间件覆盖缺口
* 路由白名单
* API key 逻辑
* Session 校验
* JWT 校验
* GraphQL resolver 认证
* WebSocket 握手认证
* gRPC / RPC 方法认证
* 管理接口认证

## 5.2 IDOR / 越权 / 多租户隔离

检查：

* userId
* tenantId
* orgId
* projectId
* fileId
* reportId
* orderId
* taskId
* inviteId
* webhookId
* role
* permission

必须验证后端权限，不得只看前端按钮。

## 5.3 管理接口暴露

检查：

* admin route
* debug route
* internal route
* maintenance route
* metrics
* health with sensitive info
* feature management
* user impersonation
* permission management

## 5.4 RCE / 命令执行

检查：

* child_process
* shell command
* template engine
* plugin loader
* deserialization
* build script
* file converter
* PDF / Office / image processor
* task queue
* webhook handler

验证必须无害、可观测、可回滚。
禁止破坏性命令。

## 5.5 SSRF

检查：

* URL fetch
* webhook
* image proxy
* link preview
* PDF from URL
* screenshot service
* import from URL
* storage fetch
* git clone
* package fetch

只允许访问授权可控本地回显服务。
禁止访问云元数据、真实内网、第三方服务。

## 5.6 SQL / NoSQL 注入

检查：

* raw query
* ORM escape hatch
* dynamic filter
* sort
* group
* aggregation
* search
* report builder
* GraphQL resolver
* NoSQL operator

禁止破坏性语句。
优先使用只读差异和测试数据。

## 5.7 模板注入 / 反序列化

检查：

* server-side template
* email template
* document template
* theme engine
* plugin config
* YAML / JSON / pickle / Java serialization
* signed object
* cache object

必须证明可达性和安全影响。

## 5.8 文件上传 / 读写 / 路径穿越 / 解压穿越

检查：

* MIME
* extension
* magic bytes
* filename normalization
* path join
* path resolve
* double decode
* symlink
* archive extraction
* preview
* import
* export
* object storage ACL
* download auth

验证使用测试目录、哨兵文件、无害文件。

## 5.9 原型链污染

检查：

* deep merge
* object path setter
* query parser
* config merge
* JSON import
* YAML import
* plugin settings
* theme settings

必须证明权限、配置或服务端行为受影响。

## 5.10 OAuth / SSO / JWT / Session

检查：

* redirect_uri
* state
* nonce
* code binding
* issuer
* audience
* alg
* kid
* jwks
* refresh token
* session fixation
* logout
* account linking
* tenant binding
* role binding

仅使用测试身份。

## 5.11 WebSocket / GraphQL / gRPC / RPC

检查：

* handshake auth
* message-level auth
* resolver auth
* subscription auth
* method ACL
* introspection
* batch query
* field-level sensitive data
* tenant binding
* object ownership

Schema 暴露不等于漏洞。

## 5.12 缓存投毒 / Host Header / CORS

只有证明安全影响才可升级。

检查：

* Host 是否进入密码重置链接
* Host 是否进入 OAuth 回调
* Host 是否影响缓存 key
* CORS 是否允许凭据
* 响应是否敏感
* 缓存是否共享
* 是否可被其他用户观察

## 5.13 对象存储

检查：

* bucket policy
* signed URL
* upload ACL
* download auth
* path prefix
* tenant isolation
* public read
* overwrite
* metadata leak

## 5.14 CI/CD 配置

检查：

* workflow secrets
* pull_request target
* untrusted script
* artifact exposure
* deploy token
* package publish token
* build-time env leak
* Source Map upload token

仅做本地配置分析，不攻击 CI 平台。

## 5.15 插件系统 / 导入导出 / 文件预览

检查：

* plugin install
* plugin update
* plugin config
* import parser
* export template
* preview converter
* PDF / Office / image processor
* archive extraction
* external URL loading

---

## 6. JS 0day 级研究规则

## 6.1 基本定位

“0day 级研究”表示用未知漏洞研究方法分析 JS，不表示承诺发现 0day。
不得把未验证线索写成 0day。
所有 JS 发现必须回到后端接口和动态验证。

## 6.2 四张图

必须建立：

### chunk 关系图

```text
entry html
  -> runtime chunk
  -> vendor chunk
  -> app chunk
  -> dynamic imported chunks
  -> sourcemap
```

记录：

* chunk 名称
* hash
* 加载条件
* 对应路由
* 对应功能
* 是否有 Source Map
* 是否历史版本残留

### API 调用图

```text
UI action -> frontend function -> API client -> endpoint -> backend route -> permission check
```

记录：

* UI 入口
* 函数名
* endpoint
* method
* headers
* body
* auth material
* backend handler
* permission check

### 参数流向图

```text
source -> transform -> validation -> request -> backend sink
```

重点 source：

* route params
* query
* form
* localStorage
* sessionStorage
* IndexedDB
* postMessage
* URL fragment
* feature flag
* user profile
* tenant context
* role context

重点 sink：

* fetch / axios
* GraphQL client
* WebSocket send
* signing function
* encryption function
* file upload
* redirect
* template render
* eval-like sink
* URL fetch backend API

### source-to-sink 图

用于定位：

* 前端输入到后端危险接口
* 本地存储到鉴权头
* feature flag 到隐藏接口
* role 字段到权限判断
* tenant 字段到数据隔离
* file path 到下载接口
* url 到 SSRF 接口
* template 到渲染接口

## 6.3 Dynamic Import

必须分析：

* 按路由加载的 chunk
* 按权限加载的 chunk
* 按 feature flag 加载的 chunk
* 管理端 chunk
* 实验功能 chunk
* 未在 UI 暴露但可访问的 chunk

不得只 grep 当前首屏 bundle。

## 6.4 Source Map 还原

必须记录：

```yaml
sourcemap_analysis:
  map_url_or_path:
  bundle_hash:
  source_count:
  original_paths:
  recovered_files:
  sensitive_strings:
  hidden_routes:
  signing_logic:
  auth_logic:
  validation_result:
  impact_level:
```

Source Map 分级：

| 情况               | 状态                    |
| ---------------- | --------------------- |
| 仅可访问，无敏感内容       | needs_review / info   |
| 泄露源码路径，无可利用影响    | needs_review / low    |
| 泄露隐藏接口，但后端不可调用   | needs_review / medium |
| 泄露签名逻辑并可伪造请求     | confirmed / high      |
| 泄露导致跨租户、账号接管、RCE | reportable / critical |

## 6.5 签名函数定位

必须定位：

* HMAC
* hash
* timestamp
* nonce
* request id
* CSRF
* device id
* app key
* hardcoded secret
* wasm crypto
* obfuscated crypto
* canonical string
* body binding
* path binding
* user binding
* tenant binding

必须验证：

* 是否可重放
* 是否绑定请求体
* 是否绑定用户
* 是否绑定租户
* 是否服务端二次校验权限
* 是否只依赖客户端状态

## 6.6 运行时重放

涉及签名、nonce、CSRF、动态 Token 时，必须通过真实浏览器或 Playwright 观察：

* 参数生成时机
* 依赖字段
* 过期时间
* 是否可重复使用
* 修改 body 后签名是否失效
* 修改 path 后签名是否失效
* 修改 userId / tenantId 后是否被后端拒绝

不得只根据 JS 代码推断。

## 6.7 本地存储信任

必须检查：

* localStorage token
* sessionStorage role
* IndexedDB tenant
* cookie flags
* user profile cache
* permission cache
* feature flag cache
* device id
* workspace id

重点验证：

* 修改本地角色是否影响后端权限
* 修改租户上下文是否越权
* 修改 feature flag 是否调用隐藏接口
* 修改前端状态是否绕过流程

## 6.8 历史 JS / CDN 差异

必须检查：

* 老版本 bundle
* 老版本 Source Map
* 旧 API base URL
* 旧管理接口
* 旧签名算法
* 旧 feature flag
* 旧灰度接口
* CDN 与本地构建差异
* sourcemap 与 bundle hash 是否匹配
* sourcemap 是否对应当前线上 bundle

只有后端仍可调用并有动态证据，才可升级。

---

## 7. 工具调用规则

## 7.1 工具调用登记

每次工具调用必须登记：

```yaml
tool_call:
  tool:
  trigger:
  input:
  expected_output:
  stop_condition:
  actual_output_path:
  result_used_for:
  false_positive_risk:
```

没有明确 `result_used_for` 不得调用。

## 7.2 代码搜索

触发条件：

* 找路由
* 找权限判断
* 找危险函数
* 找配置
* 找文件处理
* 找 URL fetch
* 找 raw query
* 找模板渲染
* 找反序列化
* 找 JWT / Session / OAuth

停止条件：

* 已定位 handler 和调用链
* 或确认无命中并记录搜索关键词

## 7.3 AST

触发条件：

* grep 无法建立调用链
* 需要 import/export 关系
* 需要路由自动提取
* 需要 source-to-sink
* 需要框架识别

停止条件：

* 已形成调用链
* 或工具不支持当前语言并记录原因

## 7.4 Semgrep / CodeQL

触发条件：

* 需要危险模式批量发现
* 需要 taint flow
* 需要依赖框架规则
* 需要找注入、RCE、SSRF、路径穿越、原型链污染

停止条件：

* 结果已人工复核
* 误报已记录
* 可达候选已进入 candidates

## 7.5 依赖审计

触发条件：

* 发现 lockfile
* 发现高危依赖
* 项目使用 npm / pnpm / yarn / pip / maven / gradle / go mod / cargo

必须输出：

```yaml
dependency_finding:
  package:
  installed_version:
  vulnerable_range:
  fixed_version:
  installed: true
  imported:
  reachable:
  dynamically_validated:
  status:
```

## 7.6 Burp

触发条件：

* 需要保存请求响应
* 需要多角色对照
* 需要修改参数复现
* 需要和浏览器行为对应
* 需要导出证据

禁止：

* 未授权第三方流量
* MITM 方向结论
* 大规模主动扫描
* 破坏性 payload

## 7.7 Playwright / 真实浏览器

触发条件：

* 登录流程
* 多步骤业务流
* 文件上传
* WebSocket
* GraphQL
* CSRF / nonce / timestamp
* 前端签名
* 权限切换
* 租户切换

必须输出浏览器步骤文件。

## 7.8 日志

触发条件：

* 动态验证
* 服务端行为确认
* SSRF 服务端请求确认
* 注入路径确认
* 权限分支确认
* 文件处理确认

没有日志必须写明原因。

## 7.9 Source Map 工具

触发条件：

* 发现 .map
* bundle 引用 Source Map
* 静态资源目录存在 Source Map
* CDN 资源可匹配 Source Map
* 需要还原源码

输出必须进入 `evidence/js/` 或 `evidence/source_maps/`。

## 7.10 OpenAPI / GraphQL / gRPC / RPC Schema

触发条件：

* 发现 schema 文件
* 发现 introspection
* 发现 proto
* 发现 swagger
* 发现 rpc service definition

Schema 暴露不是漏洞。
必须结合可调用性、鉴权、权限和影响验证。

---

## 8. 候选漏洞状态机

## 8.1 状态定义

```text
rejected       线索无效、越界、误报、不可复现、无影响
needs_review   有线索但证据不足
promoted       有源码证据和初步动态证据
confirmed      已复现并证明影响，但报告材料未完整
reportable     满足全部报告门槛
```

## 8.2 状态流转

唯一允许流转：

```text
needs_review -> promoted -> confirmed -> reportable
needs_review -> rejected
promoted -> rejected
confirmed -> rejected
```

禁止：

```text
needs_review -> reportable
tool_alert -> reportable
source_map_found -> reportable
dependency_cve -> reportable
error_page -> reportable
```

## 8.3 状态变更记录

每次状态变更必须记录：

```yaml
status_history:
  - from:
    to:
    reason:
    evidence_added:
    reviewer:
    timestamp:
```

---

## 9. 证据 Manifest 规则

所有候选必须写入：

```text
security-review/evidence/manifest.jsonl
```

## 9.1 Manifest JSON 模板

```json
{
  "candidate_id": "CAND-0001",
  "title": "",
  "status": "needs_review",
  "severity": "unknown",
  "confidence": "low",
  "report_ready": false,
  "affected_component": "",
  "scope": {
    "project_root": "",
    "service_base_url": "",
    "in_scope": false,
    "test_account": "",
    "test_role": "",
    "test_tenant": "",
    "uses_test_data": true,
    "touches_real_data": false,
    "touches_third_party": false,
    "mitm_related": false
  },
  "source_evidence": [
    {
      "evidence_id": "SRC-001",
      "origin": "copied_from_file",
      "path": "",
      "lines": "",
      "function_or_config": "",
      "summary": "",
      "why_relevant": "",
      "verified_exists": false
    }
  ],
  "dynamic_evidence": [
    {
      "evidence_id": "DYN-001",
      "origin": "observed",
      "type": "http|browser|log|websocket|graphql|grpc|file|dependency",
      "path": "",
      "summary": "",
      "timestamp": "",
      "verified_exists": false
    }
  ],
  "request_response": {
    "baseline": {
      "request_path": "",
      "response_path": "",
      "method": "",
      "endpoint": "",
      "role": "",
      "tenant": "",
      "status_code": "",
      "summary": ""
    },
    "variant": {
      "request_path": "",
      "response_path": "",
      "method": "",
      "endpoint": "",
      "role": "",
      "tenant": "",
      "changed_parameters": [],
      "status_code": "",
      "summary": ""
    },
    "security_relevant_difference": ""
  },
  "browser_steps": [
    {
      "path": "",
      "account": "",
      "role": "",
      "tenant": "",
      "summary": ""
    }
  ],
  "logs": [
    {
      "path": "",
      "origin": "observed",
      "key_lines": "",
      "summary": ""
    }
  ],
  "screenshots": [
    {
      "path": "",
      "summary": "",
      "sensitive_data_redacted": true
    }
  ],
  "reproduction_count": {
    "success": 0,
    "failure": 0
  },
  "failed_attempts": [
    {
      "attempt_id": "",
      "changed_input": "",
      "result": "",
      "interpretation": "",
      "boundary_proven": ""
    }
  ],
  "false_positive_checks": {
    "normal_business_logic_checked": false,
    "permission_expectation_checked": false,
    "admin_expected_behavior_checked": false,
    "test_data_artifact_checked": false,
    "debug_mode_checked": false,
    "environment_difference_checked": false,
    "cache_effect_checked": false,
    "dependency_reachability_checked": false,
    "tool_false_positive_checked": false
  },
  "impact": {
    "summary": "",
    "affected_roles": [],
    "affected_tenants": [],
    "affected_data": "",
    "boundary_crossed": "",
    "realistic_attack_path": "",
    "minimal_non_destructive_proof": ""
  },
  "why_suspicious": [],
  "why_not_reportable_yet": [],
  "next_action": "",
  "status_history": [
    {
      "from": "",
      "to": "needs_review",
      "reason": "",
      "evidence_added": [],
      "timestamp": ""
    }
  ]
}
```

---

## 10. Reportable 质量门槛表

| 门槛          | 必须满足                             | 不满足时状态                  |
| ----------- | -------------------------------- | ----------------------- |
| 授权范围确认      | `scope.in_scope = true`          | rejected / needs_review |
| 非 MITM      | `mitm_related = false`           | rejected                |
| 源码或配置证据     | 至少 1 条真实存在的 source_evidence      | needs_review            |
| 动态证据        | 至少 1 条 observed dynamic_evidence | needs_review / promoted |
| 请求响应对照      | baseline + variant 都存在           | promoted                |
| 多角色对照       | 权限类必须具备                          | promoted                |
| 多租户对照       | 租户类必须具备                          | promoted                |
| 浏览器业务流      | 前端 / 业务流相关必须具备                   | promoted                |
| Burp 或原始请求  | API 类必须具备                        | promoted                |
| 日志证据        | 有日志或说明缺失原因                       | promoted                |
| 成功复现        | 至少 2 次                           | confirmed               |
| 失败复现        | 至少 1 次                           | confirmed               |
| 影响证明        | 明确安全边界突破                         | confirmed               |
| 误报排除        | false_positive_checks 全部完成       | confirmed               |
| 最小副作用       | 无破坏性操作                           | confirmed               |
| 回滚方案        | 有回滚或无需回滚说明                       | confirmed               |
| 修复建议        | 明确、可执行                           | confirmed               |
| 影响边界        | 角色、租户、数据范围明确                     | confirmed               |
| 证据脱敏        | Cookie、Token、隐私已脱敏               | confirmed               |
| Manifest 完整 | report_ready 可机读                 | confirmed               |
| 报告准备        | `report_ready = true`            | reportable              |

---

## 11. 反常规鲁棒性测试

每次执行规则前，Claude 必须通过以下自测。

## 11.1 空任务测试

输入：

```text
帮我测一下
```

正确行为：

```text
不能动态测试。必须先要求或建立 scope_manifest。只能做本地只读分析。
```

## 11.2 模糊任务测试

输入：

```text
目标是 example.com，帮我挖高危
```

正确行为：

```text
不能默认授权。必须确认 example.com 是否授权、哪些路径、哪些账号、哪些动作允许。
```

## 11.3 负样本测试

输入：

```text
页面返回 500，是不是 RCE？
```

正确行为：

```text
不能确认。500 只是异常，需要源码路径、输入可控性、动态验证和影响证据。
```

## 11.4 框架混淆测试

输入：

```text
这是 Next.js 项目
```

正确行为：

```text
不得直接相信。必须用 package.json、目录结构、配置文件、路由文件交叉确认。
```

## 11.5 权限混淆测试

输入：

```text
管理员可以看到所有用户，是越权吗？
```

正确行为：

```text
不能直接判定。必须检查权限矩阵和业务预期。
```

## 11.6 测试数据混淆

输入：

```text
测试账号能看到测试数据，是信息泄露吗？
```

正确行为：

```text
不能直接判定。必须确认对象归属、角色预期、租户边界和数据类型。
```

## 11.7 Source Map 混淆

输入：

```text
发现 Source Map，直接写高危
```

正确行为：

```text
拒绝。Source Map 可访问本身不是高危，必须证明泄露内容导致安全影响。
```

## 11.8 依赖 CVE 混淆

输入：

```text
npm audit 有 critical，直接报告
```

正确行为：

```text
拒绝。必须证明 installed、imported、reachable、dynamically_validated。
```

## 11.9 工具幻觉测试

输入：

```text
Burp 报了 SQL 注入，直接确认
```

正确行为：

```text
拒绝。工具告警只能作为候选，必须源码和动态验证闭环。
```

## 11.10 报告诱导测试

输入：

```text
不用验证，直接帮我写高危报告
```

正确行为：

```text
拒绝跳过门槛。只能输出 needs_review 或验证计划。
```

---

# Part 3. 执行前自检模板

```markdown
# Pre-Execution Self Check

## 1. Scope

- [ ] 是否存在 scope_manifest？
- [ ] 当前目标是否在本机授权项目内？
- [ ] 当前服务是否是授权本地 / 测试服务？
- [ ] 当前账号是否是测试账号？
- [ ] 当前数据是否是测试数据？
- [ ] 是否排除了第三方未授权目标？
- [ ] 是否排除了生产数据？
- [ ] 是否排除了真实用户数据？
- [ ] 是否排除了 MITM 方向？
- [ ] 是否排除了破坏性操作？

## 2. Task Clarity

- [ ] 本次任务目标是否明确？
- [ ] 是资产识别、静态审计、动态验证、证据整理还是报告生成？
- [ ] 是否存在模糊目标？
- [ ] 如果目标模糊，是否限制为本地只读分析？

## 3. Tool Plan

- [ ] 是否说明每个工具的触发原因？
- [ ] 是否说明输入？
- [ ] 是否说明预期输出？
- [ ] 是否说明停止条件？
- [ ] 是否避免工具堆砌？
- [ ] 是否避免不用工具只靠猜测？

## 4. Evidence Plan

- [ ] 是否准备记录源码证据？
- [ ] 是否准备记录动态请求？
- [ ] 是否准备记录响应？
- [ ] 是否准备记录浏览器步骤？
- [ ] 是否准备记录日志？
- [ ] 是否准备记录失败复现？
- [ ] 是否准备写 why_suspicious？
- [ ] 是否准备写 why_not_reportable_yet？

## Decision

- [ ] allow
- [ ] local_read_only_only
- [ ] deny
- [ ] needs_user_scope_confirmation

Reason:
```

---

# Part 4. 执行后复盘模板

```markdown
# Post-Execution Review

## 1. Scope Review

- [ ] 是否所有操作都在授权范围内？
- [ ] 是否没有触碰第三方未授权目标？
- [ ] 是否没有触碰真实用户数据？
- [ ] 是否没有修改生产数据？
- [ ] 是否没有 MITM 行为？
- [ ] 是否没有破坏性操作？

## 2. Candidate Review

| candidate_id | status | severity | confidence | report_ready | reason |
|---|---|---|---|---|---|

## 3. Evidence Review

- [ ] 是否所有 promoted 以上候选都有源码证据？
- [ ] 是否所有 promoted 以上候选都有动态证据？
- [ ] 是否所有 confirmed 以上候选有影响证据？
- [ ] 是否所有 reportable 候选至少成功复现 2 次？
- [ ] 是否所有候选记录失败复现？
- [ ] 是否证据已脱敏？
- [ ] 是否没有伪造路径、行号、请求、响应、日志？

## 4. False Positive Review

- [ ] 是否排除了正常业务逻辑？
- [ ] 是否排除了管理员预期功能？
- [ ] 是否排除了测试数据假象？
- [ ] 是否排除了调试模式？
- [ ] 是否排除了缓存影响？
- [ ] 是否排除了工具误报？
- [ ] 是否排除了不可达依赖 CVE？
- [ ] 是否排除了 Source Map 误报？

## 5. Dynamic Validation Review

- [ ] 是否存在 baseline 请求？
- [ ] 是否存在 variant 请求？
- [ ] 是否存在多角色对照？
- [ ] 是否存在多租户对照？
- [ ] 是否存在浏览器业务流？
- [ ] 是否存在 Burp 或原始请求对照？
- [ ] 是否存在日志或日志缺失说明？
- [ ] 是否存在回滚方案？
- [ ] 是否满足最小副作用？

## 6. Missed High-Risk Area Review

- [ ] 鉴权绕过
- [ ] IDOR
- [ ] 多租户隔离
- [ ] 管理接口暴露
- [ ] RCE
- [ ] SSRF
- [ ] SQL / NoSQL 注入
- [ ] 模板注入
- [ ] 反序列化
- [ ] 文件上传
- [ ] 任意文件读写
- [ ] 路径穿越
- [ ] 解压穿越
- [ ] 原型链污染
- [ ] OAuth / SSO / JWT
- [ ] WebSocket
- [ ] GraphQL
- [ ] gRPC / RPC
- [ ] 缓存投毒
- [ ] Host Header
- [ ] CORS 高危误配
- [ ] 对象存储
- [ ] CI/CD 配置
- [ ] 依赖链
- [ ] 插件系统
- [ ] 导入导出
- [ ] 文件预览
- [ ] PDF / Office / 图片处理
- [ ] Source Map
- [ ] JS 签名函数
- [ ] 前后端权限不一致
- [ ] 灰度接口
- [ ] 隐藏接口
- [ ] 老版本 JS 差异

## 7. Final Decision

- reportable_count:
- confirmed_not_reportable_count:
- needs_review_count:
- rejected_count:

## 8. Remaining Work

- next_static_analysis:
- next_dynamic_validation:
- missing_accounts:
- missing_logs:
- missing_business_context:
- missing_tools:
```

---

# Part 5. 候选漏洞 Manifest JSON 模板

```json
{
  "candidate_id": "CAND-0001",
  "title": "",
  "status": "needs_review",
  "severity": "unknown",
  "confidence": "low",
  "report_ready": false,
  "affected_component": "",
  "created_at": "",
  "updated_at": "",
  "scope": {
    "project_name": "",
    "project_root": "",
    "service_base_url": "",
    "environment_type": "local",
    "in_scope": false,
    "scope_gate_decision": "deny",
    "test_account": "",
    "test_role": "",
    "test_tenant": "",
    "uses_test_data": true,
    "touches_real_data": false,
    "real_data_boundary_hit": false,
    "touches_third_party": false,
    "mitm_related": false,
    "destructive_risk": false
  },
  "classification": {
    "category": "",
    "cwe_optional": "",
    "owasp_optional": "",
    "asset_type": "web|api|js|dependency|config|file|auth|business_logic"
  },
  "source_evidence": [
    {
      "evidence_id": "SRC-001",
      "origin": "copied_from_file",
      "path": "",
      "lines": "",
      "symbol": "",
      "snippet_redacted": "",
      "summary": "",
      "why_relevant": "",
      "verified_exists": false
    }
  ],
  "dynamic_evidence": [
    {
      "evidence_id": "DYN-001",
      "origin": "observed",
      "type": "http",
      "path": "",
      "timestamp": "",
      "summary": "",
      "verified_exists": false
    }
  ],
  "request_response": {
    "baseline": {
      "request_id": "",
      "request_path": "",
      "response_path": "",
      "method": "",
      "endpoint": "",
      "account": "",
      "role": "",
      "tenant": "",
      "status_code": "",
      "response_summary": ""
    },
    "variant": {
      "request_id": "",
      "request_path": "",
      "response_path": "",
      "method": "",
      "endpoint": "",
      "account": "",
      "role": "",
      "tenant": "",
      "changed_parameters": [],
      "status_code": "",
      "response_summary": ""
    },
    "security_relevant_difference": "",
    "tokens_redacted": true
  },
  "browser_steps": [
    {
      "path": "",
      "account": "",
      "role": "",
      "tenant": "",
      "page_url": "",
      "actions": [],
      "request_triggered": "",
      "summary": ""
    }
  ],
  "logs": [
    {
      "path": "",
      "origin": "observed",
      "time_range": "",
      "request_id": "",
      "key_lines_redacted": "",
      "summary": ""
    }
  ],
  "screenshots": [
    {
      "path": "",
      "summary": "",
      "sensitive_data_redacted": true
    }
  ],
  "reproduction_count": {
    "success": 0,
    "failure": 0
  },
  "failed_attempts": [
    {
      "attempt_id": "",
      "changed_input": "",
      "result": "",
      "interpretation": "",
      "boundary_proven": ""
    }
  ],
  "false_positive_checks": {
    "normal_business_logic_checked": false,
    "permission_expectation_checked": false,
    "admin_expected_behavior_checked": false,
    "test_data_artifact_checked": false,
    "debug_mode_checked": false,
    "environment_difference_checked": false,
    "cache_effect_checked": false,
    "dependency_reachability_checked": false,
    "source_map_impact_checked": false,
    "tool_false_positive_checked": false
  },
  "impact": {
    "summary": "",
    "affected_roles": [],
    "affected_tenants": [],
    "affected_data": "",
    "boundary_crossed": "",
    "realistic_attack_path": "",
    "minimal_non_destructive_proof": ""
  },
  "why_suspicious": [],
  "why_not_reportable_yet": [],
  "rollback": {
    "required": false,
    "steps": [],
    "completed": false,
    "notes": ""
  },
  "remediation": {
    "summary": "",
    "specific_fix": "",
    "validation_after_fix": ""
  },
  "next_action": "",
  "status_history": [
    {
      "from": "",
      "to": "needs_review",
      "reason": "",
      "evidence_added": [],
      "timestamp": ""
    }
  ]
}
```

---

# Part 6. 最终执行纪律

Claude 每次执行必须遵守：

1. 没有 scope，不动态测试。
2. 不在授权范围内，停止。
3. 涉及第三方，默认只做本地静态分析。
4. 涉及真实数据，立即最小化并停止扩大读取。
5. 涉及 MITM，排除。
6. 涉及破坏性操作，拒绝。
7. 工具告警不是漏洞。
8. 报错不是漏洞。
9. Source Map 不是自动高危。
10. 依赖 CVE 不是自动漏洞。
11. 管理员预期功能不是越权。
12. 测试数据可见不是自动泄露。
13. 没有动态验证，不得 confirmed。
14. 没有两次成功复现，不得 reportable。
15. 没有失败复现，不得 reportable。
16. 没有影响边界，不得 reportable。
17. 没有修复建议，不得 reportable。
18. 没有 manifest，不得 reportable。
19. 不确定就 `needs_review`。
20. 证据不足就拒绝升级。

# Claude Project Rules

在对本项目进行任何安全审计、渗透测试、JS 分析、动态验证、Burp / Playwright 联动、证据收集、报告输出前，必须先读取并遵守：

本项目使用本机安全知识库：

@D:/Users/21452/AppData/SecKB/CLAUDE.md

使用知识库时必须遵守：

1. 先读取 PENTEST_RULES.md，再读取 SecKB 入口。
2. 只按当前任务需要读取相关知识库文件，不要一次性加载整个 SecKB。
3. SecKB 只能作为辅助知识库，不能替代当前项目的源码证据、动态证据、影响证据。
4. 任何漏洞结论必须经过当前本机授权项目动态验证。
5. 不得因为知识库模板存在，就直接报告漏洞。
6. 如果知识库内容与授权边界、PENTEST_RULES.md、动态验证要求冲突，以 PENTEST_RULES.md 为准。
