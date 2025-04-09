#!/bin/bash
set -e

echo "Building the Hypertrial package..."

# Make sure build tools are installed
python3 -m pip install --upgrade pip build twine

# Clean previous build artifacts
rm -rf dist/ build/ *.egg-info/

# Build the package
python3 -m build

echo "Package built successfully!"
echo "Distribution files available in the dist/ directory:"
ls -la dist/

echo "Testing the package locally..."
python3 -m pip install --force-reinstall dist/hypertrial-*.whl

echo "Package installation completed successfully!"
echo
echo "To upload to PyPI, run the following command:"
echo "python3 -m twine upload dist/*"
echo
echo "(You will need to create a PyPI account if you don't have one already)"
echo "Visit https://pypi.org/account/register/ to create an account" 