@echo off
setlocal

call "%~dp0juben\~status.cmd" %*
exit /b %errorlevel%
