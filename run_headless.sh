#!/usr/bin/env bash
set -e

RENODE_PKG="renode-latest.pkg.tar.xz"
RENODE_DIR="renode_portable"

if [ ! -f "$RENODE_PKG" ]; then
    echo "Error: $RENODE_PKG not found."
    exit 1
fi

if [ ! -d "$RENODE_DIR" ]; then
    echo "Extracting Renode..."
    mkdir -p "$RENODE_DIR"
    tar -xf "$RENODE_PKG" -C "$RENODE_DIR"
fi

# The path inside the tarball seems to be opt/renode/bin/Renode.exe
RENODE_EXE="$RENODE_DIR/opt/renode/bin/Renode.exe"

if [ ! -f "$RENODE_EXE" ]; then
    echo "Error: Renode executable not found at $RENODE_EXE"
    exit 1
fi

# Check for mono
if ! command -v mono >/dev/null 2>&1; then
    echo "Error: mono is required but not found."
    exit 1
fi

echo "Running Renode..."
mono "$RENODE_EXE" "$@"
