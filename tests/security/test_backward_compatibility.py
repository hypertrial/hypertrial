"""Tests for core/security.py backward compatibility functions.

This file tests the backward compatibility functions provided in core/security.py:
- validate_external_data(url)
- analyze_ast(code)

These functions serve as wrappers around the StrategySecurity methods 
and are maintained for backward compatibility with older code.
"""

import pytest
import importlib.util
import sys
import os
from unittest.mock import patch, MagicMock

# Import SecurityError from the package
from core.security import SecurityError, StrategySecurity

# We need to import directly from the module file, not the package
module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "security.py")
spec = importlib.util.spec_from_file_location("security_module", module_path)
security_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security_module)

# Now we can access the functions
validate_external_data = security_module.validate_external_data
analyze_ast = security_module.analyze_ast


class TestBackwardCompatibility:
    """Test cases for the backward compatibility functions in core/security.py."""

    def test_validate_external_data(self):
        """Test the validate_external_data function."""
        # Test with a valid URL from allowed domains
        with patch('core.security.strategy_security.StrategySecurity.validate_external_data') as mock_validate:
            mock_validate.return_value = None  # Function doesn't return anything when successful
            
            # Call the backward compatibility function
            result = validate_external_data("https://api.coinmetrics.io/v4/data")
            
            # Verify the StrategySecurity method was called with correct argument
            mock_validate.assert_called_once_with("https://api.coinmetrics.io/v4/data")
            assert result is None
    
    def test_validate_external_data_error(self):
        """Test validate_external_data function raises proper errors."""
        # Test with invalid URL that should raise SecurityError
        with patch('core.security.strategy_security.StrategySecurity.validate_external_data') as mock_validate:
            mock_validate.side_effect = SecurityError("External data source not allowed")
            
            # Call should raise the same error
            with pytest.raises(SecurityError, match="External data source not allowed"):
                validate_external_data("https://malicious-site.com/data.csv")
            
            # Verify the StrategySecurity method was called
            mock_validate.assert_called_once()
    
    def test_analyze_ast(self):
        """Test the analyze_ast function."""
        # Test with safe code
        safe_code = """
def safe_function():
    x = 1 + 2
    return x
"""
        with patch('core.security.strategy_security.StrategySecurity.analyze_ast') as mock_analyze:
            mock_analyze.return_value = None  # Function doesn't return anything when successful
            
            # Call the backward compatibility function
            result = analyze_ast(safe_code)
            
            # Verify the StrategySecurity method was called with correct argument
            mock_analyze.assert_called_once_with(safe_code)
            assert result is None
    
    def test_analyze_ast_error(self):
        """Test analyze_ast function raises proper errors for unsafe code."""
        # Test with unsafe code that should raise SecurityError
        unsafe_code = """
import subprocess
def unsafe_function():
    return subprocess.call('echo hello', shell=True)
"""
        with patch('core.security.strategy_security.StrategySecurity.analyze_ast') as mock_analyze:
            mock_analyze.side_effect = SecurityError("Dangerous subprocess call detected")
            
            # Call should raise the same error
            with pytest.raises(SecurityError, match="Dangerous subprocess call detected"):
                analyze_ast(unsafe_code)
            
            # Verify the StrategySecurity method was called
            mock_analyze.assert_called_once()
    
    def test_integration_with_strategy_security(self):
        """Test that backward compatibility functions correctly integrate with StrategySecurity."""
        # This test uses actual StrategySecurity implementation instead of mocking
        
        # Test with safe code - should not raise exceptions
        safe_code = """
def safe_strategy(df):
    return df
"""
        # Should not raise exceptions
        analyze_ast(safe_code)
        
        # Test with valid URL from ALLOWED_DATA_SOURCES (if configured in test environment)
        try:
            validate_external_data("https://api.coinmetrics.io/v4/data")
        except SecurityError as e:
            # This may fail in test environment if ALLOWED_DATA_SOURCES is not configured
            # But it should fail because of domain validation, not because of function error
            assert "External data source not allowed" in str(e) or "domain" in str(e).lower() 