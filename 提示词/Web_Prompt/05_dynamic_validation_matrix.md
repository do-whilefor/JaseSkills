# 05 Web 动态验证矩阵

对每个高价值疑点，按以下矩阵验证。

A. 角色矩阵：

- anonymous
- user_low
- user_normal
- user_admin
- tenant_a_user
- tenant_b_user
- tenant_a_admin
- tenant_b_admin

B. 页面矩阵：

- 登录前页面
- 登录后页面
- 普通用户页面
- 管理页面
- 租户 A 页面
- 租户 B 页面
- 列表页
- 详情页
- 搜索页
- 报表页
- 上传页
- 预览页
- 下载页
- 导出页
- 设置页
- 权限管理页
- 邀请页
- 重置页
- 验证页
- 错误页

C. 对象矩阵：

- 自己的对象
- 他人的对象
- 同租户对象
- 跨租户对象
- archived 对象
- disabled 对象
- pending 对象
- soft_deleted 对象

D. 参数变体：

- object_id
- user_id
- owner_id
- role_id
- tenant_id
- org_id
- workspace_id
- project_id
- status
- is_admin
- permissions
- scope
- visibility
- amount
- quota
- limit
- callback_url
- redirect_url
- return_url
- next
- file_path
- query_filter
- sort
- pagination
- include
- fields
- expand

E. 编码和解析变体：

- JSON
- form
- multipart
- text
- XML
- YAML
- query string
- duplicate params
- array params
- nested params
- null
- empty string
- empty array
- empty object
- boolean string
- number string
- large integer
- negative number
- case variation
- path encoding
- double slash
- dot segment
- trailing slash
- method override

F. Web 行为证据：

- 页面是否显示不应显示的数据
- 页面是否允许不应允许的操作
- 按钮或菜单是否仅前端隐藏
- 路由是否可直接访问
- network 请求是否成功
- 响应码差异
- 响应体差异
- 控制台错误
- Cookie 变化
- localStorage 变化
- sessionStorage 变化
- IndexedDB 变化
- service worker 缓存
- cache storage 变化
- 浏览器截图
- browser trace

G. 服务端反馈证据：

- 服务端日志变化
- 数据库变化
- 文件 marker
- local callback 命中
- mock service 命中
- WebSocket message 差异
- GraphQL field 差异

每个测试必须输出：

- test_id
- hypothesis
- precondition
- actor
- page_url
- browser_action
- network_request
- target_object
- modified_parameters
- expected_secure_result
- actual_result
- evidence
- conclusion
- classification
