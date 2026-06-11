@echo off
title AURA installer
echo.
echo   ============================================
echo      A U R A  -  one-click installer
echo   ============================================
echo.

where py >nul 2>nul
if errorlevel 1 (
    echo   [!] Python launcher not found. Install Python 3.12 from python.org
    pause & exit /b 1
)

py -3.12 --version >nul 2>nul
if errorlevel 1 (
    echo   [!] Python 3.12 not found. AURA needs Python 3.10-3.12 ^(mediapipe limit^).
    echo       Install it with:  winget install Python.Python.3.12
    pause & exit /b 1
)

echo   [1/3] creating virtual environment (.venv)...
py -3.12 -m venv .venv
if errorlevel 1 ( echo   [!] venv creation failed & pause & exit /b 1 )

echo   [2/3] installing dependencies (1-3 min, mediapipe is chunky)...
.venv\Scripts\python -m pip install --upgrade pip -q
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 ( echo   [!] pip install failed - see docs\TROUBLESHOOTING.md & pause & exit /b 1 )

echo   [3/3] running self-test...
.venv\Scripts\python aura.py --self-test
if errorlevel 1 ( echo   [!] self-test failed - see docs\TROUBLESHOOTING.md & pause & exit /b 1 )

echo.
echo   ============================================
echo      DONE! Launch AURA with:  run.bat
echo   ============================================
echo.
pause
