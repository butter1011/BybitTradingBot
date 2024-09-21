
@echo off

REM Check if required modules are installed
pip freeze | findstr /i "requests pybit" > nul
if %errorlevel% neq 0 (
    echo Installing required modules...
    pip install -r requirements.txt
)

REM Run the main.py script
python main.py

pause
