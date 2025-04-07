import pytest
import pandas as pd
import numpy as np
import datetime

@pytest.fixture
def sample_price_data():
    """Create a sample price DataFrame for testing."""
    # Create date range for 2 cycles (8 years)
    dates = pd.date_range(start='2013-01-01', end='2020-12-31', freq='D')
    
    # Create price data with some realistic patterns
    # Cycle 1: 2013-2016 - Bull to bear
    # Cycle 2: 2017-2020 - Another bull to bear
    prices = []
    
    for dt in dates:
        year = dt.year
        day_of_year = dt.dayofyear
        
        # Create some cyclical patterns
        if year in [2013, 2017]:  # Early bull years
            base = 100 * (1 + 0.001 * day_of_year)
        elif year in [2014, 2018]:  # Late bull years
            base = 500 * (1 + 0.0005 * day_of_year)
        elif year in [2015, 2019]:  # Early bear years
            base = 800 * (1 - 0.0003 * day_of_year)
        else:  # Late bear years
            base = 400 * (1 - 0.0001 * day_of_year)
            
        # Add some noise
        noise = np.random.normal(0, 0.02)
        price = base * (1 + noise)
        prices.append(max(10, price))  # Ensure no negative prices
    
    # Create DataFrame
    df = pd.DataFrame({
        'btc_close': prices
    }, index=dates)
    
    return df

@pytest.fixture
def backtest_config():
    """Configuration parameters for backtest."""
    return {
        'BACKTEST_START': '2013-01-01',
        'BACKTEST_END': '2020-12-31',
        'ALPHA': 1.25,
        'REBALANCE_WINDOW': 730,  # Two years
        'MIN_WEIGHT': 1e-4
    } 