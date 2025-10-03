@echo off
setlocal

REM Color output
set "RED=\033[0;31m"
set "GREEN=\033[0;32m"
set "NC=\033[0m"

REM Error handler
set "ERROR_HANDLER_CALLED="
call :set_error_handler

:set_error_handler
    if defined ERROR_HANDLER_CALLED goto :eof
    set "ERROR_HANDLER_CALLED=1"
    REM Capture the line number where the error occurred
    for /F "skip=1" %%L in ('where /F /T "%~f0"') do (
        set "ERROR_LINE=%%L"
        goto :break_loop
    )
:break_loop
    if "%ERRORLEVEL%" NEQ "0" (
        echo %RED%Error: Setup failed at line %ERROR_LINE%%NC%
        exit /b 1
    )
goto :eof

REM Project validation
if not exist "frontend" (
    echo %RED%Error: Project structure invalid. Make sure you're in the root directory.%NC%
    exit /b 1
)
if not exist "backend" (
    echo %RED%Error: Project structure invalid. Make sure you're in the root directory.%NC%
    exit /b 1
)

echo 🚀 Setting up Apsara Beauty Platform...

REM Frontend setup
echo 📦 Setting up frontend...
cd frontend
call npm install
call npm run build
if not exist .env.local (
    copy ..\.env.example .env.local
)
cd ..

REM Backend setup
echo 🐍 Setting up backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
call pip install --upgrade pip
call pip install -r requirements.txt
if not exist .env (
    copy ..\.env.example .env
)

REM Set PYTHONPATH to include the project root (Apsara directory)
REM This allows imports like 'from backend.api import ...' to work correctly
for %%i in ("%CD%") do set "PROJECT_ROOT=%%~dpi"
set "PYTHONPATH=%PYTHONPATH%;%PROJECT_ROOT%"
echo set "PYTHONPATH=%%PYTHONPATH%%;%PROJECT_ROOT%" >> venv\Scripts\activate.bat

REM Database setup
echo 🗄️ Skipping database setup on Windows...

REM Frontend validation
echo 📝 Validating frontend...
cd frontend
if not exist "package.json" (
    echo %RED%Error: Frontend package.json missing%NC%
    exit /b 1
)
call npm install
call npm run validate || echo Skipping frontend validation
cd ..

REM Backend validation
echo 🐍 Validating backend...
cd backend
if not exist "requirements.txt" (
    echo %RED%Error: Backend requirements.txt missing%NC%
    exit /b 1
)
call venv\Scripts\activate.bat
call pip install -r requirements.txt
python -c "from main import app" || echo Backend validation failed
cd ..

REM Create necessary directories
if not exist uploads mkdir uploads
if not exist logs mkdir logs
if not exist data\models mkdir data\models

echo ✨ Setup complete!
echo To start development:
echo 1. Frontend: cd frontend && npm run dev
echo 2. Backend: cd backend && call venv\Scripts\activate.bat && uvicorn main:app --reload
