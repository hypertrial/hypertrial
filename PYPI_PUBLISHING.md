# Publishing Hypertrial to PyPI

This guide outlines the steps to publish the Hypertrial package to the Python Package Index (PyPI).

## Current Package Status

Hypertrial is published on PyPI at: https://pypi.org/project/hypertrial/

Users can install it with:

```bash
pip install hypertrial
```

## Prerequisites

1. Create a PyPI account if you don't have one:

   - Visit https://pypi.org/account/register/

2. Install required tools:
   ```bash
   pip install --upgrade build twine
   ```

## Build and Test Locally

1. Run the build script:

   ```bash
   chmod +x build_package.sh
   ./build_package.sh
   ```

2. This script will:

   - Build the package
   - Install it locally
   - Display the package files created

3. Verify the installation by running:
   ```bash
   python -c "import hypertrial; print(hypertrial.__version__)"
   ```

## Upload to PyPI

1. Upload to TestPyPI first (recommended):

   ```bash
   python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
   ```

2. Test the TestPyPI installation:

   ```bash
   pip install --index-url https://test.pypi.org/simple/ hypertrial
   ```

3. When ready, upload to the official PyPI:

   ```bash
   python -m twine upload dist/*
   ```

4. You'll be prompted for your PyPI username and password

## Updating the Package

1. Update the version number in:

   - `setup.py`
   - `core/__init__.py`

2. Build and upload again following the steps above

## Package Verification

After publishing, verify the package is installable and works correctly:

```bash
# Create a new virtual environment
python -m venv test_venv
source test_venv/bin/activate  # On Windows: test_venv\Scripts\activate

# Install the package
pip install hypertrial

# Test the package
python -c "import hypertrial; print(hypertrial.__version__)"
hypertrial --help
```

## Troubleshooting

- If you encounter "File already exists" errors, it means you're trying to upload a version that already exists. Update the version number.
- If you get authentication errors, make sure your PyPI credentials are correct.
- For other issues, check the PyPI documentation: https://packaging.python.org/guides/distributing-packages-using-setuptools/
