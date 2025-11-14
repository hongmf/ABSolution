#!/bin/bash

# Cross-platform virtual environment setup and activation script for ABSolution

set -e

echo "Setting up ABSolution virtual environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Determine the correct activation script path
if [ -f "venv/bin/activate" ]; then
    ACTIVATE_SCRIPT="venv/bin/activate"
    echo "Using Unix/Linux/Mac activation script: $ACTIVATE_SCRIPT"
elif [ -f "venv/Scripts/activate" ]; then
    ACTIVATE_SCRIPT="venv/Scripts/activate"
    echo "Using Windows activation script: $ACTIVATE_SCRIPT"
else
    echo "Error: Could not find activation script in venv/bin/ or venv/Scripts/"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$ACTIVATE_SCRIPT"

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Dependencies installed successfully!"
else
    echo "Warning: requirements.txt not found"
fi

echo ""
echo "Virtual environment setup complete!"
echo "To activate the virtual environment manually, run:"
echo "  source $ACTIVATE_SCRIPT"
