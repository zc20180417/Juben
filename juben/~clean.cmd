@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" clean %*
exit /b %errorlevel%
