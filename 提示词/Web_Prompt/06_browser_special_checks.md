# 06 浏览器专项验证

请对 Web 页面和浏览器行为执行专项验证。

## 一、页面路由枚举

- 从首页开始抓取所有可见链接。
- 登录前记录可见入口。
- 登录后记录可见入口。
- 不同角色分别记录可见入口。
- 不同租户分别记录可见入口。
- 比较前端路由与 network 请求是否一致。
- 发现隐藏路由时进行非破坏性访问验证。
- 发现 admin、debug、internal、legacy、example、health、metrics 路径时进行权限验证。

输出：

- route
- visible_to
- direct_access_result
- network_requests
- evidence
- classification

## 二、Network 请求分析

- 记录每个页面触发的 API 请求。
- 记录 method、URL、status、request params、response summary。
- 找出前端没有显示但 JS bundle 中存在的接口。
- 对关键接口执行角色、租户、对象归属对照。
- 对关键参数执行输入变体测试。
- 对 export、download、preview、search、report 做权限一致性验证。

输出：

- request_id
- page_url
- request_method
- request_url
- actor
- params
- response_summary
- variant_test
- evidence
- classification

## 三、前端状态与后端信任边界

- 检查前端是否传入 role、tenant、owner、status、permission、scope。
- 检查隐藏字段、disabled 字段、只读字段是否可影响提交。
- 检查 localStorage、sessionStorage、IndexedDB 是否保存权限、角色、token、租户、对象信息。
- 检查这些前端状态是否会影响后端结果。
- 检查页面切换角色、租户、账号后是否复用旧状态。

输出：

- state_source
- field
- actor
- modified_value
- expected_result
- actual_result
- evidence
- classification

## 四、Cookie、Session、CORS、CSRF

- 检查 Cookie 属性。
- 检查登录前、登录后、退出登录后的 Cookie 变化。
- 检查跨角色、跨租户 Cookie 行为。
- 检查状态变更请求是否有 CSRF 保护。
- 检查 CORS 是否符合预期来源边界。
- 检查 session 是否和用户、角色、租户正确绑定。
- 检查退出登录后旧页面、旧请求、旧缓存是否仍可访问敏感数据。

输出：

- area
- request_or_page
- actor
- expected_result
- actual_result
- evidence
- classification

## 五、静态资源和构建产物

- 检查 JS bundle 是否包含隐藏接口、默认配置、测试数据、内部路径、debug flag。
- 检查 sourcemap 是否可访问。
- 检查 manifest、service worker、asset cache。
- 检查 robots、sitemap、well-known、health、metrics、debug 等路径。
- 检查静态资源是否暴露环境信息、示例数据、日志或内部路径。

输出：

- asset_url
- asset_type
- exposed_information_summary
- impact
- evidence
- classification

## 六、页面缓存和离线行为

- 检查浏览器后退是否显示已退出用户的敏感页面。
- 检查 service worker 是否缓存认证响应。
- 检查页面缓存是否跨用户或跨租户复用。
- 检查 export、preview、download 是否被浏览器或服务端缓存错误复用。
- 检查多标签页切换账号、角色、租户后的页面状态。

输出：

- cache_area
- actor_sequence
- expected_result
- actual_result
- evidence
- classification

## 七、错误信息和异常路径

- 对关键页面和接口输入无效参数。
- 记录错误页面、toast、modal、console、network response。
- 检查是否泄露路径、SQL、stack、token、内部接口、配置、依赖版本。
- 检查异常流程是否造成状态不一致。

输出：

- page_or_request
- invalid_input
- error_surface
- exposed_information_summary
- evidence
- classification
