@echo off
setlocal

call "%~dp0juben\~promote.cmd" %*
exit /b %errorlevel%
