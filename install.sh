#!/bin/bash

echo "Installing Clearoid dependencies..."

# Check Python version
python3 --version

# Install dependencies
pip3 install -r backend/requirements.txt

echo ""
echo "Installation complete!"
echo ""
echo "Run the connection test:"
echo "  python3 test_connections.py"
echo ""
echo "Start the server:"
echo "  ./start.sh"
