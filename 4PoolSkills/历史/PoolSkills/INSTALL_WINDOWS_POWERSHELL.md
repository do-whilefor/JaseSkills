# Windows 安装说明

将本包解压后，把 `skills` 目录中的 10 个目录复制到 Claude Skills 目录：

```powershell
$src = "D:\Users\21452\Desktop\merged_authorized_security_skills\skills"
$dst = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item -Recurse -Force "$src\*" $dst
```

建议先备份你现有的 skills：

```powershell
$backup = "$env:USERPROFILE\.claude\skills_backup_$(Get-Date -Format yyyyMMdd_HHmmss)"
Copy-Item -Recurse -Force "$env:USERPROFILE\.claude\skills" $backup
```

验证结构：

```powershell
cd D:\Users\21452\Desktop\merged_authorized_security_skills
python -m pip install -r requirements.txt
npm install
python -m playwright install chromium
python scripts\skill_selftest.py --root .
python scripts\availability_check.py --out tool_availability.json
python run_engine_selftest.py
```


运行真实目标仓库：

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\run_skills.ps1 -TargetRoot C:\path\to\authorized\repo
```

如需使用已有授权边界文件：

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\run_skills.ps1 -TargetRoot C:\path\to\authorized\repo -ScopeFile C:\path\to\authorized\repo\scope.yaml
```
