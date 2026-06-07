# Quality Gate

任何 `confirmed` 缺少证据时，必须降级。任何 gate 无法确认时，必须写入未覆盖原因。

## A. 授权与边界

- [ ] 已确认 `project_root` 是本地授权项目。
- [ ] 已确认 `local_base_url` 指向本机或授权测试环境。
- [ ] 未访问公网敏感地址。
- [ ] 未读取真实系统敏感文件。
- [ ] 读取目标仅限自建 marker 文件。
- [ ] 写入目标仅限自建 marker 测试目录。
- [ ] 上传样本仅为无害 marker 内容。
- [ ] 未上传 webshell、木马、反弹 shell、持久化脚本、破坏性 payload。
- [ ] 未执行 DoS、DDoS、压缩炸弹、超大文件、耗尽 CPU/磁盘、破坏数据库测试。
- [ ] MITM 已排除在范围外。

## B. Skill 工程门禁

- [ ] 只保留 1 个主 Skill。
- [ ] 未创建空壳 Skill。
- [ ] 未创建无内容目录。
- [ ] 文件夹名 `file-boundary-verify` 简洁且对应 TXT 核心主题。
- [ ] 文件名均为小写英文短横线或标准文件名。
- [ ] 不存在 best、final、new、advanced、ultimate、skill-only 等空泛命名。
- [ ] 已区分原文复刻和工程化补强。
- [ ] 已建立 TXT 到 Skill 映射。
- [ ] 模板、checklist、examples、tests 均存在且有实际字段。

## C. Marker 环境

- [ ] 已创建唯一 marker 根目录 `security-markers/file-boundary-{uuid}/`。
- [ ] 已创建 `allowed/allowed-read-marker.txt`。
- [ ] 已创建 `blocked/blocked-read-marker.txt`。
- [ ] 已创建 `upload/upload-write-marker.txt`。
- [ ] 已创建或确认 `download/`。
- [ ] 已记录 marker 目录 before 状态。
- [ ] 已记录 marker 文件内容摘要。
- [ ] 已确认所有读取目标仅限 allowed/blocked marker。
- [ ] 已确认所有写入目标仅限 marker 测试目录。
- [ ] 已记录 rollback 状态。

## D. 项目理解

- [ ] 已识别编程语言与框架。
- [ ] 已识别路由结构。
- [ ] 已识别上传中间件。
- [ ] 已识别文件存储方式。
- [ ] 已识别对象存储封装或确认不存在。
- [ ] 已识别下载接口。
- [ ] 已识别预览接口。
- [ ] 已识别导入导出接口。
- [ ] 已识别后台管理接口。
- [ ] 已识别附件、头像、模板、插件、主题、日志、报表相关接口。
- [ ] 已识别用户可控字段：filename、path、key、url、file、dir、folder、name、type、contentType、mime、extension、resource、template、theme、plugin、importId、attachmentId、objectKey、downloadUrl、previewUrl、avatar、logo、backup、restore、locale、lang、report、export。
- [ ] 已检查隐藏参数：multipart 额外字段、JSON body、query、header、GraphQL variables、WebSocket message。
- [ ] 已输出文件流转图。

## E. 上传验证

- [ ] 每个上传入口均有 baseline 正常上传结果或未覆盖原因。
- [ ] 已测试非允许扩展名。
- [ ] 已测试 MIME 与扩展名不一致。
- [ ] 已测试文件魔数与扩展名不一致。
- [ ] 已测试扩展名大小写。
- [ ] 已测试双扩展名。
- [ ] 已测试空格、点号、尾随点、Unicode 正规化、URL 编码、双重编码、路径分隔符变体。
- [ ] 已测试 filename 中路径边界，且只指向 marker 临时目录。
- [ ] 已测试 multipart 额外字段：dir、folder、path、name、key、type、module。
- [ ] 已测试分片或断点续传；若不存在，已写 `not applicable`。
- [ ] 已测试头像、附件、富文本图片、插件、主题、模板、导入、备份恢复等非典型上传点或说明未覆盖原因。
- [ ] 已测试上传后访问链路：静态资源、下载、预览、转换。
- [ ] 已测试是否能覆盖 marker 文件，且未覆盖真实文件。
- [ ] 已记录上传落点、规范路径和是否越界。

## F. 读取验证

- [ ] 每个读取入口均测试 allowed marker 正常读取或说明原因。
- [ ] 每个读取入口均测试 blocked marker 越界读取或说明原因。
- [ ] 已构造被拦截的负例请求。
- [ ] 已构造不存在文件请求。
- [ ] 已构造编码变体请求。
- [ ] 已执行不同角色 / 租户请求或标记 `not tested`。
- [ ] 已测试直接 ID 与隐藏 path 参数冲突。
- [ ] 已测试多参数优先级，例如 id 合法但 path 指向 blocked marker。
- [ ] 已覆盖下载、预览、缩略图、转换、附件、导出、日志、备份、模板、语言包、主题、静态资源、对象存储 key、本地路径映射、GraphQL、WebSocket、RPC 或说明未覆盖原因。

## G. 路径与二次链路

- [ ] 已检查 path.join / resolve / normalize 用法。
- [ ] 已检查先校验后解码风险。
- [ ] 已检查先拼接后校验风险。
- [ ] 已检查字符串前缀校验风险。
- [ ] 已检查真实规范路径 realpath 边界。
- [ ] 已检查软链接逃逸；若不可测，已说明。
- [ ] 已检查对象 key 是否被当作文件路径。
- [ ] 已检查 Windows 与 Linux 路径分隔符差异。
- [ ] 已检查 Unicode、URL 编码、尾随点、尾随空格、重复分隔符。
- [ ] 已检查 zip slip / tar slip / archive extraction，且只使用小型无害 marker 压缩包。
- [ ] 已检查临时文件、缓存文件、转换文件、缩略图文件、导出文件的二次读取。

## H. 权限与租户矩阵

- [ ] 已测试未登录用户或标记 `not tested`。
- [ ] 已测试普通用户 A。
- [ ] 已测试普通用户 B。
- [ ] 已测试不同租户用户或标记 `not tested`。
- [ ] 已测试管理员。
- [ ] 已测试只读角色。
- [ ] 已测试禁用/低权限角色。
- [ ] 已测试文件拥有者。
- [ ] 已测试非文件拥有者。
- [ ] 已验证 A 上传的文件 B 是否能读。
- [ ] 已验证租户 A 的文件租户 B 是否能读。
- [ ] 已验证普通用户是否能通过 path/key/id 读取管理员 marker。
- [ ] 已验证删除、预览、下载权限是否一致。
- [ ] 已验证是否只隐藏前端按钮而后端未校验。

## I. 依赖与框架专项

- [ ] 已基于实际依赖识别 multipart 解析库。
- [ ] 已基于实际代码识别路径拼接库。
- [ ] 已识别压缩包解压依赖。
- [ ] 已识别图片、PDF、Office 解析依赖。
- [ ] 已识别静态文件服务组件。
- [ ] 已识别对象存储 SDK 或确认不存在。
- [ ] 已识别导入导出相关依赖。
- [ ] 已记录依赖历史路径类风险或确认无直接相关证据。
- [ ] 已检查项目 wrapper 是否绕过官方安全用法。

## J. 结论分级

- [ ] 没有请求证据的条目未标记 confirmed。
- [ ] 没有响应证据的条目未标记 confirmed。
- [ ] 没有 marker 证据的读取/写入条目未标记 confirmed。
- [ ] 没有文件系统前后状态的写入/落点条目未标记 confirmed。
- [ ] 没有正向、负向、blocked 对照的条目未标记 confirmed。
- [ ] 没有权限矩阵的越权条目未标记 confirmed。
- [ ] 没有租户矩阵的跨租户条目未标记 confirmed。
- [ ] 没有说明为什么不是预期功能的条目未标记 confirmed。
- [ ] 没有影响范围的条目未标记 confirmed。
- [ ] 没有可复现步骤的条目未标记 confirmed。
