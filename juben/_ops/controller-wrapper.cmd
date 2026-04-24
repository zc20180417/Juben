@echo off
setlocal

set "ROOT=%~dp0..\\"
set "CONTROLLER=%ROOT%_ops\controller.py"
set "SUBCOMMAND=%~1"
set "ARGS="

if "%SUBCOMMAND%"=="" (
    echo ERROR: controller subcommand is required 1>&2
    exit /b 2
)

shift

:collect_args
if "%~1"=="" goto run_controller
set "ARGS=%ARGS% "%~1""
shift
goto collect_args

:run_controller
if exist "%ROOT%.venv\Scripts\python.exe" (
    "%ROOT%.venv\Scripts\python.exe" "%CONTROLLER%" %SUBCOMMAND% %ARGS%
    exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%CONTROLLER%" %SUBCOMMAND% %ARGS%
    exit /b %errorlevel%
)

python "%CONTROLLER%" %SUBCOMMAND% %ARGS%
exit /b %errorlevel%
