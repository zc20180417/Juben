@echo off
setlocal

call "%~dp0juben\~polish.cmd" %*
exit /b %errorlevel%
