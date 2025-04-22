@echo off
echo Installing Slide Chooser...

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed! Please install Python 3.8 or newer.
    echo You can download it from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

:: Activate virtual environment and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install pillow

:: Create requirements.txt file
echo pillow > requirements.txt

echo Installation complete!
echo.
echo To run the application, use run.bat
pause