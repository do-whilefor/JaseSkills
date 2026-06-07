@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0run_skills.ps1" %*
endlocal
