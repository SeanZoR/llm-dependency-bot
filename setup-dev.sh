#!/bin/bash
# Development environment setup script

set -e

echo "🚀 Setting up LLM Dependency Bot development environment..."

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo ""
echo "Installing pre-commit hooks..."
pre-commit install

# Run tests to verify setup
echo ""
echo "Running tests to verify setup..."
pytest

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To run pre-commit checks:"
echo "  pre-commit run --all-files"
echo ""
echo "Happy coding! 🎉"
