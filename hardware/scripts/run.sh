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

# The Touch Display 2 is a portrait screen (720 x 1280). Turn it on its
# side so the player is landscape. Only done while the screen is still
# the right way up ("normal"), so a rotation you chose yourself in the
# Control Centre is left alone. If the picture comes out upside down,
# start it with STEMDECK_ROTATION=270 ./scripts/run.sh instead.
ROTATION="${STEMDECK_ROTATION:-90}"
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
WAYLAND="${WAYLAND_DISPLAY:-wayland-0}"

if command -v wlr-randr >/dev/null 2>&1 && [ -S "$RUNTIME_DIR/$WAYLAND" ]; then
    randr() {
        XDG_RUNTIME_DIR="$RUNTIME_DIR" WAYLAND_DISPLAY="$WAYLAND" wlr-randr "$@"
    }

    OUTPUT="$(randr 2>/dev/null | awk '/^DSI/ {print $1; exit}')"

    if [ -n "$OUTPUT" ]; then
        TRANSFORM="$(randr 2>/dev/null | awk -v out="$OUTPUT" '
            /^[^ ]/ {here = ($1 == out)}
            here && /Transform:/ {print $2; exit}')"

        if [ "$TRANSFORM" = "normal" ]; then
            if randr --output "$OUTPUT" --transform "$ROTATION"; then
                echo "Turned the screen ($OUTPUT) to landscape."
            fi
        fi
    fi
fi

# main.py imports its neighbours directly (from app_window import ...),
# so it has to run from inside core/.
cd "$HARDWARE_DIR/core"

exec "$PY" main.py "$@"
