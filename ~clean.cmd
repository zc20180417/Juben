@echo off
setlocal

call "%~dp0juben\~clean.cmd" %*
exit /b %errorlevel%
