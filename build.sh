#!/bin/bash
set -e

echo "🚀 Starting simplified build process..."

# Use system Python 3.11 if available
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
    echo "📍 Using Python 3.11: $(python3.11 --version)"
else
    PYTHON_CMD=python3
    echo "📍 Using default Python: $(python3 --version)"
fi

# Create virtual environment with Python 3.11
echo "🔧 Creating virtual environment..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Upgrade pip in virtual environment
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install build dependencies
echo "🛠️ Installing build dependencies..."
pip install setuptools wheel

# Install requirements
echo "📋 Installing requirements..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright Chromium..."
playwright install chromium

echo "✅ Build completed successfully!"