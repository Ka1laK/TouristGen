@echo off
echo ========================================
echo TouristGen Pro - Starting Frontend
echo ========================================
echo.

cd frontend

if not exist "node_modules\" (
    echo ERROR: Dependencies not installed!
    echo Please run setup_frontend.bat first
    pause
    exit /b 1
)

echo Starting Vite development server...
echo.
echo Frontend will be available at: http://localhost:5173
echo.
echo Press Ctrl+C to stop the server
echo.

call npm run dev
