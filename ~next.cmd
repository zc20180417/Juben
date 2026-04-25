@echo off
setlocal

call "%~dp0juben\~next.cmd" %*
exit /b %errorlevel%
