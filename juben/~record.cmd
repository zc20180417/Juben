@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" record %*
exit /b %errorlevel%
