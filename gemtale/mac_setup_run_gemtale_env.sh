#!/bin/bash

# Force the script to stay in its own folder
cd "$(dirname "$0")"

VENV_NAME="venv-mac"
VENV_PYTHON="./$VENV_NAME/bin/python"
INSTALLER="python-3.12.10-macos11.pkg"

# Check specifically for Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "[!] Python 3.12 not found. Attempting to install from local package..."

    if [ -f "$INSTALLER" ]; then
        echo "[*] Found $INSTALLER. Starting installation..."
        echo "[*] This requires admin permissions. Please enter your password if prompted."
        
        # -pkg specifies the file, -target / installs it to the main system drive
        sudo installer -pkg "$INSTALLER" -target /
        
        if [ $? -eq 0 ]; then
            echo "[+] Python 3.12 installed successfully."
        else
            echo "[!] Installation failed. Try running: sudo installer -pkg $INSTALLER -target /"
            exit 1
        fi
    else
        echo "[!] ERROR: $INSTALLER not found in this folder."
        echo "[*] Please download it from python.org and place it here."
        exit 1
    fi
fi

# Create venv-mac if missing
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[*] Creating $VENV_NAME specifically with Python 3.12..."
    python3.12 -m venv "$VENV_NAME"
    
    if [ $? -ne 0 ]; then
        echo "[!] Failed to create venv. Ensure you have write permissions."
        exit 1
    fi
    
    echo "[*] Installing requirements..."
    "$VENV_PYTHON" -m pip install --upgrade pip
    if [ -f "requirements.txt" ]; then
        "$VENV_PYTHON" -m pip install -r requirements.txt
    fi
fi

# Launch Gemtale
echo "[*] Launching Gemtale using Python 3.12 environment..."
"$VENV_PYTHON" gemtale.py
