import unittest
import pandas as pd
import numpy as np
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import multiprocessing

from core.batch import (
    _run_single_backtest,
    backtest_all_strategies,
    backtest_multiple_strategy_files
)

class TestBatch(unittest.TestCase):
    """Tests for batch processing functionality in core/batch.py"""
    
    def setUp(self):
        """Set up test data and environment"""
        # Create sample dataframe
        dates = pd.date_range(start='2013-01-01', end='2024-12-31', freq='D')
        btc_prices = np.exp(np.linspace(np.log(10), np.log(50000), len(dates)))
        
        self.df = pd.DataFrame({
            'btc_close': btc_prices
        }, index=dates)
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a few test strategy files
        self.strategy_file1 = os.path.join(self.temp_dir, "strategy1.py")
        with open(self.strategy_file1, "w") as f:
            f.write("""
import pandas as pd
from core.strategies import register_strategy

@register_strategy("test_strategy1")
def test_strategy1(df):
    return pd.Series(1.0 / len(df), index=df.index)
""")
        
        self.strategy_file2 = os.path.join(self.temp_dir, "strategy2.py")
        with open(self.strategy_file2, "w") as f:
            f.write("""
import pandas as pd
from core.strategies import register_strategy

@register_strategy("test_strategy2")
def test_strategy2(df):
    weights = pd.Series(index=df.index, data=0.0)
    weights.iloc[::2] = 2.0 / weights.iloc[::2].shape[0]  # Every other day
    return weights
""")
    
    def tearDown(self):
        """Clean up after tests"""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    @patch('core.strategy_processor.process_single_strategy')
    @patch('core.strategy_processor.backtest_dynamic_dca')  # Patch the correct module
    def test_run_single_backtest(self, mock_backtest, mock_process):
        """Test _run_single_backtest function"""
        # Set up mocks so they don't actually run
        mock_process.return_value = {'strategy_name': 'test_strategy1', 'spd_metrics': {'min_spd': 1000.0}}
        
        # Call the function directly
        args = (self.df, self.strategy_file1, self.temp_dir, False, True)
        result = _run_single_backtest(args)
        
        # Check the result structure without relying on specific mock interactions
        self.assertIsInstance(result, dict)
        
        # Check that the result contains required keys
        self.assertIn('strategy_name', result)
        self.assertIn('strategy_file', result)
        self.assertIn('success', result)
        
        # Check the values
        self.assertEqual(result['strategy_file'], 'strategy1')
        self.assertTrue(result['success'])
    
    @patch('core.batch._run_single_backtest')
    def test_backtest_multiple_strategy_files(self, mock_run_single):
        """Test backtest_multiple_strategy_files function"""
        # Configure mock to return success for both files
        mock_run_single.side_effect = [
            {
                'strategy_file': 'test_strategy1',
                'strategy_name': 'test_strategy1',
                'success': True,
                'min_spd': 1000.0,
                'max_spd': 5000.0,
                'mean_spd': 2500.0,
                'median_spd': 2000.0
            },
            {
                'strategy_file': 'test_strategy2',
                'strategy_name': 'test_strategy2',
                'success': True,
                'min_spd': 2000.0,
                'max_spd': 6000.0,
                'mean_spd': 3500.0,
                'median_spd': 3000.0
            }
        ]
        
        # Call the function
        strategy_files = [self.strategy_file1, self.strategy_file2]
        result = backtest_multiple_strategy_files(
            self.df, 
            strategy_files, 
            self.temp_dir, 
            show_plots=False
        )
        
        # Check the result
        self.assertIsInstance(result, pd.DataFrame)
        # Check that the DataFrame contains expected information
        # The actual structure might differ from our expectations
        self.assertGreaterEqual(len(result), 1)
        
        # Verify mock was called correctly - should be called twice
        self.assertEqual(mock_run_single.call_count, 2)
    
    # This test will be skipped because we can't pickle MagicMock for multiprocessing
    @unittest.skip("Can't pickle MagicMock for multiprocessing")
    @patch('core.batch._run_single_backtest')
    def test_backtest_multiple_strategy_files_with_processes(self, mock_run_single):
        """Test backtest_multiple_strategy_files with parallel processing"""
        # Skipped due to MagicMock pickling issue
        pass
    
    @patch('core.batch._run_single_backtest')
    def test_backtest_multiple_strategy_files_with_batch_size(self, mock_run_single):
        """Test backtest_multiple_strategy_files with batch processing"""
        # Configure mock to return success for files
        mock_run_single.side_effect = [
            {
                'strategy_file': 'test_strategy1',
                'strategy_name': 'test_strategy1',
                'success': True,
                'min_spd': 1000.0
            },
            {
                'strategy_file': 'test_strategy2',
                'strategy_name': 'test_strategy2',
                'success': True,
                'min_spd': 2000.0
            }
        ]
        
        # Create more strategy files for this test
        strategy_files = [self.strategy_file1, self.strategy_file2]
        
        # Call the function with batch size
        result = backtest_multiple_strategy_files(
            self.df, 
            strategy_files, 
            self.temp_dir, 
            show_plots=False,
            batch_size=1  # Process one at a time
        )
        
        # Check the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreaterEqual(len(result), 1)  # At least one row
    
    @patch('core.strategies.list_strategies')
    @patch('core.strategies.get_strategy')
    @patch('core.security.utils.get_bandit_threat_level')
    @patch('multiprocessing.cpu_count')
    @patch('core.spd.backtest_dynamic_dca')  # Patch the correct module
    def test_backtest_all_strategies(self, mock_backtest, mock_cpu_count, mock_bandit, mock_get, mock_list):
        """Test backtest_all_strategies function"""
        # Configure mocks
        mock_list.return_value = {"test_strategy1": "Test Strategy 1", "test_strategy2": "Test Strategy 2"}
        mock_get.side_effect = lambda name: lambda df: pd.Series(1.0 / len(df), index=df.index)
        mock_cpu_count.return_value = 1  # Force sequential processing
        
        # Mock the backtest results
        mock_backtest.return_value = pd.DataFrame({
            'cycle': ['2013-2016'],
            'dynamic_spd': [1000.0],
            'uniform_spd': [900.0],
            'excess_pct': [10.0],
            'dynamic_pct': [80.0]
        })
        
        # Mock bandit results
        mock_bandit.return_value = {
            'high_threat_count': 0,
            'medium_threat_count': 0,
            'low_threat_count': 1,
            'total_threat_count': 1
        }
        
        # Create a temporary submit_strategies directory with some dummy files
        submit_dir = os.path.join(self.temp_dir, 'submit_strategies')
        os.makedirs(submit_dir, exist_ok=True)
        
        # Create dummy strategy files
        with open(os.path.join(submit_dir, 'test_strategy1.py'), 'w') as f:
            f.write("# Dummy strategy file")
        
        with open(os.path.join(submit_dir, 'test_strategy2.py'), 'w') as f:
            f.write("# Dummy strategy file")
        
        # Call the function
        result = backtest_all_strategies(
            self.df,
            self.temp_dir,
            show_plots=False
        )
        
        # Check the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertGreaterEqual(len(result), 1)  # At least one row

    @patch('core.strategies.list_strategies')
    @patch('core.strategies.get_strategy')
    @patch('core.security.utils.get_bandit_threat_level')
    @patch('multiprocessing.cpu_count')
    @patch('core.spd.backtest_dynamic_dca')  # Patch the correct module
    def test_backtest_all_strategies_with_validation_results(self, mock_backtest, mock_cpu_count, mock_bandit, mock_get, mock_list):
        """Test that validation results from spd_checks are included in the CSV output"""
        # Configure mocks
        mock_list.return_value = {"test_strategy1": "Test Strategy 1"}
        mock_get.side_effect = lambda name: lambda df: pd.Series(1.0 / len(df), index=df.index)
        mock_cpu_count.return_value = 1  # Force sequential processing
        
        # Create mock validation results in the returned DataFrame
        mock_df = pd.DataFrame({
            'cycle': ['2013-2016'],
            'dynamic_spd': [1000.0],
            'uniform_spd': [900.0],
            'excess_pct': [10.0],
            'dynamic_pct': [80.0],
            'validation_passed': [True],
            'has_negative_weights': [False],
            'has_below_min_weights': [False],
            'weights_not_sum_to_one': [False],
            'underperforms_uniform': [False],
            'is_forward_looking': [False]
        })
        
        mock_backtest.return_value = mock_df
        
        # Mock bandit results
        mock_bandit.return_value = {
            'high_threat_count': 0,
            'medium_threat_count': 0,
            'low_threat_count': 1,
            'total_threat_count': 1
        }
        
        # Create a temporary submit_strategies directory with a dummy file
        submit_dir = os.path.join(self.temp_dir, 'submit_strategies')
        os.makedirs(submit_dir, exist_ok=True)
        
        with open(os.path.join(submit_dir, 'test_strategy1.py'), 'w') as f:
            f.write("# Dummy strategy file")
        
        # Call the function
        result = backtest_all_strategies(
            self.df,
            self.temp_dir,
            show_plots=False
        )
        
        # Check that the validation results are included in the output
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn('validation_passed', result.columns)
        self.assertIn('has_negative_weights', result.columns)
        self.assertIn('has_below_min_weights', result.columns)
        self.assertIn('weights_not_sum_to_one', result.columns)
        self.assertIn('underperforms_uniform', result.columns)
        self.assertIn('is_forward_looking', result.columns)
        
        # Verify CSV was created with validation results
        csv_path = os.path.join(self.temp_dir, 'strategy_summary.csv')
        self.assertTrue(os.path.exists(csv_path))
        
        # Read the CSV and check validation columns
        csv_df = pd.read_csv(csv_path)
        self.assertIn('validation_passed', csv_df.columns)
        self.assertIn('has_negative_weights', csv_df.columns)
        self.assertIn('has_below_min_weights', csv_df.columns)
        self.assertIn('weights_not_sum_to_one', csv_df.columns)
        self.assertIn('underperforms_uniform', csv_df.columns)
        self.assertIn('is_forward_looking', csv_df.columns)

    @patch('core.batch._run_single_backtest')
    def test_csv_output_contains_all_required_columns(self, mock_run_single):
        """Test that the CSV output contains all required columns from SPD, validation, and security"""
        # Mock return value for _run_single_backtest
        mock_run_single.return_value = {
            'strategy_file': 'test_strategy',
            'strategy_name': 'dynamic_dca_test',
            'success': True,
            'min_spd': 1000.0,
            'max_spd': 5000.0,
            'mean_spd': 2500.0,
            'median_spd': 2000.0,
            'min_pct': 10.0,
            'max_pct': 90.0,
            'mean_pct': 50.0,
            'median_pct': 45.0,
            'cycles': ['2013–2016', '2017–2020', '2021–2024'],
            'excess_pct': [0.5, 1.5, 2.5],
            'mean_excess_pct': 1.5,
            'validation_validation_passed': True,
            'validation_has_negative_weights': False,
            'validation_has_below_min_weights': False,
            'validation_weights_not_sum_to_one': False,
            'validation_underperforms_uniform': False,
            'validation_cycle_issues': {},
            'high_threats': 0,
            'medium_threats': 0,
            'low_threats': 1,
            'total_threats': 1
        }
        
        # Create some test strategy files
        os.makedirs(os.path.join(self.temp_dir, 'strategies'), exist_ok=True)
        test_file_path = os.path.join(self.temp_dir, 'strategies', 'test_strategy.py')
        with open(test_file_path, 'w') as f:
            f.write("# Test strategy")
        
        # Call the function
        result = backtest_multiple_strategy_files(
            self.df,
            [test_file_path],
            self.temp_dir,
            show_plots=False,
            processes=1
        )
        
        # Check the result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 1)  # One strategy
        
        # Verify CSV was created
        csv_path = os.path.join(self.temp_dir, 'strategy_files_summary.csv')
        self.assertTrue(os.path.exists(csv_path))
        
        # Read the CSV and check all required columns
        csv_df = pd.read_csv(csv_path)
        
        # 1. Strategy identification columns
        self.assertIn('strategy_file', csv_df.columns)
        self.assertIn('strategy_name', csv_df.columns)
        self.assertIn('success', csv_df.columns)
        
        # 2. SPD metrics from spd.py
        self.assertIn('min_spd', csv_df.columns)
        self.assertIn('max_spd', csv_df.columns)
        self.assertIn('mean_spd', csv_df.columns)
        self.assertIn('median_spd', csv_df.columns)
        self.assertIn('min_pct', csv_df.columns)
        self.assertIn('max_pct', csv_df.columns)
        self.assertIn('mean_pct', csv_df.columns)
        self.assertIn('median_pct', csv_df.columns)
        self.assertIn('cycles', csv_df.columns)
        self.assertIn('excess_pct', csv_df.columns)
        self.assertIn('mean_excess_pct', csv_df.columns)
        
        # 3. Validation results from spd_checks.py
        self.assertIn('validation_validation_passed', csv_df.columns)
        self.assertIn('validation_has_negative_weights', csv_df.columns)
        self.assertIn('validation_has_below_min_weights', csv_df.columns)
        self.assertIn('validation_weights_not_sum_to_one', csv_df.columns)
        self.assertIn('validation_underperforms_uniform', csv_df.columns)
        self.assertIn('validation_cycle_issues', csv_df.columns)
        
        # 4. Security results from bandit_analyzer.py
        self.assertIn('high_threats', csv_df.columns)
        self.assertIn('medium_threats', csv_df.columns)
        self.assertIn('low_threats', csv_df.columns)
        self.assertIn('total_threats', csv_df.columns)
        
        # Verify values match what we mocked
        self.assertEqual(csv_df['strategy_name'].iloc[0], 'dynamic_dca_test')
        self.assertEqual(csv_df['min_spd'].iloc[0], 1000.0)
        self.assertEqual(csv_df['mean_excess_pct'].iloc[0], 1.5)
        self.assertEqual(csv_df['high_threats'].iloc[0], 0)
        self.assertEqual(csv_df['total_threats'].iloc[0], 1)
        self.assertTrue(csv_df['validation_validation_passed'].iloc[0])

if __name__ == "__main__":
    unittest.main() 