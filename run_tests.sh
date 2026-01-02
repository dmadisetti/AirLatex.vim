#!/bin/bash

set -e

echo "AirLatex.vim Test Runner"
echo "========================"
echo ""

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements-dev.txt

echo "Installing runtime dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
fi

pip install -q pynvim tornado requests beautifulsoup4 intervaltree

echo ""
echo "Running tests..."
echo "================"
pytest "$@"

echo ""
echo "Test run complete!"
