#!/bin/bash
set -e

echo "🚀 Starting build process..."

# Update pip first
echo "📦 Updating pip..."
python -m pip install --upgrade pip

# Install build tools with specific versions
echo "🔧 Installing build tools..."
python -m pip install setuptools==68.2.2 wheel==0.41.2 --force-reinstall --no-deps

# Verify setuptools installation
echo "✅ Verifying setuptools..."
python -c "import setuptools; print(f'Setuptools version: {setuptools.__version__}')"

# Install requirements without build isolation
echo "📋 Installing requirements..."
python -m pip install -r requirements.txt --no-build-isolation

# Install Playwright browsers
echo "🎭 Installing Playwright browsers..."
playwright install chromium

echo "✅ Build completed successfully!"