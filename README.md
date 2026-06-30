## 个人维护命令

如果本地内容就是最终内容，推荐使用：

```powershell

git config --global core.longpaths true
git config core.longpaths true

if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
}

git add -A -- . 2>&1 | Tee-Object git-add-log.txt

git status --short
git diff --cached --name-status | Select-Object -First 50

git commit -m "Update skills"
git push origin main
```

如果需要确认 GitHub 是否与本地一致：

```powershell
git status --short
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

当 `git rev-parse HEAD` 和 `git ls-remote origin refs/heads/main` 的哈希一致时，说明本地提交已经成功同步到 GitHub。

---
