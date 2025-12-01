@echo off
echo ========================================
echo TouristGen Pro - Frontend Setup
echo ========================================
echo.

cd frontend

echo Installing dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To start the frontend, run:
echo   cd frontend
echo   npm run dev
echo.
pause
