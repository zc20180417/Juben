@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" polish %*
exit /b %errorlevel%
