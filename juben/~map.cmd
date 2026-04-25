@echo off
setlocal

call "%~dp0_ops\controller-wrapper.cmd" map-book %*
exit /b %errorlevel%
