@echo off
setlocal

call "%~dp0juben\~run.cmd" %*
exit /b %errorlevel%
