@echo off
setlocal

call "%~dp0juben\~init.cmd" %*
exit /b %errorlevel%
