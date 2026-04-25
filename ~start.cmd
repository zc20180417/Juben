@echo off
setlocal

call "%~dp0juben\~start.cmd" %*
exit /b %errorlevel%
