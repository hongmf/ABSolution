@echo off
REM Windows batch file to run CDK app
REM Tries python3 first, then python

where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python3 app.py
) else (
    python app.py
)
