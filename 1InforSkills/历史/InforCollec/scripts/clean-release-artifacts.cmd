@echo off
setlocal
set ROOT=%~1
if "%ROOT%"=="" set ROOT=.
py -3 "%~dp0clean_release_artifacts.py" "%ROOT%"
exit /b %errorlevel%
