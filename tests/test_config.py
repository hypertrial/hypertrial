import unittest
import re
from datetime import datetime

# Import the config module
from core import config

class TestConfig(unittest.TestCase):
    """Tests for configuration variables in core/config.py"""
    
    def test_required_config_constants_exist(self):
        """Test that all required configuration constants exist"""
        required_constants = [
            'BACKTEST_START',
            'BACKTEST_END',
            'ALPHA',
            'REBALANCE_WINDOW',
            'MIN_WEIGHT'
        ]
        
        for constant in required_constants:
            self.assertTrue(hasattr(config, constant), f"Missing required config constant: {constant}")
    
    def test_backtest_dates_format(self):
        """Test that backtest dates are in the correct format"""
        # Define the expected date format
        date_format = r'^\d{4}-\d{2}-\d{2}$'
        
        # Check BACKTEST_START is a valid date string
        self.assertTrue(re.match(date_format, config.BACKTEST_START), 
                      f"BACKTEST_START '{config.BACKTEST_START}' is not in YYYY-MM-DD format")
        
        # Check BACKTEST_END is a valid date string
        self.assertTrue(re.match(date_format, config.BACKTEST_END), 
                      f"BACKTEST_END '{config.BACKTEST_END}' is not in YYYY-MM-DD format")
    
    def test_backtest_dates_order(self):
        """Test that BACKTEST_END is after BACKTEST_START"""
        start_date = datetime.strptime(config.BACKTEST_START, "%Y-%m-%d")
        end_date = datetime.strptime(config.BACKTEST_END, "%Y-%m-%d")
        
        self.assertLess(start_date, end_date, "BACKTEST_START must be before BACKTEST_END")
    
    def test_alpha_value(self):
        """Test that ALPHA has a valid value"""
        self.assertIsInstance(config.ALPHA, (int, float), "ALPHA must be a number")
        self.assertGreater(config.ALPHA, 0, "ALPHA must be positive")
    
    def test_rebalance_window_value(self):
        """Test that REBALANCE_WINDOW has a valid value"""
        self.assertIsInstance(config.REBALANCE_WINDOW, int, "REBALANCE_WINDOW must be an integer")
        self.assertGreater(config.REBALANCE_WINDOW, 0, "REBALANCE_WINDOW must be positive")
    
    def test_min_weight_value(self):
        """Test that MIN_WEIGHT has a valid value"""
        self.assertIsInstance(config.MIN_WEIGHT, (int, float), "MIN_WEIGHT must be a number")
        self.assertGreaterEqual(config.MIN_WEIGHT, 0, "MIN_WEIGHT must be non-negative")
        self.assertLess(config.MIN_WEIGHT, 1, "MIN_WEIGHT must be less than 1")

if __name__ == "__main__":
    unittest.main() 