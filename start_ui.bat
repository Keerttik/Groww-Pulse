@echo off
echo Starting Groww Pulse Web UI...

echo Starting FastAPI Backend...
start "Groww Pulse Backend" cmd /k "python -m uvicorn agent.api:app --host 127.0.0.1 --port 8001"

echo Starting Vite Frontend...
cd web
start "Groww Pulse Frontend" cmd /k "npm run dev"

echo Both servers are starting. You should see two new command prompt windows.
echo The frontend will be available at http://localhost:5173
pause
