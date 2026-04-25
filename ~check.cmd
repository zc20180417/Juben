@echo off
setlocal

call "%~dp0juben\~check.cmd" %*
exit /b %errorlevel%
