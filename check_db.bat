@echo off
REM FinSight Database Checker - Windows Batch File
echo ============================================
echo           FINSIGHT DATABASE CHECKER
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python first
    pause
    exit /b 1
)

REM Check if database checker script exists
if not exist "check_database.py" (
    echo ERROR: check_database.py not found
    echo Make sure you're running this from the FinSight directory
    pause
    exit /b 1
)

REM Run the database checker
echo Running database check...
echo.
python check_database.py

echo.
echo Database check completed.
pause