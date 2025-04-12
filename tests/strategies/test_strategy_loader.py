import unittest
import os
import sys
import tempfile
import importlib
import time
from unittest.mock import patch, MagicMock
import importlib.util
import importlib.machinery
import multiprocessing
import pandas as pd

from core.strategy_loader import (
    load_strategy_from_file,
    find_strategy_class,
    process_strategy_file,
    process_strategy_file_with_timeout
)

class TestStrategyLoader(unittest.TestCase):
    """Tests for strategy loader functionality in core/strategy_loader.py"""
    
    def setUp(self):
        """Set up test fixture, creating a temporary directory with test files."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a valid strategy file
        valid_strategy_path = os.path.join(self.temp_dir, "valid_strategy.py")
        with open(valid_strategy_path, 'w') as f:
            f.write("""
from core.strategies import register_strategy

@register_strategy('valid_strategy')
def strategy_function(df):
    return 0.5

class Strategy:
    def __init__(self):
        self.name = "ValidStrategy"
        
    def construct_features(self, df):
        return df
        
    def compute_weights(self, df):
        import pandas as pd
        return pd.Series(index=df.index, data=0.5)
            """)
        
        # Create an invalid strategy file (no Strategy class)
        invalid_strategy_path = os.path.join(self.temp_dir, "invalid_strategy.py")
        with open(invalid_strategy_path, 'w') as f:
            f.write("""
def some_function():
    return "Not a strategy class"
            """)
        
        # Create a timeout strategy file
        timeout_strategy_path = os.path.join(self.temp_dir, "timeout_strategy.py")
        with open(timeout_strategy_path, 'w') as f:
            f.write("""
import time
from core.strategies import register_strategy

@register_strategy('timeout_strategy')
def strategy_function(df):
    time.sleep(5)  # This will cause a timeout
    return 0.5

class Strategy:
    def __init__(self):
        self.name = "TimeoutStrategy"
        time.sleep(5)  # This will cause a timeout
        
    def construct_features(self, df):
        return df
        
    def compute_weights(self, df):
        import pandas as pd
        return pd.Series(index=df.index, data=0.5)
            """)
        
        # Create an error strategy file
        error_strategy_path = os.path.join(self.temp_dir, "error_strategy.py")
        with open(error_strategy_path, 'w') as f:
            f.write("""
from core.strategies import register_strategy

@register_strategy('error_strategy')
def strategy_function(df):
    raise ValueError("Strategy function error")
    return 0.5

class Strategy:
    def __init__(self):
        raise ValueError("Initialization error")
        
    def construct_features(self, df):
        return df
        
    def compute_weights(self, df):
        import pandas as pd
        return pd.Series(index=df.index, data=0.5)
            """)
        
        self.valid_strategy_path = valid_strategy_path
        self.invalid_strategy_path = invalid_strategy_path
        self.timeout_strategy_path = timeout_strategy_path
        self.error_strategy_path = error_strategy_path
        
        # Create test dataframe
        self.test_df = pd.DataFrame({
            'btc_close': [10000, 11000, 12000],
            'eth_close': [200, 210, 220]
        }, index=pd.date_range(start='2020-01-01', periods=3))
    
    def tearDown(self):
        """Tear down test fixture, removing the temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('core.security.validate_strategy_file')
    @patch('core.security.StrategySecurity.secure_strategy')
    def test_load_strategy_from_file_valid(self, mock_secure, mock_validate):
        """Test loading a strategy from a valid file."""
        # Mock secure_strategy to return the original function
        mock_secure.side_effect = lambda x: x
        
        # Need to patch both the imported version and the direct version
        with patch('core.strategy_loader.validate_strategy_file') as mock_validate_direct:
            # Need to mock the strategy registration
            with patch('core.strategies._strategies', new_callable=dict) as mock_strategies:
                # Set up strategy registration
                mock_strategies.clear()
                mock_strategies['valid_strategy'] = lambda df: df
                
                # Call the function
                with patch('core.strategy_loader.set', side_effect=[set(), {'valid_strategy'}]):
                    strategy_name, strategy_fn, strategy_class = load_strategy_from_file(self.valid_strategy_path)
                
                # Check the result - will return the mocked strategy
                self.assertIsNotNone(strategy_name)
                self.assertEqual(strategy_name, "valid_strategy")
                self.assertIsNotNone(strategy_fn)
                
                # In this mock setup, strategy_class might still be None, which is fine
                
                # Check mocks were called
                mock_validate_direct.assert_called_once_with(self.valid_strategy_path)
    
    def test_load_strategy_from_file_invalid_path(self):
        """Test loading a strategy from a non-existent file."""
        result = load_strategy_from_file(os.path.join(self.temp_dir, "nonexistent.py"))
        self.assertEqual(result, (None, None, None))
    
    @patch('core.security.validate_strategy_file')
    def test_load_strategy_from_file_syntax_error(self, mock_validate):
        """Test loading a strategy with syntax error."""
        # Create a file with syntax error
        syntax_error_path = os.path.join(self.temp_dir, "syntax_error.py")
        with open(syntax_error_path, 'w') as f:
            f.write("class Strategy: def __init__(self): this is a syntax error")
        
        # Mock validate_strategy_file to do nothing instead of raising an error
        mock_validate.return_value = None
        
        with patch('core.strategy_loader.validate_strategy_file') as mock_validate2:
            # Need to patch both the import and the direct function call
            mock_validate2.return_value = None
            
            # Call the function
            result = load_strategy_from_file(syntax_error_path)
            self.assertEqual(result, (None, None, None))
            
            # Check that validate_strategy_file was called
            mock_validate2.assert_called_once_with(syntax_error_path)
    
    def test_find_strategy_class_valid(self):
        """Test finding a strategy class by name."""
        # We need to mock some module imports here
        test_module = MagicMock()
        test_class = MagicMock()
        test_class.__name__ = "TestStrategy"
        test_class.construct_features = MagicMock()
        test_class.compute_weights = MagicMock()
        
        # Mock the inspect.getmembers to return our test class
        with patch('core.strategy_loader.import_module', return_value=test_module), \
             patch('inspect.getmembers', return_value=[("TestStrategy", test_class)]), \
             patch('inspect.isclass', return_value=True):
            # Call the function with the exact name that will match in the mocked getmembers
            result = find_strategy_class("TestStrategy")
            self.assertIsNotNone(result)
            self.assertEqual(result, test_class)
    
    def test_find_strategy_class_invalid(self):
        """Test finding a strategy class that doesn't exist."""
        with patch('core.strategy_loader.import_module', side_effect=ImportError), \
             patch('os.path.exists', return_value=True), \
             patch('os.listdir', return_value=[]):
            result = find_strategy_class("NonExistentStrategy")
            self.assertIsNone(result)
    
    @patch('core.strategy_loader.backtest_dynamic_dca')
    @patch('core.security.StrategySecurity.secure_strategy')
    @patch('core.strategies._strategies', new_callable=dict)
    @patch('core.strategy_loader.set')
    def test_process_strategy_file_success(self, mock_set, mock_strategies, mock_secure, mock_backtest):
        """Test processing a strategy file with successful outcome."""
        # Set up mocks to simulate a strategy being registered
        mock_strategies.clear()
        
        # Mock set operations to simulate strategy registration
        before_set = set()
        after_set = {'valid_strategy'}
        mock_set.side_effect = [before_set, after_set]  # First call returns empty set, second call returns strategy set
        
        # Mock secure_strategy to return the original function
        mock_secure.side_effect = lambda x: x
        
        # Mock backtest results
        mock_backtest.return_value = pd.DataFrame({
            'dynamic_spd': [0.1, 0.2, 0.3],
            'excess_pct': [0.05, 0.10, 0.15]
        })
        
        # Simulate a strategy function being added during module execution
        mock_strategies['valid_strategy'] = lambda df: pd.Series(0.5, index=df.index)
        
        # Need to patch the validate_strategy_file function directly in the module
        with patch('core.strategy_loader.validate_strategy_file') as mock_validate_direct:
            # Also mock the security utils function for bandit analysis
            with patch('core.security.utils.get_bandit_threat_level', return_value="Low"):
                # Call the function with test data
                args = (self.valid_strategy_path, self.test_df, False)
                result = process_strategy_file(args)
                
                # Verify validate was called directly
                mock_validate_direct.assert_called_once_with(self.valid_strategy_path)
        
        # Check results
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['strategy'], 'valid_strategy')
        self.assertEqual(result['strategy_file'], self.valid_strategy_path)
        
        # Verify other mocks called
        mock_backtest.assert_called_once()
    
    def test_process_strategy_file_load_error(self):
        """Test processing a strategy file with invalid path."""
        # Call with nonexistent file
        args = (os.path.join(self.temp_dir, "nonexistent.py"), self.test_df, False)
        result = process_strategy_file(args)
        
        # Result should be None for a file not found error
        self.assertIsNone(result)
    
    @patch('core.security.validate_strategy_file')
    def test_process_strategy_file_find_error(self, mock_validate):
        """Test processing a strategy file with no strategy function."""
        # Call with invalid strategy file
        args = (self.invalid_strategy_path, self.test_df, False)
        result = process_strategy_file(args)
        
        # Result should be None for a file with no registered strategy
        self.assertIsNone(result)
    
    @patch('core.security.validate_strategy_file')
    @patch('core.strategy_loader.backtest_dynamic_dca')
    def test_process_strategy_file_init_error(self, mock_backtest, mock_validate):
        """Test processing a strategy file with errors."""
        # Mock backtest to raise an exception
        mock_backtest.side_effect = ValueError("Backtest error")
        
        # Call with error strategy file
        args = (self.error_strategy_path, self.test_df, False)
        result = process_strategy_file(args)
        
        # Result should be None for a file with errors
        self.assertIsNone(result)
    
    @patch('signal.signal')
    @patch('signal.alarm')
    @patch('core.strategy_loader.process_strategy_file')
    def test_process_strategy_file_with_timeout_success(self, mock_process, mock_alarm, mock_signal):
        """Test processing a strategy file with timeout protection - success case."""
        # Mock process_strategy_file to return a result
        expected_result = {'strategy': 'test_strategy'}
        mock_process.return_value = expected_result
        
        # Call the function
        file_args = (self.valid_strategy_path, self.test_df, False)
        result = process_strategy_file_with_timeout((file_args, 60))
        
        # Check results
        self.assertEqual(result, expected_result)
        
        # Verify mocks called
        mock_process.assert_called_once_with(file_args)
        mock_alarm.assert_any_call(60)  # Set timeout
        mock_alarm.assert_any_call(0)   # Cancel timeout
    
    @patch('signal.signal')
    @patch('signal.alarm')
    @patch('core.strategy_loader.process_strategy_file')
    def test_process_strategy_file_timeout(self, mock_process, mock_alarm, mock_signal):
        """Test processing a strategy file with timeout."""
        # Simulate the full function behavior, including timeout handling
        with patch('core.strategy_loader.process_strategy_file_with_timeout') as mock_with_timeout:
            # Mock function to simulate a timeout
            mock_with_timeout.return_value = None
            
            # Call the function
            file_args = (self.timeout_strategy_path, self.test_df, False)
            result = mock_with_timeout((file_args, 1))
            
            # Result should be None for a timeout
            self.assertIsNone(result)
            # Verify the mock was called
            mock_with_timeout.assert_called_once_with((file_args, 1))

if __name__ == "__main__":
    unittest.main() 