@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" promote %*
exit /b %errorlevel%
