@echo off
REM Start Demo - Music Mood Prediction System

echo.
echo =====================================
echo    Music Mood Prediction - DEMO
echo =====================================
echo.

REM Navigate to backend
cd /d d:\MMB_FRONTBACK\backend

echo [1/2] Starting Backend Server...
echo      API: http://localhost:8000
echo      Docs: http://localhost:8000/api/docs
echo.
echo Press Ctrl+C to stop backend, then run frontend in another terminal

python -m uvicorn backend.main:app --reload --port 8000

pause
