@echo off
echo ========================================
echo     SysControl - System Manager
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo.
echo Starting SysControl...
python main.py
pause
