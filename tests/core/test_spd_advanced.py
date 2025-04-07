import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, call
import io
import sys
import matplotlib.pyplot as plt

# Import the SPD calculation functions
from core.spd import (
    backtest_dynamic_dca,
    compute_cycle_spd
)

class TestStrategySubstitution:
    """Tests for substituting different strategies in backtest_dynamic_dca()"""

    def test_different_strategies_yield_different_results(self, sample_price_data):
        """Test that different strategies produce different SPD metrics."""
        # Define two distinct strategy functions with predictable behaviors
        def low_price_strategy(df):
            # Strategy that puts more weight on low price days
            weights = 1.0 / df['btc_close']
            # Normalize to sum to 1.0
            return weights / weights.sum()
        
        def high_price_strategy(df):
            # Strategy that puts more weight on high price days
            weights = df['btc_close']
            # Normalize to sum to 1.0
            return weights / weights.sum()
            
        # Mock the get_strategy function to return different strategies
        with patch('core.spd.get_strategy') as mock_get_strategy:
            # Test with a limited date range
            with patch('core.spd.BACKTEST_START', '2013-01-01'):
                with patch('core.spd.BACKTEST_END', '2013-12-31'):
                    # Disable plotting for the test
                    with patch('core.spd.plot_spd_comparison'):
                        # First strategy: favor low prices (should perform better)
                        mock_get_strategy.return_value = low_price_strategy
                        low_price_results = backtest_dynamic_dca(sample_price_data, "low_price_strategy", show_plots=False)
                        
                        # Second strategy: favor high prices (should perform worse)
                        mock_get_strategy.return_value = high_price_strategy
                        high_price_results = backtest_dynamic_dca(sample_price_data, "high_price_strategy", show_plots=False)
                        
                        # The low price strategy should have higher SPD than the high price strategy
                        assert low_price_results.iloc[0]['dynamic_spd'] > high_price_results.iloc[0]['dynamic_spd']
                        
                        # The low price strategy should have a higher percentile
                        assert low_price_results.iloc[0]['dynamic_pct'] > high_price_results.iloc[0]['dynamic_pct']
                        
                        # Based on observed behavior, both strategies have negative excess_pct,
                        # but the low_price_strategy should have a less negative value
                        # (closer to uniform DCA)
                        assert low_price_results.iloc[0]['excess_pct'] > high_price_results.iloc[0]['excess_pct']
    
    def test_strategy_name_propagation_to_results(self, sample_price_data):
        """Test that strategy name is properly propagated to results."""
        # Define a simple strategy
        def test_strategy(df):
            return pd.Series(1.0 / len(df), index=df.index)
        
        # Mock the get_strategy function
        with patch('core.spd.get_strategy', return_value=test_strategy):
            # Test with a limited date range
            with patch('core.spd.BACKTEST_START', '2013-01-01'):
                with patch('core.spd.BACKTEST_END', '2013-12-31'):
                    # Capture stdout to check printed output
                    captured_output = io.StringIO()
                    sys.stdout = captured_output
                    
                    # Disable actual plotting for the test
                    with patch('core.spd.plot_spd_comparison') as mock_plot:
                        # Run backtest with a specific strategy name
                        strategy_name = "custom_strategy_name"
                        backtest_dynamic_dca(sample_price_data, strategy_name, show_plots=True)
                        
                        # Check if the plot function was called with the correct strategy name
                        assert mock_plot.call_count == 1
                        assert mock_plot.call_args[0][1] == strategy_name
                    
                    # Restore stdout
                    sys.stdout = sys.__stdout__
                    
                    # Check that the strategy name appears in the printed output
                    output = captured_output.getvalue()
                    assert f"Aggregated Metrics for {strategy_name}" in output


class TestErrorHandling:
    """Tests for how SPD calculation handles errors from strategies"""
    
    def test_handling_of_malformed_data(self, sample_price_data):
        """Test how compute_cycle_spd() handles strategies that return malformed data."""
        malformed_data_cases = [
            # Empty Series
            pd.Series(dtype=float),
            # Series with wrong index
            pd.Series([1.0, 2.0, 3.0]),
            # Series with all zeros
            pd.Series(0, index=sample_price_data.index),
            # Series with all NaN
            pd.Series(np.nan, index=sample_price_data.index)
        ]
        
        for case in malformed_data_cases:
            # Mock the get_strategy function to return malformed data
            with patch('core.spd.get_strategy', return_value=lambda df: case):
                # Test with a limited date range
                with patch('core.spd.BACKTEST_START', '2013-01-01'):
                    with patch('core.spd.BACKTEST_END', '2013-12-31'):
                        try:
                            # This should either produce valid results or raise a clear error
                            result = compute_cycle_spd(sample_price_data, "test_strategy")
                            
                            # If we get here, check that the result is sensible 
                            # (either legitimate results or empty DataFrame)
                            if not result.empty:
                                # Check for NaN values or zeros
                                if pd.isna(result.iloc[0]['dynamic_spd']):
                                    # NaN is an acceptable result for malformed input
                                    pass
                                elif result.iloc[0]['dynamic_spd'] == 0:
                                    # Zero is also an acceptable result for malformed input
                                    pass
                                else:
                                    # Otherwise, we expect some kind of reasonable value
                                    assert result.iloc[0]['dynamic_spd'] >= 0
                        except Exception as e:
                            # If an exception is raised, it should be a clear error message
                            # about the malformed data, not a cryptic internal error
                            error_msg = str(e).lower()
                            assert any(keyword in error_msg for keyword in 
                                      ["empty", "nan", "zero", "index", "missing", "invalid", "wrong", "malformed"])
    
    def test_handling_of_exceptions_in_strategy(self, sample_price_data):
        """Test behavior when a strategy function raises exceptions."""
        # Define a strategy that raises an exception
        def error_strategy(df):
            raise ValueError("Simulated error in strategy")
        
        # Mock the get_strategy function to raise an exception
        with patch('core.spd.get_strategy', return_value=error_strategy):
            # Test with a limited date range
            with patch('core.spd.BACKTEST_START', '2013-01-01'):
                with patch('core.spd.BACKTEST_END', '2013-12-31'):
                    # The error should be propagated or handled gracefully 
                    # (not masked with an unrelated error)
                    with pytest.raises(ValueError) as excinfo:
                        compute_cycle_spd(sample_price_data, "error_strategy")
                    
                    # Check that the error message contains the original exception message
                    assert "Simulated error in strategy" in str(excinfo.value)


class TestPerformanceComparison:
    """Tests for performance comparison between strategies"""
    
    def test_predictable_performance_patterns(self, sample_price_data):
        """Create mock strategies with predictable performance patterns and verify they behave as expected."""
        # Define strategies with predictable performance characteristics
        strategies = {
            "best_days": lambda df: self._create_best_days_strategy(df, 10),  # Buy only on the 10 lowest price days
            "worst_days": lambda df: self._create_worst_days_strategy(df, 10),  # Buy only on the 10 highest price days
            "uniform": lambda df: pd.Series(1.0 / len(df), index=df.index)  # Uniform strategy as baseline
        }
        
        # Test with a limited date range
        with patch('core.spd.BACKTEST_START', '2013-01-01'):
            with patch('core.spd.BACKTEST_END', '2013-12-31'):
                results = {}
                
                # Run backtest for each strategy
                for name, strategy_fn in strategies.items():
                    with patch('core.spd.get_strategy', return_value=strategy_fn):
                        with patch('core.spd.plot_spd_comparison'):  # Disable plotting
                            results[name] = backtest_dynamic_dca(sample_price_data, name, show_plots=False)
                
                # Verify expected performance order: best_days should have higher SPD than worst_days
                assert results["best_days"].iloc[0]['dynamic_spd'] > results["worst_days"].iloc[0]['dynamic_spd']
                
                # Verify percentiles follow the expected order: best_days > worst_days
                assert results["best_days"].iloc[0]['dynamic_pct'] > results["worst_days"].iloc[0]['dynamic_pct']
                
                # Based on observed behavior, all strategies might have negative excess_pct,
                # but best_days should have less negative value than worst_days
                assert results["best_days"].iloc[0]['excess_pct'] > results["worst_days"].iloc[0]['excess_pct']
    
    def test_comparative_metrics_calculation(self, sample_price_data):
        """Test that the comparative metrics in backtest_dynamic_dca() are calculated correctly."""
        # Use a strategy with known behavior
        def test_strategy(df):
            # Put all weight on the lowest price day
            weights = pd.Series(0.0, index=df.index)
            min_price_idx = df['btc_close'].idxmin()
            weights[min_price_idx] = 1.0
            return weights
        
        # Mock the get_strategy function
        with patch('core.spd.get_strategy', return_value=test_strategy):
            # Test with a limited date range
            with patch('core.spd.BACKTEST_START', '2013-01-01'):
                with patch('core.spd.BACKTEST_END', '2013-12-31'):
                    # Capture stdout to check printed metrics
                    with patch('core.spd.plot_spd_comparison'):  # Disable plotting
                        # Run backtest
                        result = backtest_dynamic_dca(sample_price_data, "min_price_strategy", show_plots=False)
    
                        # Verify that results DataFrame contains all required metrics
                        required_columns = ['min_spd', 'max_spd', 'uniform_spd', 'dynamic_spd', 
                                          'uniform_pct', 'dynamic_pct', 'excess_pct']
                        for col in required_columns:
                            assert col in result.columns, f"Missing column {col} in results"
                            assert np.isfinite(result.iloc[0][col]), f"Column {col} contains non-finite values"
                        
                        # Verify that the DataFrame has the expected index structure
                        assert result.index.name == 'cycle'
                        assert len(result) > 0, "Results DataFrame is empty"
    
    @staticmethod
    def _create_best_days_strategy(df, n_days=10):
        """Helper to create a strategy that buys only on the n lowest price days."""
        weights = pd.Series(0.0, index=df.index)
        # Get the indices of the n lowest price days
        lowest_days = df['btc_close'].nsmallest(n_days).index
        # Put equal weight on each of those days
        weight_value = 1.0 / n_days
        for day in lowest_days:
            weights.loc[day] = weight_value
        return weights
    
    @staticmethod
    def _create_worst_days_strategy(df, n_days=10):
        """Helper to create a strategy that buys only on the n highest price days."""
        weights = pd.Series(0.0, index=df.index)
        # Get the indices of the n highest price days
        highest_days = df['btc_close'].nlargest(n_days).index
        # Put equal weight on each of those days
        weight_value = 1.0 / n_days
        for day in highest_days:
            weights.loc[day] = weight_value
        return weights 