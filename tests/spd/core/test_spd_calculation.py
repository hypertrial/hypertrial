import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Import the SPD calculation functions
from core.spd import compute_cycle_spd

def test_spd_calculation_with_uniform_weights(sample_price_data):
    """Test that SPD calculation produces expected results with uniform weights."""
    # Mock the get_strategy function to return uniform weights
    with patch('core.spd.get_strategy') as mock_get_strategy:
        # Create uniform weights: each day gets 1/N weight
        def uniform_weights(df):
            # We need dates in the range of the test
            cycle_dates = df.loc['2013-01-01':'2016-12-31'].index
            N = len(cycle_dates)
            # Initialize all weights to 0
            weights = pd.Series(0.0, index=df.index)
            # Set weights for cycle_dates to 1/N
            weights.loc[cycle_dates] = 1.0 / N
            return weights.fillna(0)
        
        mock_get_strategy.return_value = uniform_weights
        
        # Patch the config values
        with patch('core.spd.BACKTEST_START', '2013-01-01'):
            with patch('core.spd.BACKTEST_END', '2016-12-31'):  # Just test first cycle
                # Compute SPD
                results = compute_cycle_spd(sample_price_data, "uniform_dca")
                
                # Check that there's one cycle
                assert len(results) == 1
                
                # Check cycle label
                assert results.index[0] == "2013–2016"
                
                # Test the calculation of min_spd and max_spd
                cycle_data = sample_price_data.loc['2013-01-01':'2016-12-31']
                cycle_high = cycle_data['btc_close'].max()
                cycle_low = cycle_data['btc_close'].min()
                expected_min_spd = (1 / cycle_high) * 1e8
                expected_max_spd = (1 / cycle_low) * 1e8
                
                assert np.isclose(results.iloc[0]['min_spd'], expected_min_spd, rtol=1e-10)
                assert np.isclose(results.iloc[0]['max_spd'], expected_max_spd, rtol=1e-10)
                
                # For the uniform SPD calculation, we calculate the mean of 1/price for all days in the cycle
                # This matches how the core.spd.compute_cycle_spd calculates it
                expected_uniform_spd = (1 / cycle_data['btc_close']).mean() * 1e8
                assert np.isclose(results.iloc[0]['uniform_spd'], expected_uniform_spd, rtol=1e-5)
                
                # The dynamic SPD should be similar to uniform SPD when weights are uniform
                weights = uniform_weights(sample_price_data)
                weight_sum = weights.loc[cycle_data.index].sum()
                if weight_sum > 0:  # Protect against division by zero
                    normalized_weights = weights.loc[cycle_data.index] / weight_sum
                    calc_dynamic_spd = ((normalized_weights / cycle_data['btc_close']).sum()) * 1e8
                    assert np.isclose(calc_dynamic_spd, results.iloc[0]['dynamic_spd'], rtol=1e-5)

def test_spd_calculation_with_dynamic_weights(sample_price_data):
    """Test that SPD calculation produces expected results with non-uniform weights."""
    # Mock the get_strategy function to return non-uniform weights
    with patch('core.spd.get_strategy') as mock_get_strategy:
        # Create dynamic weights: higher weights when price is low
        def dynamic_weights(df):
            # Simple inverse price weighting
            weights = 1 / df['btc_close']
            # Normalize to sum to 1.0 by cycle
            start_year = 2013
            cycle_labels = df.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
            normalized_weights = pd.Series(index=df.index, dtype=float)
            
            for cycle, group in df.groupby(cycle_labels):
                cycle_weights = weights.loc[group.index]
                normalized_weights.loc[group.index] = cycle_weights / cycle_weights.sum()
            
            return normalized_weights
        
        mock_get_strategy.return_value = dynamic_weights
        
        # Patch the config values
        with patch('core.spd.BACKTEST_START', '2013-01-01'):
            with patch('core.spd.BACKTEST_END', '2016-12-31'):  # Just test first cycle
                # Compute SPD
                results = compute_cycle_spd(sample_price_data, "dynamic_dca")
                
                # Check that dynamic SPD is greater than uniform SPD (buy more when price is low)
                assert results.iloc[0]['dynamic_spd'] > results.iloc[0]['uniform_spd']
                
                # Calculate expected SPD manually
                cycle_data = sample_price_data.loc['2013-01-01':'2016-12-31']
                weights = dynamic_weights(cycle_data)
                expected_dynamic_spd = ((weights / cycle_data['btc_close']).sum()) * 1e8
                
                assert np.isclose(results.iloc[0]['dynamic_spd'], expected_dynamic_spd, rtol=1e-10)

def test_cycle_boundary_calculations(sample_price_data):
    """Test that cycles are correctly calculated and bounded."""
    # Create a mock strategy function that returns uniform weights
    def uniform_weights(df):
        weights = pd.Series(index=df.index, dtype=float)
        start_year = 2013
        cycle_labels = df.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        for cycle, group in df.groupby(cycle_labels):
            N = len(group)
            weights.loc[group.index] = 1.0 / N
            
        return weights
    
    # Mock the get_strategy function
    with patch('core.spd.get_strategy') as mock_get_strategy:
        mock_get_strategy.return_value = uniform_weights
        
        # Test with a start date in the middle of the first year
        with patch('core.spd.BACKTEST_START', '2013-06-01'):
            with patch('core.spd.BACKTEST_END', '2020-12-31'):
                results = compute_cycle_spd(sample_price_data, "uniform_dca")
                
                # Should have 2 full 4-year cycles
                assert len(results) == 2
                
                # Check cycle labels
                assert results.index[0] == "2013–2017"
                assert results.index[1] == "2017–2020"

def test_spd_percentile_calculations(sample_price_data):
    """Test that SPD percentile is correctly calculated."""
    # Create a mock strategy function that returns uniform weights
    def uniform_weights(df):
        weights = pd.Series(index=df.index, dtype=float)
        start_year = 2013
        cycle_labels = df.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        for cycle, group in df.groupby(cycle_labels):
            N = len(group)
            weights.loc[group.index] = 1.0 / N
            
        return weights
    
    # Mock the get_strategy function
    with patch('core.spd.get_strategy') as mock_get_strategy:
        mock_get_strategy.return_value = uniform_weights
        
        # Test with a specific date range
        with patch('core.spd.BACKTEST_START', '2013-01-01'):
            with patch('core.spd.BACKTEST_END', '2016-12-31'):
                results = compute_cycle_spd(sample_price_data, "uniform_dca")
                
                # Calculate expected percentile manually
                min_spd = results.iloc[0]['min_spd']
                max_spd = results.iloc[0]['max_spd']
                uniform_spd = results.iloc[0]['uniform_spd']
                
                expected_uniform_pct = (uniform_spd - min_spd) / (max_spd - min_spd) * 100
                expected_dynamic_pct = expected_uniform_pct  # For uniform weights, these should be the same
                expected_excess_pct = 0.0
                
                assert np.isclose(results.iloc[0]['uniform_pct'], expected_uniform_pct, rtol=1e-10)
                assert np.isclose(results.iloc[0]['dynamic_pct'], expected_dynamic_pct, rtol=1e-10)
                assert np.isclose(results.iloc[0]['excess_pct'], expected_excess_pct, rtol=1e-10) 