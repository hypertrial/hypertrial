import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import patch

# Import the data validation functions
from core.data import validate_price_data, clean_price_data

class TestDataValidation:
    """Tests for data validation and cleaning functions."""

    def test_validate_price_data_basic(self):
        """Test basic price data validation."""
        # Create valid test data
        dates = pd.date_range(start='2020-01-01', end='2020-01-10')
        data = pd.DataFrame({
            'btc_close': np.random.uniform(10000, 20000, len(dates)),
            'btc_volume': np.random.uniform(1000, 2000, len(dates))
        }, index=dates)
        
        # Validate should pass
        assert validate_price_data(data) is True

    def test_validate_price_data_missing_columns(self):
        """Test validation with missing required columns."""
        # Create data missing required columns
        dates = pd.date_range(start='2020-01-01', end='2020-01-10')
        data = pd.DataFrame({
            'wrong_column': np.random.uniform(10000, 20000, len(dates))
        }, index=dates)
        
        # Validate should fail when we require btc_close
        with pytest.raises(ValueError):
            validate_price_data(data, required_columns=['btc_close'])

    def test_validate_price_data_invalid_values(self):
        """Test validation with invalid price values."""
        # Create data with invalid values
        dates = pd.date_range(start='2020-01-01', end='2020-01-10')
        data = pd.DataFrame({
            'btc_close': [-100, 0, np.nan, np.inf, -np.inf] + [10000] * 5,
            'btc_volume': [1000] * 10
        }, index=dates)
        
        # Validate should fail
        with pytest.raises(ValueError):
            validate_price_data(data)

    def test_clean_price_data(self):
        """Test data cleaning function."""
        # Create data with some issues to clean
        dates = pd.date_range(start='2020-01-01', end='2020-01-10')
        data = pd.DataFrame({
            'btc_close': [10000, np.nan, 12000, 0, 15000, np.inf, 18000, -np.inf, 20000, 22000],
            'btc_volume': [1000] * 10
        }, index=dates)
        
        # Clean the data
        cleaned_data = clean_price_data(data)
        
        # Check that invalid values were handled
        assert not cleaned_data['btc_close'].isna().any()
        assert not np.isinf(cleaned_data['btc_close']).any()
        assert (cleaned_data['btc_close'] > 0).all()

    def test_validate_price_data_date_range(self):
        """Test validation of date range requirements."""
        # Create data with insufficient date range
        dates = pd.date_range(start='2020-01-01', end='2020-01-05')
        data = pd.DataFrame({
            'btc_close': np.random.uniform(10000, 20000, len(dates)),
            'btc_volume': np.random.uniform(1000, 2000, len(dates))
        }, index=dates)
        
        # Validate should fail for insufficient date range
        with pytest.raises(ValueError):
            validate_price_data(data, min_days=10)

    def test_validate_price_data_duplicate_dates(self):
        """Test validation with duplicate dates."""
        # Create data with duplicate dates
        dates = pd.DatetimeIndex(['2020-01-01', '2020-01-01', '2020-01-02', '2020-01-02'])
        data = pd.DataFrame({
            'btc_close': np.random.uniform(10000, 20000, len(dates)),
            'btc_volume': np.random.uniform(1000, 2000, len(dates))
        }, index=dates)
        
        # Validate should fail
        with pytest.raises(ValueError):
            validate_price_data(data)

    def test_clean_price_data_duplicates(self):
        """Test handling of duplicate dates in cleaning."""
        # Create data with duplicate dates
        dates = pd.DatetimeIndex(['2020-01-01', '2020-01-01', '2020-01-02', '2020-01-02'])
        data = pd.DataFrame({
            'btc_close': [10000, 11000, 12000, 13000],
            'btc_volume': [1000, 1100, 1200, 1300]
        }, index=dates)
        
        # Clean the data
        cleaned_data = clean_price_data(data)
        
        # Check that duplicates were handled
        assert not cleaned_data.index.duplicated().any()
        assert len(cleaned_data) == 2  # Should have only unique dates

    def test_validate_price_data_gaps(self):
        """Test validation of data gaps."""
        # Create data with gaps
        dates = pd.DatetimeIndex(['2020-01-01', '2020-01-03', '2020-01-05'])
        data = pd.DataFrame({
            'btc_close': np.random.uniform(10000, 20000, len(dates)),
            'btc_volume': np.random.uniform(1000, 2000, len(dates))
        }, index=dates)
        
        # Validate should fail for gaps
        with pytest.raises(ValueError):
            validate_price_data(data, allow_gaps=False)

    def test_clean_price_data_gaps(self):
        """Test handling of data gaps in cleaning."""
        # Create data with gaps
        dates = pd.DatetimeIndex(['2020-01-01', '2020-01-03', '2020-01-05'])
        data = pd.DataFrame({
            'btc_close': [10000, 12000, 15000],
            'btc_volume': [1000, 1200, 1500]
        }, index=dates)
        
        # Clean the data
        cleaned_data = clean_price_data(data, fill_gaps=True)
        
        # Check that gaps were filled
        expected_dates = pd.date_range(start='2020-01-01', end='2020-01-05')
        assert len(cleaned_data) == len(expected_dates)
        assert cleaned_data.index.equals(expected_dates) 