@echo off
title 🚀 Training Analytics Scraper + Dashboard
echo =======================================================
echo       TRAINING ANALYTICS DASHBOARD LAUNCHER
echo =======================================================

REM ======================================================
REM (1) ACTIVATE ENVIRONMENT (OPTIONAL)
REM ======================================================
REM Uncomment if using a virtual environment:
REM call venv\Scripts\activate
REM OR for Anaconda:
REM call C:\Users\YourName\anaconda3\Scripts\activate.bat

echo.
echo =======================================
echo   Step 1: Upgrading pip
echo =======================================
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ❌ Failed to upgrade pip
    pause
    exit /b
)

echo.
echo =======================================
echo   Step 2: Installing required libraries
echo =======================================
echo.

REM === DASHBOARD LIBRARIES ===
pip install --quiet streamlit pandas plotly

REM === SCRAPER LIBRARIES ===
pip install --quiet playwright requests beautifulsoup4 lxml tqdm

REM === VISUALIZATION + GUI LIBRARIES ===
pip install --quiet matplotlib seaborn tk

REM === OPTIONAL UTILITIES ===
pip install --quiet openpyxl schedule

if %errorlevel% neq 0 (
    echo ❌ Library installation failed. Please check your Python setup.
    pause
    exit /b
)

echo ✅ All required libraries installed successfully!
echo.

REM ======================================================
REM (3) INITIALIZE PLAYWRIGHT (first-time setup)
REM ======================================================
echo Checking Playwright browser installation...
python -m playwright install chromium >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Playwright browser may already be installed.
) else (
    echo ✅ Playwright Chromium installed successfully!
)
echo.

REM ======================================================
REM (4) RUN SCRAPER SCRIPT
REM ======================================================
echo =======================================
echo   Step 3: Running scraper.py
echo =======================================
echo.

python scraper.py
if %errorlevel% neq 0 (
    echo ❌ Error running scraper.py
    pause
    exit /b
)

echo ✅ Scraper completed successfully!
echo.

REM ======================================================
REM (5) LAUNCH STREAMLIT DASHBOARD
REM ======================================================
echo =======================================
echo   Step 4: Launching dashboard.py
echo =======================================
echo.

start "" streamlit run dashboard.py

REM Wait 5 seconds, then open dashboard in browser
timeout /t 5 >nul
start "" http://localhost:8501

echo.
echo ✅ Dashboard is live at: http://localhost:8501
echo -------------------------------------------------------
echo Press any key to close this window.
pause >nul
exit
