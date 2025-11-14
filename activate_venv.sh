#!/bin/bash

# Dynamic virtual environment activation script
# This script detects the correct activation path for the current platform

# Determine the correct activation script path
if [ -f "venv/bin/activate" ]; then
    ACTIVATE_SCRIPT="venv/bin/activate"
elif [ -f "venv/Scripts/activate" ]; then
    ACTIVATE_SCRIPT="venv/Scripts/activate"
else
    echo "Error: Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Source the activation script
source "$ACTIVATE_SCRIPT"
echo "Virtual environment activated using: $ACTIVATE_SCRIPT"
