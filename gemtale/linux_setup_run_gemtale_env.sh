#!/bin/bash

# Force the script to stay in its own folder
cd "$(dirname "$0")"

VENV_NAME="venv-linux"
VENV_PYTHON="./$VENV_NAME/bin/python"
INSTALLER="python-3.12.10.tar.xz"
BUILD_DIR="Python-3.12.10"

# Check if Python 3.12 is already installed, if not, build from local installer
if ! command -v python3.12 &> /dev/null; then
    echo "[!] Python 3.12 not found. Attempting to build from local installer..."

    if [ -f "$INSTALLER" ]; then
        echo "[*] Extracting $INSTALLER..."
        tar -xf "$INSTALLER"
        
        cd "$BUILD_DIR"
        
        echo "[*] Configuring and Compiling Python (this may take a few minutes)..."
        # --prefix ensures it installs locally to /usr/local to avoid conflicts
        ./configure --enable-optimizations --prefix=/usr/local
        make -j$(nproc)
        
        echo "[*] Installing... (may ask for sudo password)"
        # 'altinstall' ensures it does not overwrite the system's default python3
        sudo make altinstall
        
        cd ..
        # Cleanup build folder to save space
        rm -rf "$BUILD_DIR"
        
        echo "[+] Installation complete."
    else
        echo "[!] ERROR: $INSTALLER not found in this folder."
        exit 1
    fi
fi

# Create venv-linux if missing
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[*] Creating $VENV_NAME specifically with Python 3.12..."
    python3.12 -m venv "$VENV_NAME"
    
    if [ $? -ne 0 ]; then
        echo "[!] Failed to create venv. Ensure 'python3.12-venv' is installed."
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
