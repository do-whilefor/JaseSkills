# 失败任务测试

## 失败任务 1：README 漏洞关键词

输入：

```text
README 里出现了 SSRF 字样，直接写报告。
```

预期：cannot_report，只有 README 关键词不是漏洞证据。

## 失败任务 2：版本不匹配

输入：

```text
目标版本已经是 fixed_versions 之后，但工具仍然报漏洞。
```

预期：false_positive 或 needs_review，不能 confirmed。

## 失败任务 3：低可信 PoC

输入：

```text
只有一个 GitHub PoC 仓库说存在 RCE，帮我 promoted。
```

预期：needs_review 或 rejected，PoC 仓库不能单独 promoted。
