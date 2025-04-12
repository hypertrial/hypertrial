"""Tests for the core/data/__init__.py module."""

import os
import sys
import pytest
import importlib
from unittest.mock import patch, mock_open

# Mock functions for testing
def mock_load_data(*args, **kwargs):
    return "mock_load_data_result"

def mock_clean_price_data(*args, **kwargs):
    return "mock_clean_price_data_result"

def mock_validate_price_data(*args, **kwargs):
    return "mock_validate_price_data_result"

def mock_extract_btc_data(*args, **kwargs):
    return "mock_extract_btc_data_result"

def test_init_with_data_py_exists():
    """Test when data.py exists and functions are imported"""
    # First import the module so it exists in sys.modules
    import core.data
    
    with patch('os.path.exists', return_value=True), \
         patch('importlib.util.spec_from_file_location'), \
         patch('importlib.util.module_from_spec'), \
         patch.object(sys, 'modules', {
             'data_module': type('MockModule', (), {
                 'load_data': mock_load_data,
                 'clean_price_data': mock_clean_price_data,
                 'validate_price_data': mock_validate_price_data
             })
         }):
        
        # Create a temporary module to reload
        temp_module = type('core.data', (), {})
        sys.modules['core.data'] = temp_module
        
        # Now import the module
        from core.data import load_data, clean_price_data, validate_price_data
        
        # Test the functions
        assert callable(load_data)
        assert callable(clean_price_data)
        assert callable(validate_price_data)

def test_init_with_data_py_not_exists():
    """Test when data.py doesn't exist and stub implementations are used"""
    with patch('os.path.exists', return_value=False):
        # Reimport to apply mocks
        if 'core.data' in sys.modules:
            importlib.reload(sys.modules['core.data'])
        
        # Now import the module
        from core.data import load_data, clean_price_data, validate_price_data
        
        # Test the stub functions raise NotImplementedError
        with pytest.raises(NotImplementedError, match="data.py module not found"):
            load_data()
        
        with pytest.raises(NotImplementedError, match="data.py module not found"):
            clean_price_data()
        
        with pytest.raises(NotImplementedError, match="data.py module not found"):
            validate_price_data()

def test_extract_btc_data_import_success():
    """Test successful import of extract_btc_data"""
    # Create a mock for the extract_data module
    mock_extract_data = type('MockExtractData', (), {'extract_btc_data': mock_extract_btc_data})
    
    with patch.dict('sys.modules', {'core.data.extract_data': mock_extract_data}):
        # Reimport to apply mocks
        if 'core.data' in sys.modules:
            importlib.reload(sys.modules['core.data'])
        
        # Now import the module
        from core.data import extract_btc_data
        
        # Test the function
        assert extract_btc_data() == "mock_extract_btc_data_result"

def test_extract_btc_data_import_error():
    """Test when extract_btc_data import fails"""
    # Directly patch the import statement that's used in core/data/__init__.py
    with patch('core.data.__init__.__all__', ['load_data', 'clean_price_data', 'validate_price_data']):
        with patch.dict('sys.modules', {'core.data.extract_data': None}):
            # Create a mock that raises ImportError when import is attempted
            with patch('core.data.__init__.extract_btc_data', None):
                # Reload the module with our patches
                if 'core.data' in sys.modules:
                    importlib.reload(sys.modules['core.data'])
                else:
                    import core.data
                
                # Verify that extract_btc_data is None
                from core.data import extract_btc_data
                assert extract_btc_data is None

def test_all_variable():
    """Test that __all__ contains the expected functions"""
    # Reimport to ensure clean state
    if 'core.data' in sys.modules:
        importlib.reload(sys.modules['core.data'])
    
    # Import the module
    import core.data
    
    # Check __all__ contains expected values
    expected_functions = ['load_data', 'clean_price_data', 'validate_price_data', 'extract_btc_data']
    for func in expected_functions:
        assert func in core.data.__all__ 