@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" start %*
exit /b %errorlevel%
