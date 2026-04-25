@echo off
setlocal

if "%~1"=="" (
    echo Usage: ~review ^<batchXX^> PASS^|FAIL --reviewer ^<name^> [--reason "..."]
    exit /b 2
)

call "%~dp0_ops\controller-wrapper.cmd" batch-review-done %*
exit /b %errorlevel%
