#!/bin/bash

# Check if python3 is installed
if command -v python3 &>/dev/null; then
    echo "Python3 is installed, running the script."
    python3 main.py
else
    echo "Python3 is not installed, please install Python3 to run this script."
fi
