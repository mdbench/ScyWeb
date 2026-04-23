@echo off
setlocal enabledelayedexpansion

:: Force the script to stay in its own folder
cd /d "%~dp0"

:: Check specifically for Python 3.12 anywhere on the system
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python 3.12 not found.
    
    if exist "python-3.12.10-amd64.exe" (
        echo [*] Installing Python 3.12.10... Please accept any admin prompts.
        start /wait "" "python-3.12.10-amd64.exe" /quiet PrependPath=1 Include_test=0
        echo [+] Installation complete.
        echo [!] Please CLOSE this window and RE-RUN the script to refresh system paths.
        pause
        exit /b
    ) else (
        echo [!] ERROR: python-3.12.10-amd64.exe not found in this folder.
        pause
        exit /b
    )
)

:: Set venv-windows path
set "VENV_PYTHON=%~dp0venv-windows\Scripts\python.exe"

:: Create venv ONLY using the 3.12 engine
if not exist "%VENV_PYTHON%" (
    echo [*] Creating venv-windows specifically with Python 3.12...
    py -3.12 -m venv venv-windows
    
    echo [*] Installing requirements...
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if exist "requirements.txt" (
        "%VENV_PYTHON%" -m pip install -r requirements.txt
    )
)

:: Launch Gemtale
echo [*] Launching Gemtale using Python 3.12 environment...
start "Gemtale" cmd /k ""%VENV_PYTHON%" gemtale.py"

exit /b

