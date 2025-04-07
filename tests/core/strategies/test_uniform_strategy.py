import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch

# Import the strategy
from core.strategies.uniform_dca import UniformDCAStrategy

def test_uniform_dca_feature_construction(sample_price_data):
    """Test that the UniformDCAStrategy feature construction works as expected."""
    # The UniformDCAStrategy doesn't add any features, so the output should be a copy
    result = UniformDCAStrategy.construct_features(sample_price_data)
    
    # Check that the result is a copy, not the same object
    assert result is not sample_price_data
    
    # Check that the result has the same data
    pd.testing.assert_frame_equal(result, sample_price_data)

def test_uniform_dca_weights_sum_to_one_per_cycle(sample_price_data, backtest_config):
    """Test that UniformDCAStrategy weights sum to 1.0 for each cycle."""
    # Patch the config values
    with patch('core.strategies.uniform_dca.BACKTEST_START', backtest_config['BACKTEST_START']):
        with patch('core.strategies.uniform_dca.BACKTEST_END', backtest_config['BACKTEST_END']):
            # Compute weights
            weights = UniformDCAStrategy.compute_weights(sample_price_data)
            
            # Check that weights exist for all dates in the backtest period
            backtest_dates = pd.date_range(
                start=backtest_config['BACKTEST_START'],
                end=backtest_config['BACKTEST_END'],
                freq='D'
            )
            assert all(date in weights.index for date in backtest_dates)
            
            # Group by 4-year cycles
            start_year = pd.to_datetime(backtest_config['BACKTEST_START']).year
            cycle_labels = weights.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
            
            # Check that weights sum to approximately 1.0 for each cycle
            for cycle, group in weights.groupby(cycle_labels):
                assert np.isclose(group.sum(), 1.0, rtol=1e-10)

def test_uniform_dca_weights_are_equal_within_cycle(sample_price_data, backtest_config):
    """Test that UniformDCAStrategy weights are equal within each cycle."""
    # Patch the config values
    with patch('core.strategies.uniform_dca.BACKTEST_START', backtest_config['BACKTEST_START']):
        with patch('core.strategies.uniform_dca.BACKTEST_END', backtest_config['BACKTEST_END']):
            # Compute weights
            weights = UniformDCAStrategy.compute_weights(sample_price_data)
            
            # Group by 4-year cycles
            start_year = pd.to_datetime(backtest_config['BACKTEST_START']).year
            cycle_labels = weights.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
            
            # Check that all weights within a cycle are equal
            for cycle, group in weights.groupby(cycle_labels):
                # All weights should be the same (1.0 / number of days in cycle)
                expected_weight = 1.0 / len(group)
                assert all(np.isclose(weight, expected_weight, rtol=1e-10) for weight in group) 