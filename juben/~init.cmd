@echo off
setlocal

if "%~1"=="" (
    echo ERROR: novel file is required. Usage: ~init ^<novel.md^> [--episodes N] [--target-total-minutes N]
    exit /b 2
)

call "%~dp0_ops\controller-wrapper.cmd" init --force %*
exit /b %errorlevel%
