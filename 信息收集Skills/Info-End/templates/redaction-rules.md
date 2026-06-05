# 敏感信息脱敏规则

## 总原则

不得输出完整密钥、完整 token、完整 cookie、完整私钥、完整密码、完整连接串、完整隐私数据。只输出脱敏样本、长度、类型、上下文、文件/接口位置、hash 指纹和影响判断。

## 常见格式

| 类型 | 原始内容处理方式 | 输出示例 |
|---|---|---|
| API Key | 保留前缀和末尾 4 位 | sk_live_****abcd |
| JWT | 三段均脱敏 | eyJ****.****.****xyz |
| DB URL | 密码替换为 **** | mysql://user:****@host:3306/db |
| Cookie | 值脱敏，记录长度和 hash | session=****abcd; 长度：64; SHA256: xxx |
| Private Key | 不输出正文 | 类型：Private Key; 长度：xx; SHA256: xxx |
| OAuth Secret | 前后脱敏 | oauth_****wxyz |
| 邮箱 | 局部脱敏 | a***@example.com |
| 手机号 | 局部脱敏 | 138****1234 |

## 报告中必须包含

- 类型
- 上下文
- 位置
- 长度
- SHA256
- 脱敏样本
- 是否运行态可访问
- 是否非预期角色可见
