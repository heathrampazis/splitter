#!/bin/bash
#
# Splitter Studio
#
# Double-click this file in Finder, or run ./run.command in a terminal.
#
# The first launch builds a local Python environment and downloads the
# dependencies. That is roughly 2 GB, mostly PyTorch, and takes a while.
# Every launch after that opens the app straight away.
#
#   ./run.command            start the app
#   ./run.command --reset    throw the environment away and rebuild it

set -euo pipefail

# A file double-clicked in Finder starts in your home folder, not here.
# Everything below assumes we are in the software directory.
cd "$(dirname "$0")"

# On Python 3.9, pip's progress renderer can leave sys.stdout.encoding
# unset, which turns a harmless warning into a crash. Pinning the encoding
# and locale avoids that whole class of failure.
export PYTHONIOENCODING="utf-8"
export LC_ALL="${LC_ALL:-en_US.UTF-8}"
export LANG="${LANG:-en_US.UTF-8}"

VENV="venv"
STAMP="$VENV/.installed-from"
MIN_MINOR=9

heading() {
    printf "\n\033[1m%s\033[0m\n" "$1"
}

pause_then_close() {
    echo
    read -n 1 -s -r -p "Press any key to close this window."
    echo
}

# Without this, a Finder double-click can flash an error past too quickly
# to read and leave you none the wiser.
on_error() {
    echo
    echo "Setup stopped. The message above explains why."
    pause_then_close
}

trap on_error ERR

echo "========================================"
echo "       Splitter Studio"
echo "========================================"

# ---- optional reset -----------------------------------------------------

if [ "${1:-}" = "--reset" ]; then
    heading "Removing the existing environment"
    rm -rf "$VENV"
fi

# ---- find a usable Python ----------------------------------------------

find_python() {
    local candidate version major minor

    # Newest first. python3 on macOS is often Apple's old build, and a
    # current version avoids a pile of packaging papercuts.
    for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
        command -v "$candidate" >/dev/null 2>&1 || continue

        version=$("$candidate" -c 'import sys; print("%d %d" % sys.version_info[:2])' 2>/dev/null) || continue

        major=${version% *}
        minor=${version#* }

        if [ "$major" -eq 3 ] && [ "$minor" -ge "$MIN_MINOR" ]; then
            echo "$candidate"
            return 0
        fi
    done

    return 1
}

if [ ! -d "$VENV" ]; then
    if ! PYTHON=$(find_python); then
        echo
        echo "ERROR: Python 3.$MIN_MINOR or newer was not found."
        echo
        echo "Install it from python.org, or with Homebrew:"
        echo "    brew install python"
        exit 1
    fi

    heading "Creating the environment with $($PYTHON --version 2>&1)"

    if [ "$("$PYTHON" -c 'import sys; print(sys.version_info[1])')" -le 9 ]; then
        echo
        echo "NOTE: Python 3.9 is past end of life. This works, but if you"
        echo "hit packaging errors, a current version fixes most of them:"
        echo "    brew install python"
        echo "    ./run.command --reset"
        echo
    fi

    "$PYTHON" -m venv "$VENV"
fi

PY="$VENV/bin/python"

# ---- install dependencies when they change ------------------------------

# Comparing a checksum of requirements.txt against the one recorded at the
# last install means a normal launch skips pip entirely.
current_hash=$(shasum -a 256 requirements.txt | cut -d " " -f 1)
installed_hash=$(cat "$STAMP" 2>/dev/null || echo "none")

if [ "$current_hash" != "$installed_hash" ]; then
    heading "Installing dependencies"
    echo "This downloads about 2 GB the first time, mostly PyTorch."
    echo "Expect several minutes. It only happens once."
    echo

    # Always go through "python -m pip". Upgrading pip replaces the pip
    # script itself, which can leave a stale one running mid-install.
    # --no-compile skips pip's bytecode pre-compilation step. PySide6 ships
    # a Jinja template named __init__.tmpl.py which is not valid Python, and
    # on 3.9 the resulting warning crashes pip instead of being printed.
    # Python compiles modules on first import anyway, so nothing is lost.
    "$PY" -m pip install --upgrade pip --quiet --disable-pip-version-check
    "$PY" -m pip install --no-compile --disable-pip-version-check -r requirements.txt

    echo "$current_hash" > "$STAMP"

    heading "Dependencies installed"
else
    echo
    echo "Dependencies are up to date."
fi

# ---- system dependency --------------------------------------------------

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo
    echo "NOTE: ffmpeg was not found."
    echo "Demucs uses it to read MP3 and AIFF files. WAV will still work."
    echo "To install it:    brew install ffmpeg"
fi

# ---- run ----------------------------------------------------------------

heading "Starting Splitter Studio"
echo "Close the app window to quit."
echo

trap - ERR
set +e

"$PY" main.py
status=$?

set -e

if [ "$status" -ne 0 ]; then
    echo
    echo "The app exited with an error (code $status)."
    echo "The traceback above should say what went wrong."
    pause_then_close
fi
