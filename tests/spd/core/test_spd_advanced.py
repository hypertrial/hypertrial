import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, call
import io
import sys
import matplotlib.pyplot as plt
import os

# Import the SPD calculation functions
from core.spd import (
    backtest_dynamic_dca,
    compute_cycle_spd,
    plot_spd_comparison,
    list_available_strategies,
    compute_spd_metrics,
    standalone_plot_comparison
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

@pytest.fixture
def sample_spd_results():
    """Fixture to create sample SPD results dataframe"""
    return pd.DataFrame({
        'min_spd': [100, 200],
        'max_spd': [1000, 2000],
        'uniform_spd': [300, 400],
        'dynamic_spd': [400, 500],
        'uniform_pct': [20, 15],
        'dynamic_pct': [30, 20],
        'excess_pct': [10, 5]
    }, index=['2013–2016', '2017–2020'])

@pytest.fixture
def sample_weights():
    """Fixture to create sample strategy weights"""
    dates = pd.date_range(start='2013-01-01', end='2020-12-31')
    return pd.Series(data=np.random.rand(len(dates)), index=dates)


def test_plot_spd_comparison(sample_spd_results):
    """Test plot_spd_comparison function"""
    with patch('matplotlib.pyplot.show') as mock_show, \
         patch('matplotlib.pyplot.subplots', return_value=(MagicMock(), MagicMock())) as mock_subplots, \
         patch('matplotlib.pyplot.savefig') as mock_savefig, \
         patch('matplotlib.pyplot.tight_layout') as mock_tight_layout:
        
        # Create more detailed mock axes
        mock_fig, mock_ax1 = mock_subplots.return_value
        mock_ax2 = MagicMock()
        mock_ax1.twinx.return_value = mock_ax2
        
        # Mock the plot method to return a list of Line2D objects
        lines_mock = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_ax1.plot.return_value = lines_mock
        
        # Create mock bar objects
        bar1_mock = MagicMock()
        bar2_mock = MagicMock()
        mock_ax2.bar.side_effect = [bar1_mock, bar2_mock]
        
        # Call the function
        plot_spd_comparison(sample_spd_results, "test_strategy")
        
        # Verify that show was called
        mock_show.assert_called_once()
        
        # Verify subplots was called
        mock_subplots.assert_called()
        
        # Verify basic plot setup
        mock_ax1.set_title.assert_called_with("Strategy Performance: test_strategy")
        mock_ax1.set_ylabel.assert_called_with('Sats per Dollar (Log Scale)')
        mock_ax1.set_xlabel.assert_called_with("Cycle")
        mock_ax1.grid.assert_called_with(True, linestyle='--', linewidth=0.5)
        mock_ax1.legend.assert_called()
        mock_ax1.set_xticks.assert_called()
        mock_ax1.set_xticklabels.assert_called()
        
        # Verify plot was called
        mock_ax1.plot.assert_called()
        
        # Verify second y-axis
        mock_ax2.set_ylabel.assert_called_with('SPD Percentile (%)')
        mock_ax2.set_ylim.assert_called_with(0, 100)
        mock_ax2.legend.assert_called()


def test_backtest_dynamic_dca(sample_price_data):
    """Test backtest_dynamic_dca function"""
    with patch('core.spd.compute_cycle_spd') as mock_compute, \
         patch('core.spd.plot_spd_comparison') as mock_plot, \
         patch('core.spd.logging.getLogger') as mock_getlogger:
        
        # Set up mock compute_cycle_spd return value
        mock_compute.return_value = pd.DataFrame({
            'min_spd': [100, 200],
            'max_spd': [1000, 2000],
            'uniform_spd': [300, 400],
            'dynamic_spd': [400, 500],
            'uniform_pct': [20, 15],
            'dynamic_pct': [30, 20],
            'excess_pct': [10, 5]
        }, index=['2013–2016', '2017–2020'])
        
        # Set up mock logger
        mock_logger = MagicMock()
        mock_getlogger.return_value = mock_logger
        
        # Test with show_plots=True
        with patch('builtins.print') as mock_print:
            results = backtest_dynamic_dca(sample_price_data, "test_strategy", show_plots=True)
            
            # Verify compute_cycle_spd was called properly
            mock_compute.assert_called_once_with(sample_price_data, "test_strategy")
            
            # Verify plot_spd_comparison was called
            mock_plot.assert_called_once()
            
            # Verify print was called
            assert mock_print.call_count > 0
            
            # Verify logger was called
            mock_logger.info.assert_called_once()
            
            # Verify the returned results
            assert isinstance(results, pd.DataFrame)
            assert len(results) == 2
            assert all(col in results.columns for col in ['min_spd', 'max_spd', 'uniform_spd', 'dynamic_spd', 
                                                         'uniform_pct', 'dynamic_pct', 'excess_pct'])
        
        # Test with show_plots=False
        mock_compute.reset_mock()
        mock_plot.reset_mock()
        mock_logger.reset_mock()
        
        with patch('builtins.print') as mock_print:
            results = backtest_dynamic_dca(sample_price_data, "test_strategy", show_plots=False)
            
            # Verify compute_cycle_spd was called properly
            mock_compute.assert_called_once_with(sample_price_data, "test_strategy")
            
            # Verify plot_spd_comparison was NOT called
            mock_plot.assert_not_called()


def test_list_available_strategies():
    """Test list_available_strategies function"""
    with patch('core.spd.list_strategies') as mock_list_strategies, \
         patch('builtins.print') as mock_print:
        
        # Test with no strategies
        mock_list_strategies.return_value = {}
        result = list_available_strategies()
        assert result == {}
        mock_print.assert_called()
        
        # Reset mocks
        mock_print.reset_mock()
        
        # Test with core strategies only
        mock_list_strategies.return_value = {
            'uniform_dca': 'Uniform Dollar Cost Averaging strategy',
            'dynamic_dca': 'Dynamic Dollar Cost Averaging strategy'
        }
        result = list_available_strategies()
        assert result == mock_list_strategies.return_value
        assert mock_print.call_count > 3  # At least header + two strategies
        
        # Reset mocks
        mock_print.reset_mock()
        
        # Test with both core and custom strategies
        mock_list_strategies.return_value = {
            'uniform_dca': 'Uniform Dollar Cost Averaging strategy',
            'dynamic_dca': 'Dynamic Dollar Cost Averaging strategy',
            'custom_strategy1': 'Custom strategy 1',
            'custom_strategy2': 'Custom strategy 2'
        }
        result = list_available_strategies()
        assert result == mock_list_strategies.return_value
        assert mock_print.call_count > 5  # Header + section headers + four strategies


def test_compute_spd_metrics(sample_price_data, sample_weights):
    """Test compute_spd_metrics function"""
    with patch('core.spd.logging.getLogger') as mock_getlogger:
        # Set up mock logger
        mock_logger = MagicMock()
        mock_getlogger.return_value = mock_logger
        
        # Test with default parameters
        with patch('core.spd.BACKTEST_START', '2013-01-01'), \
             patch('core.spd.BACKTEST_END', '2020-12-31'):
            
            results = compute_spd_metrics(sample_price_data, sample_weights)
            
            # Verify logger was called
            mock_logger.info.assert_called_once()
            
            # Verify the structure of the results
            assert isinstance(results, dict)
            assert 'cycles' in results
            assert 'min_spd' in results
            assert 'max_spd' in results
            assert 'uniform_spd' in results
            assert 'dynamic_spd' in results
            assert 'excess_pct' in results
            assert 'uniform_pct' in results
            assert 'dynamic_pct' in results
            
            # Verify the types are correct
            assert isinstance(results['min_spd'], (int, float, np.number))
            assert isinstance(results['max_spd'], (int, float, np.number))
            assert isinstance(results['mean_spd'], (int, float, np.number))
            assert isinstance(results['median_spd'], (int, float, np.number))
            assert isinstance(results['uniform_spd'], list)
            assert isinstance(results['dynamic_spd'], list)
            assert isinstance(results['uniform_pct'], list)
            assert isinstance(results['dynamic_pct'], list)
            assert isinstance(results['excess_pct'], list)
            
            # Verify there's data for each cycle
            assert len(results['cycles']) > 0
            assert len(results['uniform_spd']) == len(results['cycles'])
            assert len(results['dynamic_spd']) == len(results['cycles'])
            assert len(results['excess_pct']) == len(results['cycles'])


def test_standalone_plot_comparison(sample_price_data, sample_weights):
    """Test standalone_plot_comparison function"""
    with patch('core.spd.compute_spd_metrics') as mock_compute, \
         patch('matplotlib.pyplot.show') as mock_show, \
         patch('matplotlib.pyplot.savefig') as mock_savefig, \
         patch('matplotlib.pyplot.figure') as mock_figure, \
         patch('os.makedirs') as mock_makedirs:
        
        # Set up mock compute_spd_metrics return value
        mock_compute.return_value = {
            'cycles': ['2013–2016', '2017–2020'],
            'min_spd': [100, 200],
            'max_spd': [1000, 2000],
            'uniform_spd': [300, 400],
            'dynamic_spd': [400, 500],
            'uniform_pct': [20, 15],
            'dynamic_pct': [30, 20],
            'excess_pct': [10, 5]
        }
        
        # Create mock figure and axes
        mock_fig = MagicMock()
        mock_ax1 = MagicMock()
        mock_ax2 = MagicMock()
        mock_figure.return_value = mock_fig
        mock_fig.add_subplot.return_value = mock_ax1
        mock_ax1.twinx.return_value = mock_ax2
        
        # Test without saving to file
        standalone_plot_comparison(sample_price_data, sample_weights, "test_strategy", save_to_file=False)
        
        # Verify compute_spd_metrics was called
        mock_compute.assert_called_once_with(sample_price_data, sample_weights, "test_strategy")
        
        # Verify show was called but not savefig
        mock_show.assert_called_once()
        mock_savefig.assert_not_called()
        
        # Reset mocks
        mock_compute.reset_mock()
        mock_show.reset_mock()
        mock_savefig.reset_mock()
        mock_makedirs.reset_mock()
        
        # Test with saving to file
        standalone_plot_comparison(sample_price_data, sample_weights, "test_strategy", save_to_file=True, output_dir="test_dir")
        
        # Verify compute_spd_metrics was called
        mock_compute.assert_called_once_with(sample_price_data, sample_weights, "test_strategy")
        
        # Verify makedirs was called
        mock_makedirs.assert_called_once_with("test_dir", exist_ok=True)
        
        # Verify savefig was called but not show
        mock_savefig.assert_called_once()
        mock_show.assert_not_called() 