#!/usr/bin/env bash
export PYRENODE_PKG=`pwd`/renode-latest.pkg.tar.xz
set -euo pipefail

# Simple helper to create a Python virtualenv, install dependencies and run the UI
# Usage:
#   ./run_ui.sh [--venv DIR] [--python PYTHON] [--] [args...]
# Environment overrides:
#   PYTHON - path to python executable (default: python3)
#   VENV_DIR - virtualenv directory (default: .venv)

VENV_DIR_DEFAULT=".venv"
PYTHON_DEFAULT="python3"

show_help() {
    cat <<EOF
Usage: $0 [--venv DIR] [--python PYTHON] [--] [args...]

Creates/activates a virtual environment, installs dependencies from
`requirements.txt` and runs `main.py`.

Options:
  --venv DIR     Virtualenv directory (default: ${VENV_DIR_DEFAULT})
  --python PATH  Python interpreter to use (default: ${PYTHON_DEFAULT})
  --help         Show this help

You can also set the environment variables PYTHON and VENV_DIR to override
defaults.
EOF
}

VENV_DIR="${VENV_DIR:-$VENV_DIR_DEFAULT}"
PYTHON="${PYTHON:-$PYTHON_DEFAULT}"

# Basic arg parsing
while [[ ${#} -gt 0 ]]; do
    case "$1" in
        --venv)
            VENV_DIR="$2"; shift 2;;
        --python)
            PYTHON="$2"; shift 2;;
        --help|-h)
            show_help; exit 0;;
        --)
            shift; break;;
        -* )
            echo "Unknown option: $1" >&2; show_help; exit 1;;
        *)
            break;;
    esac
done

# Remaining args will be passed to the Python app
APP_ARGS=("$@")

# Change to the script's directory
cd "$(dirname "${BASH_SOURCE[0]}")"

echo "Using python: $PYTHON"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Error: Python executable '$PYTHON' not found." >&2
    exit 2
fi

# Check for mono
if ! command -v mono >/dev/null 2>&1; then
    if [ "$EUID" -ne 0 ]; then
        echo "Error: Mono is missing. Please run this script as root (sudo) to install dependencies." >&2
        echo "Usage: sudo $0 $@" >&2
        exit 1
    else
        echo "Installing mono..."
        DEBIAN_FRONTEND=noninteractive apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y mono-complete
    fi
fi

# If running as root (and likely invoked via sudo), drop privileges for the rest of the execution
if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ]; then
    echo "Dependencies installed. Dropping privileges to user '$SUDO_USER' to run the application..."
    exec sudo -u "$SUDO_USER" "$0" "$@"
fi

# Ensure Python >= 3.10
if ! "$PYTHON" - <<'PY' 2>/dev/null
import sys
sys.exit(0 if sys.version_info >= (3,10) else 1)
PY
then
    echo "Error: Python 3.10 or newer is required." >&2
    "$PYTHON" --version || true
    exit 3
fi

echo "Virtualenv dir: $VENV_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtualenv in $VENV_DIR..."
    "$PYTHON" -m venv "$VENV_DIR"
fi

PIP="$VENV_DIR/bin/pip"
PY_BIN="$VENV_DIR/bin/python"

if [[ ! -x "$PIP" ]]; then
    echo "Error: pip not found inside virtualenv ($PIP)." >&2
    exit 4
fi

echo "Upgrading pip inside virtualenv..."
$PIP install --upgrade pip

REQ_FILE="requirements.txt"
if [[ ! -f "$REQ_FILE" ]]; then
    echo "Warning: $REQ_FILE not found. Skipping dependency install." >&2
else
    echo "Installing dependencies from $REQ_FILE..."
    $PIP install -r "$REQ_FILE"
fi

echo "Running application (main.py)..."
"$PY_BIN" main.py "${APP_ARGS[@]}"
