#!/usr/bin/env bash

# Try python3 first, then fallback to python
if command -v python3 &> /dev/null; then
    python3 -m termnet.main "$@"
elif command -v python &> /dev/null; then
    python -m termnet.main "$@"
else
    echo "Error: Python is not installed."
    exit 1
fi
