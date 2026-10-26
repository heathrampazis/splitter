#!/bin/bash
#
# StemDeck setup, for a Raspberry Pi running Raspberry Pi OS (64-bit).
#
# Run it from anywhere:
#
#   ./scripts/setup.sh            install everything
#   ./scripts/setup.sh --reset    throw the environment away and rebuild it
#
# Installs the system packages, builds a Python environment in
# hardware/venv and checks the audio output and the GPIO controls.
# It is safe to run again: anything already done is skipped.
#
# Afterwards, start the player with ./scripts/run.sh. There is no need
# to activate the environment yourself - run.sh uses it directly.

set -euo pipefail

# Work out where everything is from this script's own location, so it
# does the same thing whichever folder you run it from.
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARDWARE_DIR="$(dirname "$SCRIPTS_DIR")"
VENV="$HARDWARE_DIR/venv"
PY="$VENV/bin/python"
REQUIREMENTS="$HARDWARE_DIR/requirements.txt"

heading() {
    printf "\n\033[1m%s\033[0m\n" "$1"
}

on_error() {
    echo
    echo "Setup stopped. The message above explains why."
}

trap on_error ERR

echo "========================================"
echo "       StemDeck Setup"
echo "========================================"
echo "Folder: $HARDWARE_DIR"

# ---- optional reset -----------------------------------------------------

if [ "${1:-}" = "--reset" ]; then
    heading "Removing the existing environment"
    rm -rf "$VENV"
fi

# ---- checks ---------------------------------------------------------------

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: Python 3 is not installed."
    exit 1
fi

echo "Python: $(python3 --version 2>&1)"

# PySide6 only publishes 64-bit ARM builds for Linux. On a 32-bit OS pip
# fails much later with a confusing "no matching distribution" error.
ARCH="$(uname -m)"

if [ "$ARCH" != "aarch64" ] && [ "$ARCH" != "x86_64" ]; then
    echo
    echo "WARNING: this system is $ARCH."
    echo "PySide6 needs a 64-bit OS. On a Raspberry Pi, install"
    echo "Raspberry Pi OS (64-bit) and run this script again."
fi

# ---- system packages ------------------------------------------------------

heading "Installing system packages"

sudo apt update
sudo apt install -y \
    python3-venv \
    python3-dev \
    ffmpeg \
    libportaudio2 \
    portaudio19-dev \
    libsndfile1 \
    alsa-utils \
    libasound2-dev \
    swig \
    liblgpio-dev

# ---- Python environment ---------------------------------------------------

heading "Python environment"

if [ ! -x "$PY" ]; then
    echo "Creating $VENV"
    python3 -m venv "$VENV"
else
    echo "Already exists: $VENV"
fi

# Everything below calls the environment's own Python directly, so the
# environment never needs activating - not here, and not in run.sh.

heading "Installing Python packages"
echo "PySide6 is large, so the first install takes a few minutes."
echo

"$PY" -m pip install --upgrade pip setuptools wheel --quiet --disable-pip-version-check
"$PY" -m pip install --disable-pip-version-check -r "$REQUIREMENTS"

heading "Checking Python packages"

"$PY" - <<'PY'
import importlib

for module, name in [
    ("PySide6", "PySide6"),
    ("gpiozero", "gpiozero"),
    ("lgpio", "lgpio"),
    ("mido", "mido"),
    ("rtmidi", "python-rtmidi"),
    ("sounddevice", "sounddevice"),
    ("numpy", "numpy"),
]:
    importlib.import_module(module)
    print(f"{name}: OK")
PY

# ---- audio ----------------------------------------------------------------

heading "Audio devices"

if command -v aplay >/dev/null 2>&1; then
    aplay -l || true
else
    echo "WARNING: aplay was not found."
fi

if aplay -l 2>/dev/null | grep -qi "USB"; then
    echo
    echo "USB audio device detected."
else
    echo
    echo "WARNING: no USB audio device detected."
    echo "This is okay if the adapter is not plugged in yet. Without it the"
    echo "player falls back to the default output, which may be HDMI."
fi

# ---- GPIO --------------------------------------------------------------

heading "GPIO"

"$PY" - <<'PY'
try:
    from gpiozero import Device
    from gpiozero.pins.lgpio import LGPIOFactory

    Device.pin_factory = LGPIOFactory()
    print("GPIO: OK (lgpio)")
except Exception as e:
    print("WARNING: GPIO is not available:", e)
    print("This is expected on a computer that is not a Raspberry Pi.")
PY

# ---- finish ---------------------------------------------------------------

chmod +x "$SCRIPTS_DIR/run.sh" "$SCRIPTS_DIR/setup.sh"

trap - ERR

echo
echo "========================================"
echo "       StemDeck Setup Complete"
echo "========================================"
echo
echo "Start the player with:"
echo "    $SCRIPTS_DIR/run.sh"
echo
