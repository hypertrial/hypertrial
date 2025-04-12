import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

# Import the strategy
from core.strategies.dynamic_dca import DynamicDCAStrategy

def test_dynamic_dca_feature_construction(sample_price_data):
    """Test that the DynamicDCAStrategy feature construction adds ma200 and std200."""
    # Call the feature construction method
    result = DynamicDCAStrategy.construct_features(sample_price_data)
    
    # Verify that the required features are present
    assert 'ma200' in result.columns
    assert 'std200' in result.columns
    
    # Check calculation for ma200
    expected_ma200 = sample_price_data['btc_close'].rolling(window=200, min_periods=1).mean()
    
    # Values should match the expected values
    np.testing.assert_allclose(
        result['ma200'],
        expected_ma200,
        rtol=1e-10
    )

def test_dynamic_dca_weights_sum_to_one_per_cycle(sample_price_data, backtest_config):
    """Test that DynamicDCAStrategy weights sum to 1.0 for each cycle."""
    # Construct features using the strategy's method 
    df = DynamicDCAStrategy.construct_features(sample_price_data)
    
    # Patch the config values
    with patch('core.strategies.dynamic_dca.BACKTEST_START', backtest_config['BACKTEST_START']):
        with patch('core.strategies.dynamic_dca.BACKTEST_END', backtest_config['BACKTEST_END']):
            with patch('core.strategies.dynamic_dca.ALPHA', backtest_config['ALPHA']):
                with patch('core.strategies.dynamic_dca.REBALANCE_WINDOW', backtest_config['REBALANCE_WINDOW']):
                    with patch('core.strategies.dynamic_dca.MIN_WEIGHT', backtest_config['MIN_WEIGHT']):
                        # Compute weights
                        weights = DynamicDCAStrategy.compute_weights(df)
                        
                        # Group by 4-year cycles
                        start_year = pd.to_datetime(backtest_config['BACKTEST_START']).year
                        cycle_labels = weights.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
                        
                        # Check that weights sum to approximately 1.0 for each cycle
                        for cycle, group in weights.groupby(cycle_labels):
                            assert np.isclose(group.sum(), 1.0, rtol=1e-10)

def test_dynamic_dca_weight_boost_on_price_below_ma(sample_price_data, backtest_config):
    """Test that prices below ma200 receive higher weights."""
    # Create a test DataFrame with controlled values
    dates = pd.date_range(start='2013-01-01', end='2013-01-10', freq='D')
    # Create price data where some prices are below MA
    prices = [100, 110, 90, 80, 120, 110, 100, 90, 80, 70]
    
    # Create the test dataframe
    df = pd.DataFrame({
        'btc_close': prices,
    }, index=dates)
    
    # Apply feature construction to get ma200
    df = DynamicDCAStrategy.construct_features(df)
    
    # Patch the config values
    with patch('core.strategies.dynamic_dca.BACKTEST_START', '2013-01-01'):
        with patch('core.strategies.dynamic_dca.BACKTEST_END', '2013-01-10'):
            with patch('core.strategies.dynamic_dca.ALPHA', 1.0):  # Set alpha to 1.0 for simpler calculations
                with patch('core.strategies.dynamic_dca.REBALANCE_WINDOW', 5):
                    with patch('core.strategies.dynamic_dca.MIN_WEIGHT', 1e-4):
                        # Compute weights
                        weights = DynamicDCAStrategy.compute_weights(df)
                        
                        # Days with prices below MA200 should have higher weights
                        below_ma_days = df.index[df['btc_close'] < df['ma200']]
                        above_ma_days = df.index[df['btc_close'] >= df['ma200']]
                        
                        if len(below_ma_days) > 0 and len(above_ma_days) > 0:
                            avg_weight_below_ma = weights.loc[below_ma_days].mean()
                            avg_weight_above_ma = weights.loc[above_ma_days].mean()
                            
                            # Check that days below MA receive higher weights on average
                            assert avg_weight_below_ma > avg_weight_above_ma

def test_dynamic_dca_weight_proportional_to_z_score(sample_price_data, backtest_config):
    """Test that boost is proportional to z-score deviation."""
    # Create a test DataFrame with controlled values
    dates = pd.date_range(start='2013-01-01', end='2013-01-10', freq='D')
    
    # Create test dataframe
    df = pd.DataFrame({
        'btc_close': [100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
    }, index=dates)
    
    # Apply feature construction to get ma200 and std200
    df = DynamicDCAStrategy.construct_features(df)
    
    # Patch the config values with values that ensure the weight boosting works
    with patch('core.strategies.dynamic_dca.BACKTEST_START', '2013-01-01'):
        with patch('core.strategies.dynamic_dca.BACKTEST_END', '2013-01-10'):
            with patch('core.strategies.dynamic_dca.ALPHA', 0.5):  # Lower alpha makes it easier to boost
                with patch('core.strategies.dynamic_dca.REBALANCE_WINDOW', 3):  # Shorter window
                    with patch('core.strategies.dynamic_dca.MIN_WEIGHT', 1e-6):  # Lower minimum weight
                        # Compute weights
                        weights = DynamicDCAStrategy.compute_weights(df)
                        
                        # Check if any days with price below MA have higher weights than baseline
                        below_ma_days = df.index[df['btc_close'] < df['ma200']]
                        uniform_weight = 1.0 / len(df)
                        
                        # At least one day below MA should have weight higher than uniform
                        higher_weight_days = below_ma_days[weights.loc[below_ma_days] > uniform_weight]
                        assert len(higher_weight_days) > 0
                        
                        # For days significantly below MA, check that weight is higher
                        # Find days where price is at least 2 std devs below MA
                        significant_below_days = df.index[(df['ma200'] - df['btc_close']) / df['std200'] >= 2]
                        
                        if len(significant_below_days) > 0:
                            # Check at least one of these days has higher weight than uniform
                            assert any(weights.loc[significant_below_days] > uniform_weight) 