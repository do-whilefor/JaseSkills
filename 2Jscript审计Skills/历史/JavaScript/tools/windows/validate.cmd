@echo off
setlocal
cd /d "%~dp0\..\.."
node scripts\js_cross_platform_runner.mjs windows:validate
exit /b %ERRORLEVEL%
