"""
Tests for the data loader module.
"""
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from stacking_sats.core.data_loader import load_btc_data


def test_load_btc_data_mock(monkeypatch, sample_price_data, temp_data_dir):
    """Test loading BTC data with a mock."""
    # Create a mock data file
    cache_file = os.path.join(temp_data_dir, "btc_usd_daily.parquet")
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    sample_price_data.to_parquet(cache_file)
    
    # Patch the data loader to use our temp directory
    def mock_get_data_dir():
        return temp_data_dir
    
    monkeypatch.setattr(
        "stacking_sats.core.data_loader._get_data_dir", 
        mock_get_data_dir
    )
    
    # Load the data
    data = load_btc_data(force_download=False)
    
    # Check that the data was loaded correctly
    assert isinstance(data, pd.DataFrame)
    assert "btc_close" in data.columns
    assert len(data) > 0
    assert isinstance(data.index, pd.DatetimeIndex)


def test_load_btc_data_error_handling(monkeypatch, temp_data_dir):
    """Test error handling when loading BTC data."""
    # Patch the data loader to use our temp directory
    def mock_get_data_dir():
        return temp_data_dir
    
    monkeypatch.setattr(
        "stacking_sats.core.data_loader._get_data_dir", 
        mock_get_data_dir
    )
    
    # Ensure the file doesn't exist
    cache_file = os.path.join(temp_data_dir, "btc_usd_daily.parquet")
    if os.path.exists(cache_file):
        os.remove(cache_file)
        
    # Mock the download function to raise an exception
    def mock_download_data(*args, **kwargs):
        raise Exception("Mock download error")
    
    monkeypatch.setattr(
        "stacking_sats.core.data_loader._download_btc_data", 
        mock_download_data
    )
    
    # Test that the data loader handles the error gracefully
    with pytest.raises(Exception) as excinfo:
        load_btc_data(force_download=True)
    
    assert "Mock download error" in str(excinfo.value) 