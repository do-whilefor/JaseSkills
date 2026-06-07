@echo off
setlocal
set ROOT=%~1
if "%ROOT%"=="" set ROOT=.
set OUTDIR=%~2
if "%OUTDIR%"=="" set OUTDIR=selftest\out
if "%SELFTEST_STEP_TIMEOUT%"=="" set SELFTEST_STEP_TIMEOUT=45
py -3 "%ROOT%\scripts\selftest-step-runner.py" --root "%ROOT%" --outdir "%OUTDIR%" --timeout "%SELFTEST_STEP_TIMEOUT%"
if errorlevel 1 exit /b %errorlevel%
