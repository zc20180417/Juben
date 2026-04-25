@echo off
setlocal

call "%~dp0juben\~extract.cmd" %*
exit /b %errorlevel%
