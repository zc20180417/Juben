@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" run %*
exit /b %errorlevel%
