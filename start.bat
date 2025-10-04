@echo off
chcp 65001 >nul
echo Starting Budget Manager Cloud...

REM Start backend in background
start /min "" python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8004 --reload

REM Wait 3 seconds
timeout /t 3 /nobreak >nul

REM Start frontend in background  
start /min "" python -m http.server 8080

REM Wait 2 seconds
timeout /t 2 /nobreak >nul

REM Open browser automatically
start http://127.0.0.1:8080

echo Budget Manager Cloud is now running!
echo Backend: http://127.0.0.1:8004
echo Frontend: http://127.0.0.1:8080
echo.
echo Browser should open automatically.
echo To stop: Close the minimized windows in taskbar.
echo.
pause
