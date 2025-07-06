#!/bin/bash

# S&P 500 MD&A Extractor Setup Script
# This script sets up the environment and tests the installation

set -e  # Exit on any error

echo "================================================"
echo "S&P 500 MD&A EXTRACTOR - SETUP SCRIPT"
echo "================================================"

# Check if Python 3.8+ is available
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if requested
if [[ "$1" == "--venv" ]]; then
    echo "Creating virtual environment..."
    python3 -m venv sp500_env
    source sp500_env/bin/activate
    echo "Virtual environment created and activated"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

# Make scripts executable
echo "Making scripts executable..."
chmod +x sp500_mda_extractor.py
chmod +x finbert_analyzer.py
chmod +x test_installation.py

# Create output directory
echo "Creating output directory..."
mkdir -p output

# Run installation test
echo "Running installation test..."
python3 test_installation.py

echo ""
echo "================================================"
echo "SETUP COMPLETE!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Test with a small sample:"
echo "   python3 sp500_mda_extractor.py --email your@email.com --max-companies 3"
echo ""
echo "2. Run FinBERT analysis on the results:"
echo "   python3 finbert_analyzer.py --input-file output/sp500_mda_finbert_*.csv --create-report"
echo ""
echo "3. For full S&P 500 extraction (will take several hours):"
echo "   python3 sp500_mda_extractor.py --email your@email.com --create-finbert"
echo ""
echo "Note: Replace 'your@email.com' with your actual email address"
echo ""

if [[ "$1" == "--venv" ]]; then
    echo "Virtual environment is activated. To deactivate later, run: deactivate"
fi