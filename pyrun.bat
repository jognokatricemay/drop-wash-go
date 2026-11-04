@echo off
setlocal
set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"

if exist "%PY_EXE%" (
    "%PY_EXE%" %*
) else (
    python %*
)
