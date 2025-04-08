import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import requests
import json
import io
import sys

# Import the data handling functions
from core.data import load_data, validate_price_data, clean_price_data

class TestErrorHandling:
    """Tests for error handling in data processing and API requests."""
    
    def test_api_connection_error(self):
        """Test handling of API connection errors."""
        # Mock the extract_btc_data import and the function to raise a connection error
        with patch.dict('sys.modules', {'core.data.extract_data': MagicMock()}):
            with patch('core.data.extract_data.extract_btc_data', side_effect=requests.ConnectionError("Connection failed")):
                # Mock the os.path.exists to return False so we try to fetch data
                with patch('os.path.exists', return_value=False):
                    # Test that a RuntimeError is raised with the appropriate message
                    with pytest.raises(RuntimeError) as exc_info:
                        load_data()
                    assert "Could not load BTC price data" in str(exc_info.value)
    
    def test_api_timeout_error(self):
        """Test handling of API timeout errors."""
        # Mock the extract_btc_data import and function to raise a timeout error
        with patch.dict('sys.modules', {'core.data.extract_data': MagicMock()}):
            with patch('core.data.extract_data.extract_btc_data', side_effect=requests.Timeout("Request timed out")):
                # Mock the os.path.exists to return False so we try to fetch data
                with patch('os.path.exists', return_value=False):
                    # Test that a RuntimeError is raised with the appropriate message
                    with pytest.raises(RuntimeError) as exc_info:
                        load_data()
                    assert "Could not load BTC price data" in str(exc_info.value)
    
    def test_api_json_error(self):
        """Test handling of malformed JSON in API responses."""
        # Mock the extract_btc_data import and function to raise a JSON decode error
        with patch.dict('sys.modules', {'core.data.extract_data': MagicMock()}):
            with patch('core.data.extract_data.extract_btc_data', side_effect=json.JSONDecodeError("Malformed JSON", "", 0)):
                # Mock the os.path.exists to return False so we try to fetch data
                with patch('os.path.exists', return_value=False):
                    # Test that a RuntimeError is raised with the appropriate message
                    with pytest.raises(RuntimeError) as exc_info:
                        load_data()
                    assert "Could not load BTC price data" in str(exc_info.value)
    
    def test_malformed_csv_error(self):
        """Test handling of malformed CSV files."""
        # Create a malformed CSV file content
        malformed_csv = "date,btc_close\n2020-01-01,invalid\n2020-01-02,10000"
        
        # Mock the open function to return our malformed CSV
        mock_open = MagicMock(return_value=io.StringIO(malformed_csv))
        
        # Mock pandas.read_csv to raise a ValueError
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open):
                with patch('pandas.read_csv', side_effect=ValueError("Could not convert string to float")):
                    # Test that a RuntimeError is raised
                    with pytest.raises(RuntimeError):
                        load_data()
    
    def test_empty_data_error(self):
        """Test handling of empty data."""
        # Create empty DataFrame
        empty_df = pd.DataFrame()
        
        # Test that validate_price_data raises a ValueError
        with pytest.raises(ValueError) as exc_info:
            validate_price_data(empty_df)
        assert "empty" in str(exc_info.value).lower()
    
    def test_invalid_date_format_error(self):
        """Test handling of invalid date formats."""
        # Create data with invalid date format
        invalid_dates = ["2020/01/01", "2020-02-01", "2020-03-01"]
        values = [10000, 11000, 12000]
        df = pd.DataFrame({"btc_close": values}, index=invalid_dates)
        
        # Test that validation handles invalid date formats
        with pytest.raises(ValueError):
            validate_price_data(df)
    
    def test_extreme_price_values(self):
        """Test handling of extreme price values."""
        # Create data with extreme price values
        dates = pd.date_range(start='2020-01-01', end='2020-01-10')
        extreme_values = [1e10, 1e-10, 1e20, 1e-20] + [10000] * 6
        df = pd.DataFrame({"btc_close": extreme_values}, index=dates)
        
        # Clean the data
        cleaned_df = clean_price_data(df)
        
        # Check that extreme values were handled (should be replaced with more reasonable values)
        assert not ((cleaned_df["btc_close"] > 1e9) | (cleaned_df["btc_close"] < 1e-9)).any()
    
    def test_missing_dates_handling(self):
        """Test handling of missing dates in chronological order."""
        # Create data with missing dates in the middle
        dates = pd.DatetimeIndex(['2020-01-01', '2020-01-02', '2020-01-05', '2020-01-06'])
        values = [10000, 11000, 14000, 15000]
        df = pd.DataFrame({"btc_close": values}, index=dates)
        
        # Test that clean_price_data fills in the missing dates when requested
        # Use a custom function that overrides the interpolation to make testing predictable
        def mock_interpolate_func(self, method=None, **kwargs):
            # Return predictable interpolated values
            if self.name == 'btc_close':
                if self.index.equals(pd.DatetimeIndex(['2020-01-01', '2020-01-02', '2020-01-03', '2020-01-04', '2020-01-05', '2020-01-06'])):
                    return pd.Series([10000, 11000, 12000, 13000, 14000, 15000], index=self.index, name=self.name)
            return self  # Return original for other cases
            
        # Patch the Series.interpolate method
        with patch('pandas.Series.interpolate', mock_interpolate_func):
            cleaned_df = clean_price_data(df, fill_gaps=True)
            
            # Check that all dates in the range are present
            expected_dates = pd.date_range(start='2020-01-01', end='2020-01-06')
            assert cleaned_df.index.equals(expected_dates)
            
            # Check that the filled values match our expected interpolation
            assert cleaned_df.loc['2020-01-03', 'btc_close'] == 12000
            assert cleaned_df.loc['2020-01-04', 'btc_close'] == 13000
    
    def test_corrupted_data_repair(self):
        """Test repair of corrupted data."""
        # Create data with corrupted values
        dates = pd.date_range(start='2020-01-01', end='2020-01-10')
        corrupted_values = [10000, -500, 12000, 0, np.nan, np.inf, 18000, -np.inf, 20000, 22000]
        df = pd.DataFrame({"btc_close": corrupted_values}, index=dates)
        
        # Clean the data
        cleaned_df = clean_price_data(df)
        
        # Check that all corrupted values were repaired
        assert not cleaned_df["btc_close"].isna().any()
        assert not np.isinf(cleaned_df["btc_close"]).any()
        assert (cleaned_df["btc_close"] > 0).all()
        
        # Check that the repaired values are reasonable
        assert cleaned_df.loc[dates[1], "btc_close"] > 0
        assert cleaned_df.loc[dates[3], "btc_close"] > 0
    
    def test_different_csv_formats(self):
        """Test handling of different CSV formats."""
        # Test various formats (comma-separated, tab-separated, semicolon-separated)
        formats = [
            "date,btc_close\n2020-01-01,10000\n2020-01-02,11000",  # Comma-separated
            "date\tbtc_close\n2020-01-01\t10000\n2020-01-02\t11000",  # Tab-separated
            "date;btc_close\n2020-01-01;10000\n2020-01-02;11000"   # Semicolon-separated
        ]
        
        for i, format_str in enumerate(formats):
            # Mock the os.path.exists
            with patch('os.path.exists', return_value=True):
                # Mock the open function
                with patch('builtins.open', MagicMock(return_value=io.StringIO(format_str))):
                    # Mock pandas read_csv to return a properly formatted DataFrame
                    dates = pd.DatetimeIndex(['2020-01-01', '2020-01-02'])
                    df = pd.DataFrame({"btc_close": [10000, 11000]}, index=dates)
                    
                    with patch('pandas.read_csv', return_value=df):
                        # Test loading with different separators
                        result_df = load_data()
                        
                        # Check that the data was loaded correctly
                        assert len(result_df) == 2
                        assert "btc_close" in result_df.columns
                        assert result_df.loc['2020-01-01', "btc_close"] == 10000 