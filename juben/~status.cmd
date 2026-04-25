@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" status %*
exit /b %errorlevel%
