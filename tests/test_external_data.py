import unittest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os
import importlib
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies.utils import load_strategy

try:
    # Try to import our strategy directly
    from submit_strategies.external_data_gold_strategy import ExternalDataGoldStrategy
except ImportError:
    # If import fails, it will be handled in the tests
    pass

class ExternalDataStrategyTests(unittest.TestCase):
    """Tests for strategies that use external data sources."""
    
    def setUp(self):
        """Set up test data that mimics BTC price data."""
        # Create a date range for testing
        start_date = pd.to_datetime(BACKTEST_START)
        end_date = pd.to_datetime(BACKTEST_END)
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Create a fake price dataframe with just the essential column
        self.test_data = pd.DataFrame(
            index=date_range,
            data={
                'btc_close': np.linspace(10000, 50000, len(date_range))
            }
        )
    
    @patch('pandas_datareader.data.get_data_yahoo')
    def test_strategy_handles_external_data_success(self, mock_get_data_yahoo):
        """Test that a strategy can successfully use external data."""
        # Set up mock for external data API
        mock_data = pd.DataFrame(
            index=self.test_data.index,
            data={
                'Close': np.linspace(100, 200, len(self.test_data)),
                'Open': np.linspace(99, 199, len(self.test_data)),
                'High': np.linspace(101, 201, len(self.test_data)),
                'Low': np.linspace(98, 198, len(self.test_data)),
                'Volume': np.linspace(1000, 2000, len(self.test_data)),
            }
        )
        mock_get_data_yahoo.return_value = mock_data
        
        try:
            # Use our actual strategy instead of the mock
            strategy = ExternalDataGoldStrategy()
            weights = strategy.construct_features(self.test_data)
            weights = strategy.compute_weights(weights)
        except Exception as e:
            self.fail(f"Strategy execution raised an exception: {e}")
        
        # Validate the results
        self.assertEqual(len(weights), len(self.test_data.loc[BACKTEST_START:BACKTEST_END]))
        self.assertTrue(all(weights >= 0))  # Weights should be non-negative
        
        # Check that weights are properly normalized by cycle
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = weights.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        for cycle, group in weights.groupby(cycle_labels):
            self.assertAlmostEqual(group.sum(), 1.0, places=4)
    
    @patch('pandas_datareader.data.get_data_yahoo')
    def test_strategy_handles_external_data_failure(self, mock_get_data_yahoo):
        """Test that a strategy gracefully handles failure to fetch external data."""
        # Simulate API failure
        mock_get_data_yahoo.side_effect = Exception("API Connection Error")
        
        try:
            # Use our actual strategy instead of the mock
            strategy = ExternalDataGoldStrategy()
            df = strategy.construct_features(self.test_data)
            weights = strategy.compute_weights(df)
        except Exception as e:
            self.fail(f"Strategy failed to handle API error: {e}")
        
        # Validate the results
        self.assertEqual(len(weights), len(self.test_data.loc[BACKTEST_START:BACKTEST_END]))
        self.assertTrue(all(weights >= 0))  # Weights should be non-negative
        
        # Check that weights are properly normalized by cycle
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = weights.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        for cycle, group in weights.groupby(cycle_labels):
            self.assertAlmostEqual(group.sum(), 1.0, places=4)
    
    def test_strategy_execution_time(self):
        """Test that strategies with external data complete within reasonable time."""
        # This test would load actual strategies and enforce a time limit
        max_execution_time = 30  # seconds
        
        try:
            # Time the execution of our strategy
            start_time = datetime.now()
            
            strategy = ExternalDataGoldStrategy()
            df = strategy.construct_features(self.test_data)
            weights = strategy.compute_weights(df)
            
            execution_time = (datetime.now() - start_time).total_seconds()
        except Exception as e:
            self.fail(f"Strategy execution failed: {e}")
        
        # Assert that execution was within time limit
        self.assertLess(execution_time, max_execution_time)
        
        # Check basic properties of the result
        self.assertEqual(len(weights), len(self.test_data.loc[BACKTEST_START:BACKTEST_END]))
        self.assertTrue(all(weights >= 0)) 