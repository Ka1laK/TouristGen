@echo off
echo ========================================
echo TouristGen Pro - Starting Backend
echo ========================================
echo.

cd backend

if not exist "venv\" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_backend.bat first
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Starting FastAPI server...
echo.
echo Backend will be available at: http://localhost:8000
echo API Documentation at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m app.main
