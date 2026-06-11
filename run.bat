@echo off
title AURA
if not exist .venv\Scripts\python.exe (
    echo   [!] No .venv found - run install.bat first!
    pause & exit /b 1
)
.venv\Scripts\python aura.py %*
pause
