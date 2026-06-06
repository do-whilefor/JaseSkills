# 典型任务测试

## 典型任务 1：更新近 30 天漏洞

输入：

```text
请调用 SecKB Skills，更新近 30 天 CVE、GitHub Security Advisories、CISA KEV 和厂商公告，并把不确定内容放入 needs_review。
```

预期路由：01 → 02 → 03 → 10

预期输出：来源清单、freshness audit、新增记录、needs_review、conflict、索引更新建议。

## 典型任务 2：生成漏洞模板

输入：

```text
请根据这些公开来源为 SSRF 生成 SecKB 漏洞模板，必须包含误报条件和不可报告原因。
```

预期路由：01 → 04 → 03 → 10

预期输出：漏洞模板、适用范围、不适用范围、动态验证边界、质量门槛。

## 典型任务 3：本地项目授权验证

输入：

```text
目标是我本机搭建的开源项目 D:\lab\demo，请读取 SecKB 模板，验证一个疑似 IDOR。只允许最小化非破坏验证，并生成 evidence manifest。
```

预期路由：01 → 08 → 06 → 10

预期输出：授权确认、模板读取、前置条件、证据 manifest、结论分级、不能报告原因。
