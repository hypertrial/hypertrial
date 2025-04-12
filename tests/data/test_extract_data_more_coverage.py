import unittest
import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from unittest.mock import patch, MagicMock, call
import json
import requests
import sys
import importlib
import builtins

# Directly import the module to test
from core.data.extract_data import extract_btc_data, is_running_in_test


class TestExtractDataMoreCoverage:
    """Additional tests to improve coverage for extract_data.py"""

    def test_is_running_in_test_with_pytest_arg(self):
        """Test is_running_in_test when 'pytest' is in sys.argv"""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Add pytest to sys.argv
            sys.argv.append('pytest')
            
            # Call the function
            result = is_running_in_test()
            
            # Should return True when pytest is in sys.argv
            assert result is True
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_is_running_in_test_with_test_frame(self):
        """Test is_running_in_test when a test file is in the stack frames"""
        with patch('inspect.stack') as mock_stack:
            # Create a fake stack frame with a test file
            mock_frame = MagicMock()
            mock_frame.filename = '/path/to/test_some_file.py'
            mock_stack.return_value = [mock_frame]
            
            # Call the function
            result = is_running_in_test()
            
            # Should return True when a test file is in the stack
            assert result is True

    def test_is_running_in_test_no_test_indicators(self):
        """Test is_running_in_test when no test indicators are present"""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Remove any pytest from sys.argv
            sys.argv = [arg for arg in sys.argv if 'pytest' not in arg]
            
            with patch('inspect.stack') as mock_stack:
                # Create a fake stack with no test files
                mock_frame = MagicMock()
                mock_frame.filename = '/path/to/regular_file.py'
                mock_stack.return_value = [mock_frame]
                
                # Call the function
                result = is_running_in_test()
                
                # Should return False when no test indicators
                assert result is False
        finally:
            # Restore original sys.argv
            sys.argv = original_argv

    def test_extract_btc_data_coinmetrics_timeout_not_supported(self):
        """Test extract_btc_data when CoinMetricsClient doesn't support timeout"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class:
            # Create a mock client that will be returned by the second call
            mock_client = MagicMock()
            mock_response = MagicMock()
            
            # Create a non-empty dataframe to return
            mock_df = pd.DataFrame({
                'time': pd.date_range(start='2020-01-01', periods=5),
                'PriceUSD': [1000.0, 1100.0, 1200.0, 1300.0, 1400.0]
            })
            
            # Configure the mock chain
            mock_response.to_dataframe.return_value = mock_df
            mock_client.get_asset_metrics.return_value = mock_response
            
            # First call raises TypeError, second call returns our configured mock
            mock_client_class.side_effect = [
                TypeError("timeout is not a valid parameter"),
                mock_client
            ]
            
            with patch('pandas.DataFrame.to_csv'), \
                 patch('os.makedirs'):
                # Call with save_to_csv=False to avoid file operations
                result = extract_btc_data(save_to_csv=False)
                
                # Check that client was created twice - once with timeout, once without
                assert mock_client_class.call_count == 2
                
                # Verify API call was made
                mock_client.get_asset_metrics.assert_called_once()
                
                # Check result
                assert isinstance(result, pd.DataFrame)
                assert 'btc_close' in result.columns

    def test_extract_btc_data_connection_error(self):
        """Test extract_btc_data handling of connection error"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class:
            # Set up the mock
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Make get_asset_metrics raise a ConnectionError
            mock_client.get_asset_metrics.side_effect = requests.ConnectionError("Connection failed")
            
            # Call extract_btc_data and expect the exception to be re-raised
            with pytest.raises(requests.ConnectionError):
                extract_btc_data(save_to_csv=False)

    def test_extract_btc_data_timeout_error(self):
        """Test extract_btc_data handling of timeout error"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class:
            # Set up the mock
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Make get_asset_metrics raise a Timeout
            mock_client.get_asset_metrics.side_effect = requests.Timeout("Request timed out")
            
            # Call extract_btc_data and expect the exception to be re-raised
            with pytest.raises(requests.Timeout):
                extract_btc_data(save_to_csv=False)

    def test_extract_btc_data_json_decode_error(self):
        """Test extract_btc_data handling of JSON decode error"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class:
            # Set up the mock
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Make get_asset_metrics raise a JSONDecodeError
            # We need to provide the required arguments
            json_error = json.JSONDecodeError("Invalid JSON", "{", 1)
            mock_client.get_asset_metrics.side_effect = json_error
            
            # Call extract_btc_data and expect the exception to be re-raised
            with pytest.raises(json.JSONDecodeError):
                extract_btc_data(save_to_csv=False)

    def test_extract_btc_data_empty_dataframe(self):
        """Test extract_btc_data handling of empty dataframe"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class:
            # Set up the mock
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock response with empty dataframe
            mock_response = MagicMock()
            mock_response.to_dataframe.return_value = pd.DataFrame()  # Empty dataframe
            mock_client.get_asset_metrics.return_value = mock_response
            
            # Call extract_btc_data and expect ValueError
            with pytest.raises(ValueError, match="empty"):
                extract_btc_data(save_to_csv=False)

    def test_extract_btc_data_few_records_warning(self):
        """Test extract_btc_data warning for suspiciously small datasets"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class, \
             patch('logging.Logger.warning') as mock_warning:
            # Set up the mock
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock response with very few records
            mock_response = MagicMock()
            mock_df = pd.DataFrame({
                'time': pd.date_range(start='2020-01-01', periods=10),
                'PriceUSD': np.random.rand(10) * 1000
            })
            mock_response.to_dataframe.return_value = mock_df
            mock_client.get_asset_metrics.return_value = mock_response
            
            with patch('pandas.DataFrame.to_csv'), \
                 patch('os.makedirs'):
                # Call the function
                result = extract_btc_data(save_to_csv=False)
                
                # Verify warning was logged
                mock_warning.assert_called_once()
                assert "unusually low" in mock_warning.call_args[0][0].lower()
                
                # Check result still returned
                assert isinstance(result, pd.DataFrame)
                assert len(result) == 10

    def test_extract_btc_data_test_file_path_override(self):
        """Test extract_btc_data prevents overwriting production data in test env"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class, \
             patch('logging.Logger.warning') as mock_warning, \
             patch('core.data.extract_data.is_running_in_test', return_value=True), \
             patch('pandas.DataFrame.to_csv') as mock_to_csv, \
             patch('os.makedirs'):
            
            # Set up the mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock API response with valid data
            mock_response = MagicMock()
            mock_df = pd.DataFrame({
                'time': pd.date_range(start='2020-01-01', periods=100),
                'PriceUSD': np.random.rand(100) * 1000
            })
            mock_response.to_dataframe.return_value = mock_df
            mock_client.get_asset_metrics.return_value = mock_response
            
            # Call with production path
            result = extract_btc_data(save_to_csv=True, csv_path='core/data/btc_price_data.csv')
            
            # Verify warning about test environment was logged
            mock_warning.assert_any_call(
                mock_warning.call_args_list[0][0][0] if mock_warning.call_args_list else ""
            )
            
            # Check that to_csv was called with the test path instead
            mock_to_csv.assert_called_once()
            csv_path_arg = mock_to_csv.call_args[0][0]
            assert 'TEST_ONLY' in csv_path_arg

    def test_extract_btc_data_none_response(self):
        """Test extract_btc_data handling of None response"""
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class:
            # Set up the mock
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Make get_asset_metrics return None
            mock_client.get_asset_metrics.return_value = None
            
            # Call extract_btc_data and expect ValueError
            with pytest.raises(ValueError, match="Received None response"):
                extract_btc_data(save_to_csv=False)

    def test_extract_btc_data_coinmetrics_import_error(self):
        """Test extract_btc_data handling of CoinMetrics import error"""
        # Save original __import__ function
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == 'coinmetrics.api_client':
                raise ImportError("No module named 'coinmetrics.api_client'")
            return original_import(name, *args, **kwargs)
        
        try:
            # Patch __import__ to simulate import error for coinmetrics
            with patch('builtins.__import__', side_effect=mock_import):
                # Reload the module to trigger the import error
                if 'core.data.extract_data' in sys.modules:
                    del sys.modules['core.data.extract_data']
                
                # Import should raise the error
                with pytest.raises(ImportError, match="coinmetrics.api_client module is required"):
                    from core.data.extract_data import extract_btc_data
        finally:
            # Restore original import function
            builtins.__import__ = original_import

if __name__ == '__main__':
    pytest.main() 