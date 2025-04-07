import pytest
import pandas as pd
import numpy as np
import time
import matplotlib
import matplotlib.pyplot as plt
from unittest.mock import patch
import gc
import psutil
import os
import sys

# Import the functions to benchmark
from core.spd import compute_cycle_spd, backtest_dynamic_dca

class TestBacktestPerformance:
    """Tests to measure the performance of the backtest process"""
    
    def test_backtest_execution_time(self, sample_price_data):
        """Measure execution time of backtest_dynamic_dca with different strategies."""
        strategies = {
            "uniform": lambda df: pd.Series(1.0 / len(df), index=df.index),
            "inverse_price": lambda df: (1.0 / df['btc_close']) / (1.0 / df['btc_close']).sum(),
            "price_weighted": lambda df: df['btc_close'] / df['btc_close'].sum()
        }
        
        # Use a limited date range for faster testing
        with patch('core.spd.BACKTEST_START', '2013-01-01'):
            with patch('core.spd.BACKTEST_END', '2016-12-31'):
                with patch('core.spd.plot_spd_comparison'):  # Disable plotting
                    results = {}
                    
                    for name, strategy_fn in strategies.items():
                        # Setup
                        with patch('core.spd.get_strategy', return_value=strategy_fn):
                            # Force garbage collection before timing
                            gc.collect()
                            
                            # Measure execution time
                            start_time = time.time()
                            backtest_dynamic_dca(sample_price_data, name, show_plots=False)
                            execution_time = time.time() - start_time
                            
                            # Store result
                            results[name] = execution_time
                    
                    # Print performance results
                    print("\nBacktest Execution Times:")
                    for name, exec_time in results.items():
                        print(f"  {name}: {exec_time:.6f} seconds")
                    
                    # Ensure all strategies complete in a reasonable time
                    # This is a very rough benchmark - adjust thresholds as needed
                    for name, exec_time in results.items():
                        assert exec_time < 5.0, f"Strategy {name} took too long to execute"
    
    def test_backtest_memory_usage(self, sample_price_data):
        """Measure memory usage of backtest_dynamic_dca."""
        def get_memory_usage():
            """Get current memory usage of this process in MB."""
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        
        # Define a strategy
        def test_strategy(df):
            return pd.Series(1.0 / len(df), index=df.index)
        
        # Use a limited date range for faster testing
        with patch('core.spd.BACKTEST_START', '2013-01-01'):
            with patch('core.spd.BACKTEST_END', '2016-12-31'):
                with patch('core.spd.get_strategy', return_value=test_strategy):
                    with patch('core.spd.plot_spd_comparison'):  # Disable plotting
                        # Force garbage collection and measure initial memory
                        gc.collect()
                        initial_memory = get_memory_usage()
                        
                        # Run backtest
                        backtest_dynamic_dca(sample_price_data, "test_strategy", show_plots=False)
                        
                        # Force collection again and measure final memory
                        gc.collect()
                        final_memory = get_memory_usage()
                        
                        # Calculate memory change
                        memory_change = final_memory - initial_memory
                        
                        print(f"\nMemory Usage:")
                        print(f"  Initial: {initial_memory:.2f} MB")
                        print(f"  Final: {final_memory:.2f} MB")
                        print(f"  Change: {memory_change:.2f} MB")
                        
                        # Check memory leak (allowing for some overhead)
                        # This threshold might need adjustment based on your environment
                        assert memory_change < 50.0, "Possible memory leak detected"
    
    def test_backtest_scaling_with_data_size(self, sample_price_data):
        """Test how backtest performance scales with increasing data size."""
        # Define a simple uniform strategy
        def uniform_strategy(df):
            return pd.Series(1.0 / len(df), index=df.index)
        
        # Use different data size samples
        ratios = [0.25, 0.5, 0.75, 1.0]
        execution_times = []
        
        with patch('core.spd.get_strategy', return_value=uniform_strategy):
            with patch('core.spd.plot_spd_comparison'):  # Disable plotting
                for ratio in ratios:
                    # Create a subset of the data
                    size = int(len(sample_price_data) * ratio)
                    subset_data = sample_price_data.iloc[:size].copy()
                    
                    # Define date range based on subset data
                    start_date = subset_data.index[0].strftime('%Y-%m-%d')
                    end_date = subset_data.index[-1].strftime('%Y-%m-%d')
                    
                    with patch('core.spd.BACKTEST_START', start_date):
                        with patch('core.spd.BACKTEST_END', end_date):
                            # Force garbage collection before timing
                            gc.collect()
                            
                            # Measure execution time
                            start_time = time.time()
                            backtest_dynamic_dca(subset_data, "uniform", show_plots=False)
                            execution_time = time.time() - start_time
                            
                            execution_times.append(execution_time)
        
        # Print scaling results
        print("\nBacktest Scaling with Data Size:")
        for i, ratio in enumerate(ratios):
            print(f"  {ratio*100:.0f}% data: {execution_times[i]:.6f} seconds")
        
        # Check that execution time scales reasonably with data size
        # We expect time to increase somewhat linearly with data size
        # but not exponentially (which would indicate poor scaling)
        if execution_times[0] > 0:  # Avoid division by zero
            scaling_factor = execution_times[-1] / execution_times[0]
            expected_factor = ratios[-1] / ratios[0]
            
            # Allow some overhead, but scaling should not be dramatically worse than linear
            assert scaling_factor < expected_factor * 3.0, "Backtest does not scale well with data size"
    
    def test_backtest_with_plotting_overhead(self, sample_price_data):
        """Measure the overhead added by plot generation."""
        def uniform_strategy(df):
            return pd.Series(1.0 / len(df), index=df.index)
        
        with patch('core.spd.get_strategy', return_value=uniform_strategy):
            with patch('core.spd.BACKTEST_START', '2013-01-01'):
                with patch('core.spd.BACKTEST_END', '2016-12-31'):
                    # First, run without plots
                    with patch('core.spd.plot_spd_comparison'):  # Disable plotting
                        gc.collect()
                        start_time = time.time()
                        backtest_dynamic_dca(sample_price_data, "uniform", show_plots=False)
                        no_plot_time = time.time() - start_time
                    
                    # Next, run with plots but redirect to a non-display backend
                    # Save the current backend
                    current_backend = matplotlib.get_backend()
                    matplotlib.use('Agg')  # Non-interactive backend
                    
                    gc.collect()
                    start_time = time.time()
                    with patch('matplotlib.pyplot.show'):  # Patch plt.show to avoid display
                        backtest_dynamic_dca(sample_price_data, "uniform", show_plots=True)
                    with_plot_time = time.time() - start_time
                    
                    # Restore the backend
                    plt.close('all')  # Explicitly close all figures
                    matplotlib.use(current_backend)
                    
                    # Calculate overhead
                    plot_overhead = with_plot_time - no_plot_time
                    overhead_percentage = (plot_overhead / no_plot_time) * 100 if no_plot_time > 0 else 0
                    
                    print(f"\nPlotting Overhead:")
                    print(f"  Without plots: {no_plot_time:.6f} seconds")
                    print(f"  With plots: {with_plot_time:.6f} seconds")
                    print(f"  Overhead: {plot_overhead:.6f} seconds ({overhead_percentage:.2f}%)")
                    
                    # When dealing with very small base times, percentage can be misleading
                    # So check absolute overhead instead when base time is very small
                    if no_plot_time < 0.01:  # If base time is very small (less than 10ms)
                        assert plot_overhead < 0.5, "Plotting overhead is excessively high in absolute terms"
                        print("  Base time is very small, checking absolute overhead instead of percentage")
                    else:
                        # Plotting should add some overhead, but not extremely high
                        assert overhead_percentage < 200.0, "Plotting overhead is excessively high"
    
    @pytest.mark.skipif(sys.platform != "linux", reason="Profiling test designed for Linux")
    def test_cpu_profiling(self, sample_price_data):
        """Profile CPU usage during backtest execution (Linux only)."""
        try:
            import cProfile
            import pstats
            from io import StringIO
        except ImportError:
            pytest.skip("cProfile or StringIO not available")
        
        def uniform_strategy(df):
            return pd.Series(1.0 / len(df), index=df.index)
        
        with patch('core.spd.get_strategy', return_value=uniform_strategy):
            with patch('core.spd.BACKTEST_START', '2013-01-01'):
                with patch('core.spd.BACKTEST_END', '2016-12-31'):
                    with patch('core.spd.plot_spd_comparison'):  # Disable plotting
                        # Set up profiler
                        pr = cProfile.Profile()
                        pr.enable()
                        
                        # Run backtest
                        backtest_dynamic_dca(sample_price_data, "uniform", show_plots=False)
                        
                        # Stop profiler
                        pr.disable()
                        
                        # Get stats
                        s = StringIO()
                        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
                        ps.print_stats(10)  # Print top 10 functions by cumulative time
                        
                        print("\nCPU Profiling Results (Top 10 functions):")
                        print(s.getvalue())
                        
                        # No assertions here, this is purely informational 