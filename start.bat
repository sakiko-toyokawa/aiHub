@echo off
title AI Knowledge Hub

echo.
echo ===========================================================
echo         AI Knowledge Hub - Quick Start Script
echo ===========================================================
echo.

:: Set variables
set "PROJECT_DIR=%~dp0"
set "BACKEND_DIR=%PROJECT_DIR%backend"
set "FRONTEND_DIR=%PROJECT_DIR%frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"

echo Project Directory: %PROJECT_DIR%
echo.

:: Check Python
echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%a in ('python --version 2^>^&1') do echo [OK] Python version: %%a
echo.

:: Check Node.js
echo Checking Node.js environment...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)
for /f "delims=" %%a in ('node --version') do echo [OK] Node.js version: %%a
echo.

:: Create virtual environment
echo Setting up Python virtual environment...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

:: Activate virtual environment and install dependencies
echo Installing backend dependencies...
call "%VENV_DIR%\Scripts\activate.bat"

:: Use Tsinghua mirror for faster download in China
set "PIP_CONFIG_FILE=%BACKEND_DIR%\pip.ini"

echo   Upgrading pip (using Tsinghua mirror)...
python -m pip install --upgrade pip

echo   Installing requirements (using Tsinghua mirror)...
pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo   Installing/Upgrading bilibili-api-python 
pip install --upgrade bilibili-api-python>=16.2.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo WARNING: Failed to install bilibili-api-python, Bilibili crawler may not work
)

echo [OK] Backend dependencies installed
echo.

:: Check .env file
echo Checking environment configuration...
if not exist "%BACKEND_DIR%\.env" (
    echo WARNING: .env file not found, will use default configuration
    echo        Please copy backend\.env.example to backend\.env for customization
) else (
    echo [OK] Environment configuration file found
)
echo.

:: Install frontend dependencies
echo Installing frontend dependencies...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    call pnpm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies already exist
)
echo.

cd /d "%PROJECT_DIR%"

:: Start backend service (in new window)
echo Starting backend service...
start "AI Knowledge Hub - Backend" cmd /k "cd /d "%BACKEND_DIR%" && call "%VENV_DIR%\Scripts\activate.bat" && chcp 65001 >nul && set PYTHONIOENCODING=utf-8 && set PYTHONUNBUFFERED=1 && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo   Backend URL: http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo.

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend service (in new window)
echo Starting frontend service...
start "AI Knowledge Hub - Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"
echo   Frontend URL: http://localhost:5173
echo.

echo ===========================================================
echo [OK] All services started!
echo.
echo Access URLs:
echo   Frontend:     http://localhost:5173
echo   Backend API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/docs
echo.
echo How to stop:
echo   Simply close the opened command line windows
echo ===========================================================
echo.

pause
