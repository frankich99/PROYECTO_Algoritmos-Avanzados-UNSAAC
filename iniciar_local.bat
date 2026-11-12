@echo off
chcp 65001 > nul
title Rutas Mínimas Cusco - Launcher
echo ============================================================
echo   Iniciando Rutas Mínimas en Cusco (Backend + Frontend)
echo ============================================================
echo.
echo [1/2] Iniciando backend FastAPI en http://127.0.0.1:8000 ...
start "Backend - FastAPI Uvicorn (Puerto 8000)" cmd /k ".\.venv\Scripts\python.exe -m uvicorn web_api:app --app-dir python --host 127.0.0.1 --port 8000"

echo [2/2] Esperando 2 segundos e iniciando frontend Vite en http://127.0.0.1:5173 ...
timeout /t 2 /nobreak > nul
start "Frontend - Vite Dev (Puerto 5173)" cmd /k "cd web && npm run dev"

echo.
echo Servidores en ejecución:
echo   - Backend:  http://127.0.0.1:8000/docs
echo   - Frontend: http://127.0.0.1:5173/
echo.
echo Para detenerlos, simplemente cierra las dos ventanas que se abrieron.
