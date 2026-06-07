# Windows 运行说明

本包现在优先使用 Python 同进程流水线，避免在 Windows 上连续调用 Bash/子进程导致卡住。

推荐命令：

```powershell
py -3 -m pip install -r requirements.txt
py -3 info_end_run.py --input . --scope . --output out\info-end --max-files 5000
```

可选 Node AST 检查仍然保留为独立命令。Windows 上需要先安装 Node.js，并在项目根目录执行：

```powershell
npm install
node scripts/js-ast-endpoint-extractor.mjs . --strict-ast -o out\js-ast.jsonl
```

自检和清理可以使用 Windows 包装脚本：

```powershell
scripts\run-package-selftest.cmd . selftest\out
scripts\clean-release-artifacts.cmd .
```

PowerShell 版本：

```powershell
.\scripts\run-package-selftest.ps1 -Root . -OutDir selftest\out
.\scripts\clean-release-artifacts.ps1 -Root .
```

关于 symlink：Windows ZIP/解压工具经常把 symlink 展平成普通小文本文件。本包会把显式包含 `symlink` 的小型路径占位文件识别为 `symlink_skipped`，因此无需管理员权限或开发者模式也能保留覆盖门禁语义。
