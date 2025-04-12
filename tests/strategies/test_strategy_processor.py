import unittest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from core.strategy_processor import process_single_strategy

class TestStrategyProcessor(unittest.TestCase):
    """Tests for strategy processor functionality in core/strategy_processor.py"""
    
    def setUp(self):
        """Set up test data and environment"""
        # Create a temporary directory for test plots
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test data
        date_range = pd.date_range(start='2020-01-01', end='2020-01-31', freq='D')
        self.test_data = pd.DataFrame({
            'btc_close': np.random.randn(len(date_range)) * 100 + 9000,
            'eth_close': np.random.randn(len(date_range)) * 10 + 200,
        }, index=date_range)
        
        # Create mock weights
        self.mock_weights = pd.Series(
            index=self.test_data.index, 
            data=0.5
        )
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    @patch('core.strategies.get_strategy')
    @patch('core.strategy_processor.backtest_dynamic_dca')
    @patch('core.strategy_processor.check_strategy_submission_ready')
    @patch('core.strategy_processor.find_strategy_class')
    def test_process_single_strategy_success(self, 
                                         mock_find_strategy_class,
                                         mock_validate, 
                                         mock_backtest, 
                                         mock_get_strategy):
        """Test process_single_strategy with successful execution"""
        # Configure mocks
        mock_get_strategy.return_value = lambda df: self.mock_weights
        mock_validate.return_value = True  # Validation passes
        mock_find_strategy_class.return_value = None
        
        # Call the function
        process_single_strategy(
            btc_df=self.test_data,
            strategy_name="test_strategy", 
            show_plots=False,
            validate=True
        )
        
        # Verify mocks were called
        mock_get_strategy.assert_called_once_with("test_strategy")
        mock_validate.assert_called_once()
        mock_backtest.assert_called_once()
    
    @patch('core.strategies.get_strategy')
    @patch('core.strategy_processor.backtest_dynamic_dca')
    @patch('core.strategy_processor.check_strategy_submission_ready')
    @patch('core.strategy_processor.find_strategy_class')
    def test_process_single_strategy_validation_failure(self, 
                                                    mock_find_strategy_class,
                                                    mock_validate, 
                                                    mock_backtest,
                                                    mock_get_strategy):
        """Test process_single_strategy with validation failure"""
        # Configure mocks
        mock_get_strategy.return_value = lambda df: self.mock_weights
        mock_validate.return_value = False  # Validation fails
        mock_find_strategy_class.return_value = None
        
        # Call the function
        process_single_strategy(
            btc_df=self.test_data,
            strategy_name="test_strategy", 
            show_plots=False,
            validate=True
        )
        
        # Verify mocks were called
        mock_get_strategy.assert_called_once_with("test_strategy")
        mock_validate.assert_called_once()
        # If validation fails, backtest should still run
        mock_backtest.assert_called_once()
    
    @patch('core.strategies.get_strategy')
    @patch('core.strategy_processor.backtest_dynamic_dca')
    @patch('core.strategy_processor.check_strategy_submission_ready')
    @patch('core.strategy_processor.find_strategy_class')
    def test_process_single_strategy_no_validation(self, 
                                               mock_find_strategy_class,
                                               mock_validate, 
                                               mock_backtest, 
                                               mock_get_strategy):
        """Test process_single_strategy with validation disabled"""
        # Configure mocks
        mock_get_strategy.return_value = lambda df: self.mock_weights
        mock_find_strategy_class.return_value = None
        
        # Call the function
        process_single_strategy(
            btc_df=self.test_data,
            strategy_name="test_strategy", 
            show_plots=False,
            validate=False
        )
        
        # Verify mocks were called
        mock_get_strategy.assert_called_once_with("test_strategy")
        mock_validate.assert_not_called()
        mock_backtest.assert_called_once()
    
    @patch('core.strategies.get_strategy')
    @patch('core.strategy_processor.backtest_dynamic_dca')
    @patch('core.strategy_processor.check_strategy_submission_ready')
    @patch('core.strategy_processor.find_strategy_class')
    @patch('core.strategy_processor.plot_price_vs_lookback_avg')
    @patch('core.strategy_processor.plot_final_weights')
    @patch('core.strategy_processor.plot_weight_sums_by_cycle')
    def test_process_single_strategy_with_plots(self, 
                                            mock_plot_weight_sums,
                                            mock_plot_final_weights,
                                            mock_plot_price, 
                                            mock_find_strategy_class,
                                            mock_validate, 
                                            mock_backtest, 
                                            mock_get_strategy):
        """Test process_single_strategy with plot generation"""
        # Configure mocks
        mock_get_strategy.return_value = lambda df: self.mock_weights
        mock_validate.return_value = True
        mock_find_strategy_class.return_value = None
        
        # Call the function
        process_single_strategy(
            btc_df=self.test_data,
            strategy_name="test_strategy", 
            show_plots=True,
            validate=True
        )
        
        # Verify plot functions were called
        mock_plot_price.assert_called_once()
        mock_plot_final_weights.assert_called_once()
        mock_plot_weight_sums.assert_called_once()
        mock_backtest.assert_called_once()
    
    @patch('core.strategies.get_strategy')
    @patch('core.strategy_processor.backtest_dynamic_dca')
    @patch('core.strategy_processor.check_strategy_submission_ready')
    @patch('core.strategy_processor.find_strategy_class')
    def test_process_single_strategy_from_file(self, 
                                           mock_find_strategy_class,
                                           mock_validate, 
                                           mock_backtest, 
                                           mock_get_strategy):
        """Test process_single_strategy with strategy from file"""
        # Configure mocks for load_strategy_from_file
        with patch('core.strategy_processor.load_strategy_from_file') as mock_load_file:
            mock_load_file.return_value = ("test_strategy", lambda df: self.mock_weights, None)
            mock_validate.return_value = True
            
            # Call the function
            process_single_strategy(
                btc_df=self.test_data,
                strategy_file="path/to/strategy.py",
                show_plots=False,
                validate=True
            )
            
            # Verify load_strategy_from_file was called
            mock_load_file.assert_called_once_with("path/to/strategy.py")
            mock_validate.assert_called_once()
            mock_backtest.assert_called_once()
            # get_strategy should not be called when using a file
            mock_get_strategy.assert_not_called()

    @patch('core.strategies.get_strategy')
    @patch('core.strategy_processor.load_strategy_from_file')
    def test_process_single_strategy_file_not_found(self,
                                                mock_load_file,
                                                mock_get_strategy):
        """Test process_single_strategy with file not found"""
        # Configure mock to return None for file not found
        mock_load_file.return_value = (None, None, None)
        
        # Call the function
        process_single_strategy(
            btc_df=self.test_data,
            strategy_file="nonexistent.py",
            show_plots=False
        )
        
        # Verify load_strategy_from_file was called
        mock_load_file.assert_called_once_with("nonexistent.py")
        # Backtest should not be called if strategy file not found
        mock_get_strategy.assert_not_called()

    @patch('core.strategies.get_strategy')
    @patch('core.strategy_processor.compute_spd_metrics')
    @patch('core.strategy_processor.standalone_plot_comparison')
    @patch('core.strategy_processor.check_strategy_submission_ready')
    @patch('core.strategy_processor.find_strategy_class')
    @patch('core.strategy_processor.load_strategy_from_file')
    @patch('core.strategy_processor.plot_final_weights')
    @patch('core.strategy_processor.plot_weight_sums_by_cycle')
    @patch('core.strategy_processor.plot_price_vs_lookback_avg')
    def test_process_single_strategy_standalone_mode(self,
                                                 mock_plot_price,
                                                 mock_plot_weight_sums,
                                                 mock_plot_final_weights,
                                                 mock_load_strategy_from_file,
                                                 mock_find_strategy_class,
                                                 mock_validate,
                                                 mock_standalone_plot,
                                                 mock_compute_metrics,
                                                 mock_get_strategy):
        """Test process_single_strategy in standalone mode"""
        # Configure mocks
        mock_get_strategy.return_value = lambda df: self.mock_weights
        mock_validate.return_value = True
        mock_find_strategy_class.return_value = None
        mock_compute_metrics.return_value = {
            'min_spd': 10.0,
            'max_spd': 20.0,
            'mean_spd': 15.0,
            'median_spd': 15.0,
            'excess_pct_by_cycle': {'2020–2023': 5.0},
            'mean_excess_pct': 5.0
        }
        # Mock the strategy loader to return a valid strategy
        mock_load_strategy_from_file.return_value = ("test_strategy", lambda df: self.mock_weights, None)
        
        # Call the function with standalone mode
        process_single_strategy(
            btc_df=self.test_data,
            strategy_file="path/to/strategy.py",
            show_plots=True,
            standalone=True,
            validate=True
        )
        
        # In standalone mode with strategy file, should compute metrics and plot
        mock_compute_metrics.assert_called_once()
        mock_standalone_plot.assert_called_once()
        # Verify other plotting functions were also called
        mock_plot_final_weights.assert_called_once()
        mock_plot_weight_sums.assert_called_once()

if __name__ == "__main__":
    unittest.main() 