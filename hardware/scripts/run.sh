#!/bin/bash
#
# Starts StemDeck. Run it from anywhere:
#
#   ./scripts/run.sh
#
# Uses the Python environment that setup.sh built in hardware/venv, so
# there is nothing to activate first.

set -euo pipefail

# Find everything from this script's own location, so it works whichever
# folder you start it from - including from a desktop shortcut or a
# service, which start in your home folder.
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARDWARE_DIR="$(dirname "$SCRIPTS_DIR")"
PY="$HARDWARE_DIR/venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "The Python environment has not been set up yet. Run:"
    echo "    $SCRIPTS_DIR/setup.sh"
    exit 1
fi

# Started over SSH there is no screen to draw on, and Qt stops with
# "could not connect to display". Point it at the Pi's own screen. On
# Raspberry Pi OS's Wayland desktop, :0 is the X compatibility layer,
# which Qt is happy to use.
if [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
    export DISPLAY=:0
    echo "No display set - using the Pi's own screen (DISPLAY=:0)."
fi

# main.py imports its neighbours directly (from app_window import ...),
# so it has to run from inside core/.
cd "$HARDWARE_DIR/core"

exec "$PY" main.py "$@"
