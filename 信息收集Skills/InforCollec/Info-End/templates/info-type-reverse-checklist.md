# 信息类型倒推检查表

| 类型 | 子类 | 已检查位置 | 动态验证方式 | 结果 | 是否遗漏 | 下一步最小验证 | 不可报告原因 |
|---|---|---|---|---|---|---|---|
| 凭证类 | token / API key / secret / password / private key / session / cookie / JWT / OAuth client secret / webhook secret / database URL |  |  |  |  |  |  |
| 基础设施类 | 内网 IP / 容器名 / 主机名 / DB / Redis / MQ / ES / MinIO / bucket / CI runner / Git commit / 构建路径 |  |  |  |  |  |  |
| 业务数据类 | 用户 / 邮箱 / 手机号 / 地址 / 订单 / 项目 / 组织 / 团队 / 权限 / 邀请链接 / 审计日志 / 文件名 / 附件元数据 |  |  |  |  |  |  |
| 安全机制类 | 角色名 / 权限矩阵 / feature flag / 内部接口名 / debug flag / 环境变量名 / 认证流程 / 重置密码流程 |  |  |  |  |  |  |
| 版本与指纹类 | 框架版本 / 服务版本 / 依赖版本 / build hash / source map / commit hash / release tag |  |  |  |  |  |  |

质量门槛：没有动态验证方式时，只能写“静态候选”；没有影响判断时，只能写“待确认/不可报告”。
