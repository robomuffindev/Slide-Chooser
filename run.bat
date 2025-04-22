@echo off
echo Starting Slide Chooser...

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Run the application
python slide_chooser.py

:: Deactivate virtual environment on exit
call venv\Scripts\deactivate.bat