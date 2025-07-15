#!/bin/bash
set -e  # Stop on any error

echo "🚀 Starting build process with Python 3.11..."

# Show Python version
python --version

# Clean any existing setuptools
echo "🧹 Cleaning existing setuptools..."
pip uninstall -y setuptools wheel || true

# Update pip to latest
echo "📦 Updating pip to latest..."
python -m pip install --upgrade pip

# Install setuptools and wheel from scratch
echo "🔧 Installing fresh setuptools and wheel..."
python -m pip install --no-cache-dir setuptools==69.5.1 wheel==0.43.0

# Verify installation
echo "✅ Verifying setuptools installation..."
python -c "import setuptools; print(f'✅ Setuptools {setuptools.__version__} installed successfully')"

# Install requirements
echo "📋 Installing project requirements..."
pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
echo "🎭 Installing Playwright Chromium..."
playwright install chromium

echo "✅ Build completed successfully with Python $(python --version)!"