# Blackboard

> 只记录已测部分、结果、证据和下一步。每轮结束更新。

```yaml
scope:
  targets: []
  identities: []
  note: ""

tested:
  # - id: T001
  #   object: "接口 / 页面 / JS / 参数 / 业务功能"
  #   identity: "未登录 / 管理员 / 测试账号"
  #   method: "怎么测的，尽量一句话"
  #   result: "成功 / 失败 / 无异常 / 有弱信号 / 可复现"
  #   evidence_path: "evidence/..."
  #   status: tested|candidate|verified|rejected|blocked

findings:
  # - id: F001
  #   object: ""
  #   summary: "已确认或待确认的问题"
  #   evidence_path: "evidence/..."
  #   status: candidate|verified|rejected
  #   next: "继续验证 / 写报告 / 放弃"

blocked:
  # - id: B001
  #   object: ""
  #   reason: "为什么卡住"
  #   need: "需要什么才能继续"

next:
  priority: ""
  object: ""
  action: ""
  reason: ""
```