@echo off
REM Cross-platform virtual environment setup script for ABSolution (Windows)

echo Setting up ABSolution virtual environment...

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Determine the correct activation script path
if exist "venv\Scripts\activate.bat" (
    set ACTIVATE_SCRIPT=venv\Scripts\activate.bat
    echo Using Windows activation script: %ACTIVATE_SCRIPT%
) else if exist "venv\bin\activate" (
    set ACTIVATE_SCRIPT=venv\bin\activate
    echo Using Unix/Linux/Mac activation script: %ACTIVATE_SCRIPT%
) else (
    echo Error: Could not find activation script in venv\Scripts\ or venv\bin\
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call %ACTIVATE_SCRIPT%

REM Install requirements
if exist "requirements.txt" (
    echo Installing Python dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo Dependencies installed successfully!
) else (
    echo Warning: requirements.txt not found
)

echo.
echo Virtual environment setup complete!
echo To activate the virtual environment manually, run:
echo   %ACTIVATE_SCRIPT%
