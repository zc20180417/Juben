@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" check %*
exit /b %errorlevel%
