@echo off
setlocal

call "%~dp0juben\~map.cmd" %*
exit /b %errorlevel%
