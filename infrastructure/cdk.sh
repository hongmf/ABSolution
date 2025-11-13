#!/bin/bash
# Shell script to run CDK app
# Tries python3 first, then python

if command -v python3 &> /dev/null; then
    python3 app.py
elif command -v python &> /dev/null; then
    python app.py
else
    echo "Error: Python not found"
    exit 1
fi
