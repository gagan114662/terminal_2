@echo off
REM Run termnet.main using available Python

where python3 >nul 2>nul
if %errorlevel%==0 (
    python3 -m termnet.main %*
    exit /b
)

where python >nul 2>nul
if %errorlevel%==0 (
    python -m termnet.main %*
    exit /b
)

echo Error: Python is not installed.
exit /b 1
