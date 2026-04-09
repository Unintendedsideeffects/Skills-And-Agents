#!/bin/bash
# Obsidian to EPUB converter wrapper
# This script invokes obsidian2epub with the correct Python environment

set -e

OBSIDIAN2EPUB_DIR="${OBSIDIAN2EPUB_DIR:-/home/malcolm/Code/Obsidian2Epub}"
VENV_PYTHON="$OBSIDIAN2EPUB_DIR/.venv/bin/python"
SCRIPT="$OBSIDIAN2EPUB_DIR/obsidian2epub.py"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $OBSIDIAN2EPUB_DIR/.venv"
    echo "Please set OBSIDIAN2EPUB_DIR or install the tool first."
    exit 1
fi

if [ ! -f "$SCRIPT" ]; then
    echo "Error: obsidian2epub.py not found at $SCRIPT"
    exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT" "$@"
