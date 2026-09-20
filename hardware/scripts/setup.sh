#!/bin/bash

set -e
echo "========================================"
echo "       StemDeck Setup"
echo "========================================"
echo

# CHECK PYTHON
PYTHON="python3"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed."
    exit 1
fi
echo "Python version:"
"$PYTHON" --version
echo

# SYSTEM DEPENDENCIES
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y \
    python3-venv \
    python3-dev \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    libsndfile1 \
    alsa-utils \
    swig \
    liblgpio-dev

# CHECK LGPIO LIBRARY
echo
echo "Checking lgpio system library..."
if ldconfig -p | grep -q "liblgpio"; then
    echo "liblgpio: OK"
else
    echo "WARNING: liblgpio was not found."
    echo "The lgpio Python package may not install."
fi

# CREATE VIRTUAL ENVIRONMENT
echo
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    "$PYTHON" -m venv venv
else
    echo "Virtual environment already exists."
fi

# ACTIVATE VIRTUAL ENVIRONMENT
echo
echo "Activating virtual environment..."
source venv/bin/activate

# UPDATE PIP
echo
echo "Updating pip..."
python -m pip install \
    --upgrade \
    pip \
    setuptools \
    wheel

# INSTALL PYTHON DEPENDENCIES
echo
echo "Installing Python dependencies..."
pip install \
    -r ../requirements.txt

# TEST PYTHON DEPENDENCIES
echo
echo "Testing Python dependencies..."

python - <<'PY'

import PySide6
import gpiozero
import lgpio
import sounddevice
import numpy

print("PySide6: OK")
print("gpiozero: OK")
print("lgpio: OK")
print("sounddevice: OK")
print("numpy: OK")

PY

# CHECK ALSA AUDIO
echo
echo "Checking audio devices..."
if command -v aplay >/dev/null 2>&1; then
    aplay -l || true
else
    echo "WARNING: aplay was not found."
fi

# CHECK USB AUDIO
echo
echo "Checking for USB audio..."
if aplay -l 2>/dev/null | grep -qi "USB Audio"; then
    echo "USB audio device detected."
else
    echo "WARNING: USB audio device not detected."
    echo "This is okay if the USB audio adapter is not currently plugged in."
fi

# TEST SOUNDDEVICE
echo
echo "Checking sounddevice..."
python - <<'PY'
import sounddevice as sd
print(sd.query_devices())
PY

# MAKE RUN SCRIPT EXECUTABLE
if [ -f "run.sh" ]; then
    chmod +x run.sh
    echo
    echo "run.sh marked as executable."
fi

# FINISHED
echo
echo "========================================"
echo "       StemDeck Setup Complete"
echo "========================================"
echo

echo "Virtual environment:"
echo "    ./venv"

echo

echo "Run StemDeck with:"
echo "    ./run.sh"

echo

echo "Or manually:"
echo "    source venv/bin/activate"
echo "    python3 main.py"

echo
echo "========================================"