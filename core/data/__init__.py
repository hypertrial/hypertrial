# __init__.py for core/data package
# This makes the directory a proper Python package

import os
import sys
import importlib.util

# Get directory path for this module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

# Path to data.py
data_py_path = os.path.join(parent_dir, 'data.py')

# Check if data.py exists
if os.path.exists(data_py_path):
    # Import load_data and other functions from data.py
    spec = importlib.util.spec_from_file_location('data_module', data_py_path)
    data_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(data_module)
    
    # Get the functions we need
    load_data = data_module.load_data
    clean_price_data = data_module.clean_price_data
    validate_price_data = data_module.validate_price_data
else:
    # Define stub implementations if data.py is not found
    def load_data(*args, **kwargs):
        raise NotImplementedError("data.py module not found")
    
    def clean_price_data(*args, **kwargs):
        raise NotImplementedError("data.py module not found")
    
    def validate_price_data(*args, **kwargs):
        raise NotImplementedError("data.py module not found")

# Import extract_data.py functions
try:
    from .extract_data import extract_btc_data
except ImportError:
    extract_btc_data = None

# Define what to export
__all__ = ['load_data', 'clean_price_data', 'validate_price_data', 'extract_btc_data']

__version__ = "0.1.11"
