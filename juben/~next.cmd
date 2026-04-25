@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" next %*
exit /b %errorlevel%
