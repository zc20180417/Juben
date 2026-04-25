@echo off
setlocal

call "%~dp0juben\~record.cmd" %*
exit /b %errorlevel%
