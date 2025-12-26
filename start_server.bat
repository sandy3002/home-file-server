@echo off
title Home File Server Dashboard

echo 🏠 Starting Home File Server Dashboard...
echo ==================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Install requirements
echo 📦 Installing required packages...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install requirements. Make sure pip is installed.
    pause
    exit /b 1
)

REM Create file storage directory
set FILE_DIR=%USERPROFILE%\Documents\FileServer
if not exist "%FILE_DIR%" (
    echo 📁 Creating file storage directory: %FILE_DIR%
    mkdir "%FILE_DIR%"
)

REM Get local IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
set LOCAL_IP=%LOCAL_IP: =%

echo.
echo 🚀 Starting server...
echo 📂 Files will be stored in: %FILE_DIR%
echo 🌐 Access dashboard at:
echo    • Local:   http://localhost:5000
if not "%LOCAL_IP%"=="" (
    echo    • Network: http://%LOCAL_IP%:5000
)
echo.
echo Press Ctrl+C to stop the server
echo ==================================

REM Start the Flask application
python app.py

pause