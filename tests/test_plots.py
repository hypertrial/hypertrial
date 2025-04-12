import unittest
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import os
import io
import sys
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Set non-interactive backend for testing
matplotlib.use('Agg')

# Import the plotting functions
from core.plots import (
    plot_price_vs_lookback_avg,
    plot_final_weights,
    plot_weight_sums_by_cycle,
    print_weight_sums_by_cycle
)
from core.config import BACKTEST_START, BACKTEST_END

class TestPlots(unittest.TestCase):
    """Tests for plotting functions in core/plots.py"""
    
    def setUp(self):
        """Set up test data for plotting"""
        # Create a sample DataFrame with BTC prices and moving averages
        dates = pd.date_range(start='2013-01-01', end='2024-12-31', freq='D')
        btc_prices = np.exp(np.linspace(np.log(10), np.log(50000), len(dates)))
        btc_prices = btc_prices * (1 + 0.1 * np.sin(np.linspace(0, 50, len(dates))))
        
        # Create DataFrame with BTC prices
        self.df = pd.DataFrame({
            'btc_close': btc_prices
        }, index=dates)
        
        # Add a moving average column
        self.df['ma_50'] = self.df['btc_close'].rolling(window=50, min_periods=1).mean()
        
        # Create sample weights
        weights = np.ones(len(dates)) / len(dates)
        # Add some variation to weights
        weights = weights * (1 + 0.5 * np.sin(np.linspace(0, 20, len(dates))))
        
        self.weights = pd.Series(weights, index=dates)
    
    def tearDown(self):
        """Clean up after tests"""
        # Close all plot figures
        plt.close('all')
    
    def test_plot_price_vs_lookback_avg(self):
        """Test plot_price_vs_lookback_avg function"""
        # Test without weights
        with patch('matplotlib.pyplot.show'):
            fig = plot_price_vs_lookback_avg(self.df)
            # Check that the plot was created
            self.assertIsNotNone(plt.gcf())
            # Should have at least 2 lines (price and MA)
            ax = plt.gca()
            self.assertGreaterEqual(len(ax.get_lines()), 2)
        
        # Test with weights
        with patch('matplotlib.pyplot.show'):
            fig = plot_price_vs_lookback_avg(self.df, self.weights)
            # Check that the plot was created
            self.assertIsNotNone(plt.gcf())
            # Should include a scatter plot for weights
            ax = plt.gca()
            scatter_plots = [c for c in ax.get_children() if isinstance(c, matplotlib.collections.PathCollection)]
            self.assertGreaterEqual(len(scatter_plots), 1)
    
    def test_plot_price_vs_lookback_avg_validation(self):
        """Test validation in plot_price_vs_lookback_avg function"""
        # Create a DataFrame without MA columns
        df_no_ma = self.df[['btc_close']].copy()
        
        # Should raise ValueError due to missing MA columns
        with self.assertRaises(ValueError):
            plot_price_vs_lookback_avg(df_no_ma)
    
    def test_plot_final_weights(self):
        """Test plot_final_weights function"""
        with patch('matplotlib.pyplot.show'):
            # Call the function
            plot_final_weights(self.weights)
            
            # Check that the plot was created
            self.assertIsNotNone(plt.gcf())
            
            # Should have at least one line per cycle
            ax = plt.gca()
            self.assertGreaterEqual(len(ax.get_lines()), 3)  # At least one line per cycle
    
    def test_print_weight_sums_by_cycle(self):
        """Test print_weight_sums_by_cycle function"""
        # Capture stdout to check output
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            # Call the function
            result = print_weight_sums_by_cycle(self.weights)
            
            # Check the output contains expected text
            output = captured_output.getvalue()
            self.assertIn("Weight sums by cycle", output)
            self.assertIn("2013–2016", output)
            
            # Check the returned DataFrame
            self.assertIsInstance(result, pd.Series)
            self.assertGreater(len(result), 0)
        finally:
            # Reset stdout
            sys.stdout = sys.__stdout__
    
    def test_plot_weight_sums_by_cycle(self):
        """Test plot_weight_sums_by_cycle function"""
        with patch('matplotlib.pyplot.show'), patch('core.plots.print_weight_sums_by_cycle', return_value=pd.Series([0.98, 1.02, 0.99], index=[0, 1, 2])):
            # Call the function
            plot_weight_sums_by_cycle(self.weights)
            
            # Check that the plot was created
            self.assertIsNotNone(plt.gcf())
            
            # Should have a bar chart
            ax = plt.gca()
            self.assertGreaterEqual(len(ax.containers), 1)
            
            # Should have a horizontal line at y=1.0
            lines = [line for line in ax.get_lines() if line.get_linestyle() == '--']
            self.assertGreaterEqual(len(lines), 1)

if __name__ == "__main__":
    unittest.main() 