@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" export %*
exit /b %errorlevel%
