# File Boundary Verify

## 适用范围

本 Skill 用于当前本地授权开源项目的文件处理安全动态验证。它把 TXT 中的文件上传、文件写入、路径穿越、危险文件解析、文件读取、附件下载绕过、预览接口读取、导入导出链路读取、压缩包解压写入、对象存储 key 映射错误，转成可执行、可复现、可回滚、无破坏的验证流程。

适用目标必须同时满足：项目位于本机或授权测试环境；测试者有明确授权；测试数据为本 Skill 创建的 marker 文件；服务地址为本地或授权内网测试地址；所有结论都有证据等级。

## 不适用范围

不得用于未授权目标、公网敏感地址、第三方生产系统、真实用户数据、真实系统敏感文件或凭据相关内容。

不得读取系统账户文件、SSH key、环境变量、云元数据、真实用户文件、数据库配置文件。任意文件读取验证只能读取本 Skill 创建的 `allowed-read-marker.txt` 与 `blocked-read-marker.txt`。

不得上传 webshell、木马、反弹 shell、持久化脚本、破坏性 payload。上传样本只能是无害 marker 内容。不得执行 DoS、DDoS、压缩炸弹、超大文件耗尽磁盘、耗尽 CPU、破坏数据库或破坏业务运行的测试。

MITM、中间人攻击、凭据窃取、生产数据读取不属于本 Skill 范围。

## 输入要求

调用前必须提供或在项目中确认以下输入。缺失输入时，按“失败处理”降级执行，不得伪造结果。

| 输入项 | 必填 | 含义 | 缺失处理 |
|---|---:|---|---|
| `project_root` | 是 | 本地授权项目根目录 | 停止动态验证，只输出缺失项与待执行计划 |
| `local_base_url` | 是 | 本地运行服务地址 | 不执行请求，只输出请求矩阵 |
| `auth_contexts` | 否 | 未登录、普通用户 A、普通用户 B、管理员、只读角色、低权限/禁用角色 | 缺失角色对应项标记 `not tested` |
| `tenant_contexts` | 否 | 租户 A、租户 B 或项目等效隔离维度 | 缺失租户矩阵标记 `not tested` |
| `test_marker_root` | 是 | marker 根目录，格式建议 `security-markers/file-boundary-{uuid}/` | 无法创建则停止读取/写入验证 |
| `evidence_output_dir` | 是 | 请求、响应、日志摘要、文件系统状态、manifest 输出目录 | 缺失则只输出计划，不输出 confirmed |
| `allowed_operations` | 是 | 允许的动作：upload、download、preview、read-marker、write-marker、import、export、archive-extract、object-key-map | 未列入动作不得执行 |
| `rollback_policy` | 是 | 删除 marker 目录、测试上传记录、导入任务、导出缓存的方式 | 缺失则禁止写入类测试 |

## 输出要求

最终报告必须使用 `templates/output-template.md`。报告章节固定为：

1. 项目文件处理攻击面总览。
2. 上传入口清单。
3. 读取入口清单。
4. 文件流转图。
5. 高风险候选点列表。
6. 动态验证计划。
7. 已执行验证结果。
8. confirmed 漏洞。
9. candidate 漏洞。
10. false positive。
11. 未覆盖原因。
12. 下一轮必须补测的偏门路径。
13. 修复建议。
14. 回归测试用例。
15. 反向审判降级结果。
16. evidence manifest 索引。

结论状态只能使用：`confirmed`、`candidate`、`false positive`、`blocked`、`not tested`、`not applicable`。

`confirmed` 必须同时具备：请求证据、响应证据、marker 证明、文件系统前后状态、日志证据或日志不可用说明、正向测试、负向测试、blocked 测试、权限矩阵或明确不适用原因、租户矩阵或明确不适用原因、影响范围、误报排除、非静态猜测证明、可复现步骤、回滚状态。任一缺失必须降级。

## 原文复刻规则

以下规则直接来自 TXT，执行时不得弱化：

1. 只允许测试当前本地授权项目。
2. 禁止访问公网敏感地址。
3. 禁止读取真实系统敏感文件。
4. 任意读取只能读取自建 marker 文件。
5. 任意写入只能写入自建临时测试目录。
6. 文件上传只能使用无害 marker 文件。
7. 禁止 DoS、DDoS、压缩炸弹、超大文件、耗尽 CPU/磁盘、破坏数据库、破坏业务运行。
8. 忽略 MITM 方向。
9. 没有动态证据只能标记 `candidate`，不能标记 `confirmed`。
10. 每个 `confirmed` 必须有可复现请求、响应、日志、文件系统前后状态、marker 证明、失败对照组。
11. 必须先理解项目：语言、框架、路由、上传中间件、存储方式、对象存储封装、下载、预览、导入导出、后台管理、附件、头像、模板、插件、主题、日志、报表。
12. 必须识别文件处理依赖：multipart 解析、图片处理、PDF 预览、Office 解析、压缩包处理、对象存储 SDK、路径处理库、模板引擎、静态资源服务、反序列化导入功能。
13. 必须画出文件流转图：入口参数 → 服务端解析 → 文件名处理 → 路径拼接 → 权限判断 → 存储位置 → 后续访问方式 → 预览 / 下载 / 解析 / 转换 / 删除链路。
14. 必须找出用户可控字段：filename、path、key、url、file、dir、folder、name、type、contentType、mime、extension、resource、template、theme、plugin、importId、attachmentId、objectKey、downloadUrl、previewUrl、avatar、logo、backup、restore、locale、lang、report、export。
15. 必须找出前端未暴露但后端可能接受的隐藏参数：multipart 额外字段、JSON body、query、header、GraphQL variables、WebSocket message。
16. 必须建立 marker 目录：allowed、blocked、upload、download，并创建 `allowed-read-marker.txt`、`blocked-read-marker.txt`、`upload-write-marker.txt`。
17. 必须记录每一步文件系统前后状态，并保证可回滚。
18. 上传验证必须覆盖基线、扩展名、MIME、魔数、大小写、双扩展名、空格、点号、尾随点、Unicode 正规化、URL 编码、双重编码、路径分隔符变体、filename 路径边界、multipart 额外字段、分片/断点续传、头像、附件、富文本图片、插件、主题、模板、导入、备份恢复、上传后访问链路、覆盖、目录逃逸。
19. 读取验证必须覆盖下载、预览、缩略图、PDF/Office/图片转换、附件、导出、日志、备份、模板、语言包、主题、静态资源、对象存储 key 到本地路径映射、ID 与 path/key/name 冲突、隐藏参数、GraphQL、WebSocket、RPC。
20. 路径验证必须覆盖 join/resolve/normalize、解码顺序、拼接顺序、字符串前缀、真实规范路径、软链接、对象 key、Windows/Linux 分隔符差异、Unicode、编码、尾随点、尾随空格、重复分隔符、zip slip、tar slip、archive extraction、临时/缓存/转换/缩略图/导出文件二次读取。
21. 权限矩阵必须覆盖未登录、普通用户 A、普通用户 B、不同租户用户、管理员、只读角色、禁用/低权限角色、文件拥有者、非文件拥有者。
22. 反向审判必须逐条复核 confirmed、candidate、false positive；缺证据必须降级。

## 工程化补强规则

以下内容是为了让 Skill 可执行而新增，不得写成 TXT 原文：

1. 使用验证编号 `FBV-YYYYMMDD-NNN`。
2. 每个入口必须进入动态验证矩阵。
3. 请求样本必须脱敏认证信息。
4. 响应只记录状态码、关键字段、marker 命中和安全判断。
5. 文件系统状态使用 before / after / rollback 三段记录。
6. 日志证据记录来源、时间窗口、关键行摘要；无日志访问权限写 `not available`。
7. 依赖专项必须来自项目依赖文件、锁文件或代码引用，不得凭语言栈推断。
8. 未执行请求的发现统一为 `candidate` 或 `not tested`。
9. marker 根目录创建失败时停止读取/写入类验证。
10. 回滚确认失败时报告标记 `rollback incomplete`。

## 核心工作流

```text
读取输入与授权边界
  → 项目文件处理面识别
  → marker 安全测试环境建立
  → 上传入口动态验证
  → 读取入口动态验证
  → 路径规范化与边界验证
  → 角色/租户/权限矩阵验证
  → 依赖与框架专项核对
  → evidence manifest 汇总
  → 初步结论分级
  → 反向审判复核
  → 降级、补证或标记未覆盖
  → 最终报告
```

## 分阶段执行步骤

### 阶段 1：确认输入与边界

1. 检查 `project_root` 是否存在且属于授权本地项目。
2. 检查 `local_base_url` 是否为本地或授权测试服务。
3. 列出可用角色与租户；缺失项标记 `not tested`。
4. 确认 `allowed_operations` 未包含破坏性动作。
5. 输出“可执行动作”和“禁止动作”。

失败处理：任一授权边界不明确时，不执行动态请求，不输出 `confirmed`。

### 阶段 2：项目文件处理面识别

从路由、controller、service、middleware、guard/policy、DTO/schema、storage adapter、file utility、background job、cron task、import/export module、admin module、test-only route、deprecated route、static serving config、Nginx/Apache/reverse proxy config、Docker volume、environment config、CI/test fixture、前端 JS、sourcemap 中识别文件处理入口。

输出字段：`endpoint`、`method`、`handler/source`、`operation`、`parameters`、`auth required`、`tenant scoped`、`storage target`、`follow-up access`、`status`、`evidence`。

失败处理：只在代码中发现、未执行请求的条目状态为 `candidate`。

### 阶段 3：建立 marker 环境

创建：

```text
security-markers/file-boundary-{uuid}/
  allowed/allowed-read-marker.txt
  blocked/blocked-read-marker.txt
  upload/upload-write-marker.txt
  download/
```

记录每个 marker 的规范绝对路径、内容摘要、存在状态。读取测试只能使用 allowed/blocked marker；写入测试只能写入 marker 根目录内；上传测试只能使用无害 marker 内容。

失败处理：marker 创建失败时，停止读取、写入、上传落点类验证。

### 阶段 4：上传入口动态验证

对每个上传入口执行以下验证组：

| 验证组 | 动作 | 必填证据 | 通过标准 | 失败处理 |
|---|---|---|---|---|
| baseline | 正常上传 marker | 请求、响应、落点、回滚 | 仅落入预期目录 | 失败则标记 `baseline failed` |
| extension | 非允许扩展名、大小写、双扩展名 | 请求、响应、保存名 | 服务端拒绝或安全重命名 | 未执行为 `not tested` |
| content | MIME 与扩展名不一致、魔数不一致 | 请求、响应、识别结果 | 服务端不只信任 `Content-Type` | 证据不足为 `candidate` |
| filename | 空格、点号、尾随点、Unicode、编码、路径分隔符 | 请求、响应、规范落点 | 不越出上传根目录 | 无落点不得 confirmed |
| hidden fields | dir、folder、path、name、key、type、module | 请求、响应、保存路径 | 客户端字段不能控制越界路径 | 无请求不得 confirmed |
| chunk | chunk / resumable / 合并 | 分片请求、合并请求、落点 | 合并阶段重新校验扩展名、路径、权限 | 无功能为 `not applicable` |
| atypical | 头像、附件、富文本图片、插件、主题、模板、导入、备份恢复 | endpoint 证据 | 每个入口独立验证 | 未覆盖写原因 |
| second access | 静态资源、下载、预览、转换访问上传文件 | 访问请求、响应 | 不产生越权访问 | 无链路为 `not applicable` |
| overwrite | 覆盖 marker 文件 | before/after | 不覆盖 marker 外文件 | 禁止真实文件覆盖 |
| escape | 上传目录逃逸 | before/after、realpath | 不越出预期根目录 | 无落点证明不得 confirmed |

### 阶段 5：读取入口动态验证

对每个读取候选点构造：

1. 正常读取 allowed marker。
2. 越界读取 blocked marker。
3. 被拦截的负例请求。
4. 不存在文件请求。
5. 编码变体请求。
6. 不同角色 / 租户请求。
7. 直接 ID 与隐藏 path 参数冲突请求。
8. 多参数优先级请求，例如 id 合法但 path 指向 blocked marker。

覆盖对象：下载、预览、缩略图、PDF/Office/图片转换、附件、导出、日志、备份、模板、语言包、主题、静态资源、对象存储 key、本地路径映射、GraphQL、WebSocket、RPC。

失败处理：缺少 marker 命中证据时，不得标记任意文件读取 `confirmed`。

### 阶段 6：路径规范化与边界验证

对每个路径相关入口记录原始参数、解码后参数、拼接路径、规范路径、realpath、根目录边界、落点或读取目标。检查 join/resolve/normalize、解码顺序、拼接顺序、字符串前缀、软链接、对象 key、Windows/Linux 分隔符、Unicode、编码、尾随点、尾随空格、重复分隔符、小型无害 zip/tar 解压、临时/缓存/转换/缩略图/导出文件二次读取。

失败处理：只有代码迹象但无请求、响应、marker 或落点证据时，状态为 `candidate`。

### 阶段 7：权限与租户矩阵

每个上传/读取问题都必须执行或标记以下身份：未登录、普通用户 A、普通用户 B、不同租户用户、管理员、只读角色、禁用/低权限角色、文件拥有者、非文件拥有者。

必须验证：A 上传的文件 B 是否能读；租户 A 文件租户 B 是否能读；普通用户是否能通过 path/key/id 读取管理员 marker；删除、预览、下载权限是否一致；前端隐藏按钮是否对应后端校验。

失败处理：缺失权限或租户矩阵时，不得确认越权类问题。

### 阶段 8：依赖与框架专项

根据实际项目选择，不得把未发现的框架写成已检查：

| 技术栈 | 必查对象 |
|---|---|
| Node.js / Express / Nest / Next | multer、busboy、formidable、express-fileupload、static middleware、sendFile、res.download、path.join、path.resolve、Next API route、public/static、server action、image optimizer |
| Python / Django / Flask / FastAPI | FileField、MEDIA_ROOT、send_file、send_from_directory、UploadFile、aiofiles、werkzeug secure_filename、图片处理、PDF 预览、模板读取、静态资源映射 |
| Java / Spring | MultipartFile、ResourceHttpRequestHandler、Files.copy、Paths.get、ClassPathResource、FileSystemResource、download controller、静态资源 handler、模板和导入导出 |
| PHP / Laravel | Storage facade、public disk、local disk、move_uploaded_file、response()->download、symlink public storage、路由参数、隐藏 path 参数、文件名过滤 |
| Go | multipart.FileHeader、http.ServeFile、filepath.Clean、filepath.Join、os.Open、tar/zip 解压、路径清洗、根目录边界检查 |
| Ruby / Rails | ActiveStorage、send_file、send_data、public/uploads、导入导出、附件预览 |

依赖风险必须回答 multipart、路径拼接、压缩包解压、图片/PDF/Office 解析、静态文件服务、对象存储、导入导出、历史路径类风险、项目封装错误、wrapper 是否绕过官方安全用法。

### 阶段 9：证据 manifest 与结论分级

每个 `confirmed` 使用以下字段：

```yaml
id: FBV-YYYYMMDD-NNN
status: confirmed
vulnerability_type: "file-read | file-write | path-boundary | upload-bypass | archive-extraction | object-key-mapping | authorization-bypass"
endpoint: "METHOD /path"
auth_role: "role name"
tenant: "tenant id or none"
request_sample: "redacted minimal request"
response_summary: "status code and key fields"
marker_proof: "marker filename and content digest"
filesystem_before: "path, exists, digest"
filesystem_after: "path, exists, digest"
log_evidence: "log source and summary, or not available"
positive_test: "baseline request result"
negative_test: "expected rejection result"
blocked_test: "blocked marker result"
impact_scope: "boundary crossed"
not_false_positive_reason: "why expected behavior does not explain this"
not_static_guess_reason: "which dynamic evidence proves it"
minimal_fix: "specific server-side fix"
regression_test: "repeatable test case"
rollback_status: "complete | incomplete | not required"
```

### 阶段 10：反向审判复核

使用 `checklists/final-review.md` 逐条审判全部 `confirmed` / `candidate` / `false positive`。凡缺少请求、响应、marker、文件系统前后状态、对照组、权限矩阵、租户矩阵、影响范围、可复现步骤的，降级。

## 质量门禁

最终报告前必须通过 `checklists/quality-gate.md`。硬性 gate：

- [ ] 未读取 TXT 对应规则，不得生成最终 Skill 或最终报告。
- [ ] 未建立 TXT 到 Skill 映射，不得通过。
- [ ] 未区分原文复刻和工程化补强，不得通过。
- [ ] 未覆盖关键章节，不得通过。
- [ ] 未提供模板、checklist、examples、tests，不得通过。
- [ ] 未定义失败处理，不得通过。
- [ ] 文件命名无法对应 TXT 核心主题，不得通过。
- [ ] Skill 数量无理由过多，不得通过。
- [ ] 空壳文件存在，不得通过。
- [ ] 输出不可追溯 TXT，不得通过。
- [ ] confirmed 缺少任一核心证据，不得通过。

## 幻觉控制

1. 不得把静态代码迹象写成动态确认。
2. 不得把未执行请求写成已执行。
3. 不得把 403/404 直接写成安全，必须记录请求、响应和预期行为。
4. 不得把前端限制写成后端安全。
5. 不得忽略异步任务、转换任务、缩略图任务、导入任务、后台 worker。
6. 不得忽略对象存储、缓存目录、临时目录。
7. 不得忽略二次访问链路。
8. 不得把工程化补强写成 TXT 原文。
9. 不得输出真实系统敏感文件路径读取结果。
10. 不得使用夸张、保证式、无证据结论。

## 失败处理

| 失败场景 | 处理 |
|---|---|
| `project_root` 不存在 | 停止动态验证，输出缺失输入 |
| 服务未启动 | 输出待执行矩阵，不输出 confirmed |
| marker 创建失败 | 停止读取/写入/上传落点验证 |
| 缺少角色凭据 | 对应角色标记 `not tested` |
| 缺少租户环境 | 租户矩阵标记 `not tested`，不得确认跨租户问题 |
| 日志不可用 | 写 `not available`，不得伪造日志 |
| 请求工具不可用 | 输出请求样本和待执行状态 |
| 文件系统状态不可读 | 写 `candidate`，不得 confirmed 写入/读取 |
| 回滚失败 | 标记 `rollback incomplete` 并列出残留测试项 |
| 发现真实敏感路径测试企图 | 立即停止该测试，改用 marker 路径 |

## 输出格式

使用 `templates/output-template.md`。所有矩阵字段必须填写；未知写 `unknown`，未执行写 `not tested`，不适用写 `not applicable`，不可用写 `not available`。不得留空表达结论。

## 自检清单

- [ ] 是否只保留 1 个主 Skill。
- [ ] 是否无空壳目录、空壳文件。
- [ ] 是否覆盖 TXT 两部分：动态验证与反向审判。
- [ ] 是否保留原文关键术语、字段、入口、矩阵、降级规则。
- [ ] 是否所有 `confirmed` 都有动态证据。
- [ ] 是否所有读取/写入都限定 marker。
- [ ] 是否所有新增字段都标记为工程化补强。
- [ ] 是否模板可直接填写。
- [ ] 是否 checklist 可验收。
- [ ] 是否 examples 贴近文件处理动态验证主题。
- [ ] 是否 tests 能发现漏复刻、幻觉扩展、空壳文件、命名失败。

## TXT 到 Skill 映射说明

本 Skill 的规则主体来自 TXT。`原文复刻规则` 保存 TXT 的边界、流程、验证对象、禁止事项、输出要求和反向审判规则；`工程化补强规则` 保存为了执行而新增的编号、矩阵、证据字段、失败处理和报告约束。详细映射见 README 的“TXT 复刻一致性映射表”。
