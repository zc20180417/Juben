@echo off
setlocal

set "ROOT=%~dp0..\\"
set "CONTROLLER=%ROOT%_ops\controller.py"
set "SUBCOMMAND=%~1"

if "%SUBCOMMAND%"=="" (
    echo ERROR: controller subcommand is required 1>&2
    exit /b 2
)

shift

if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" "%CONTROLLER%" %SUBCOMMAND% %*
    exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%CONTROLLER%" %SUBCOMMAND% %*
    exit /b %errorlevel%
)

python "%CONTROLLER%" %SUBCOMMAND% %*
exit /b %errorlevel%
