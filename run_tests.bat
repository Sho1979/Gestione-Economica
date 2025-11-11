@echo off
setlocal
pushd %~dp0
python -m run_tests %*
set EXITCODE=%ERRORLEVEL%
popd
exit /b %EXITCODE%
