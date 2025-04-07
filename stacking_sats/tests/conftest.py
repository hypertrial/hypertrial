"""
Pytest fixtures for stacking_sats tests.
"""
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_price_data():
    """
    Generate sample price data for testing.
    
    Returns:
        DataFrame with BTC price data
    """
    # Create a date range for the last 1000 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=1000)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Seed for reproducibility
    np.random.seed(42)
    
    # Generate synthetic price data
    # Start at $10,000 and add random daily changes
    price = 10000.0
    prices = [price]
    
    for _ in range(1, len(dates)):
        # Daily percentage change: mostly small, occasional big moves
        daily_change = np.random.normal(0.001, 0.02)  # mean=0.1%, std=2%
        
        # Apply change
        price *= (1 + daily_change)
        prices.append(price)
    
    # Create DataFrame
    df = pd.DataFrame({
        'btc_close': prices,
        'btc_volume': np.random.uniform(1e9, 5e9, size=len(dates))
    }, index=dates)
    
    return df


@pytest.fixture
def temp_config_dir(tmpdir):
    """
    Create a temporary config directory.
    
    Args:
        tmpdir: Pytest fixture for temporary directory
        
    Returns:
        Path to temporary config directory
    """
    config_dir = tmpdir.mkdir("stacking_sats_config")
    return str(config_dir)


@pytest.fixture
def temp_data_dir(tmpdir):
    """
    Create a temporary data directory.
    
    Args:
        tmpdir: Pytest fixture for temporary directory
        
    Returns:
        Path to temporary data directory
    """
    data_dir = tmpdir.mkdir("stacking_sats_data")
    return str(data_dir) 