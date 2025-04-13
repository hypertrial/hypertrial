import pytest
import pandas as pd
import numpy as np
import os
import multiprocessing
from unittest.mock import patch, MagicMock, call

# Import the batch functions
from core.batch import _run_single_backtest, backtest_all_strategies, backtest_multiple_strategy_files


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing"""
    dates = pd.date_range(start='2010-01-01', end='2022-12-31')
    data = {
        'btc_close': np.random.rand(len(dates)) * 50000,
        'btc_open': np.random.rand(len(dates)) * 50000,
        'btc_high': np.random.rand(len(dates)) * 50000,
        'btc_low': np.random.rand(len(dates)) * 50000,
        'btc_volume': np.random.rand(len(dates)) * 1000000
    }
    return pd.DataFrame(data, index=dates)


def test_run_single_backtest_success(sample_dataframe):
    """Test _run_single_backtest when the strategy is processed successfully"""
    with patch('core.batch.process_single_strategy') as mock_process:
        # Mock successful processing with metrics
        mock_process.return_value = {
            'strategy_name': 'test_strategy',
            'spd_metrics': {
                'min_spd': 1000.0,
                'max_spd': 5000.0
            }
        }
        
        # Run the function
        strategy_file = 'test_strategy.py'
        output_dir = 'test_output'
        result = _run_single_backtest((sample_dataframe, strategy_file, output_dir, False, True))
        
        # Verify process_single_strategy was called with correct arguments
        mock_process.assert_called_once_with(
            sample_dataframe, 
            strategy_file=strategy_file, 
            show_plots=False, 
            save_plots=True, 
            output_dir=output_dir, 
            validate=True,
            return_metrics=True
        )
        
        # Check return value is a dictionary with expected keys
        assert isinstance(result, dict)
        assert result['strategy_file'] == 'test_strategy'
        assert result['strategy_name'] == 'test_strategy'
        assert result['success'] is True


def test_run_single_backtest_error(sample_dataframe):
    """Test _run_single_backtest when an error occurs during processing"""
    with patch('core.batch.process_single_strategy') as mock_process:
        # Mock an error during processing
        mock_process.side_effect = Exception("Processing error")
        
        with patch('builtins.print') as mock_print:
            # Run the function
            strategy_file = 'test_strategy.py'
            output_dir = 'test_output'
            result = _run_single_backtest((sample_dataframe, strategy_file, output_dir, False, True))
            
            # Verify process_single_strategy was called with correct arguments
            mock_process.assert_called_once_with(
                sample_dataframe, 
                strategy_file=strategy_file, 
                show_plots=False, 
                save_plots=True, 
                output_dir=output_dir, 
                validate=True,
                return_metrics=True
            )
            
            # Verify error was printed
            mock_print.assert_any_call("Error processing test_strategy.py: Processing error")
            
            # Check return value is a dictionary with error information
            assert isinstance(result, dict)
            assert result['strategy_file'] == 'test_strategy'
            assert result['success'] is False
            assert 'error' in result


def test_backtest_all_strategies_no_strategies():
    """Test backtest_all_strategies when no strategies are found"""
    with patch('core.strategies.list_strategies', return_value={}) as mock_list, \
         patch('os.makedirs') as mock_makedirs, \
         patch('core.batch.logger') as mock_logger:
        
        # Run the function
        result = backtest_all_strategies(pd.DataFrame(), 'test_output')
        
        # Verify list_strategies was called
        mock_list.assert_called_once()
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        
        # Verify result is None
        assert result is None


def test_backtest_all_strategies_sequential(sample_dataframe):
    """Test backtest_all_strategies with sequential processing"""
    # Mock strategies
    strategies = {
        'strategy1': 'Strategy 1 description',
        'strategy2': 'Strategy 2 description'
    }
    
    with patch('core.strategies.list_strategies', return_value=strategies) as mock_list, \
         patch('os.makedirs') as mock_makedirs, \
         patch('multiprocessing.cpu_count', return_value=1) as mock_cpu_count, \
         patch('core.batch.logger') as mock_logger, \
         patch('core.spd.backtest_dynamic_dca') as mock_backtest, \
         patch('core.security.utils.get_bandit_threat_level') as mock_bandit, \
         patch('os.path.dirname') as mock_dirname, \
         patch('os.path.exists', return_value=True) as mock_exists, \
         patch('pandas.DataFrame.to_csv') as mock_to_csv:
        
        # Set up mock returns
        mock_dirname.return_value = '/mock/path'
        mock_backtest.return_value = pd.DataFrame({
            'dynamic_spd': [100, 200],
            'dynamic_pct': [20, 30],
            'excess_pct': [5, 10]
        }, index=['cycle1', 'cycle2'])
        mock_bandit.return_value = {
            'high_threat_count': 0,
            'medium_threat_count': 1,
            'low_threat_count': 2,
            'total_threat_count': 3
        }
        
        # Run the function
        result = backtest_all_strategies(sample_dataframe, 'test_output')
        
        # Verify list_strategies was called
        mock_list.assert_called_once()
        
        # Verify backtest_dynamic_dca was called for each strategy
        assert mock_backtest.call_count == 2
        mock_backtest.assert_has_calls([
            call(sample_dataframe, strategy_name='strategy1', show_plots=False),
            call(sample_dataframe, strategy_name='strategy2', show_plots=False)
        ], any_order=True)
        
        # Verify to_csv was called to save results
        assert mock_to_csv.call_count >= 2
        
        # Check that the function returned a DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # One row per strategy


def test_backtest_all_strategies_parallel(sample_dataframe):
    """Test backtest_all_strategies with parallel processing"""
    # Mock strategies
    strategies = {
        'strategy1': 'Strategy 1 description',
        'strategy2': 'Strategy 2 description'
    }
    
    with patch('core.strategies.list_strategies', return_value=strategies) as mock_list, \
         patch('os.makedirs') as mock_makedirs, \
         patch('multiprocessing.cpu_count', return_value=4) as mock_cpu_count, \
         patch('core.batch.logger') as mock_logger, \
         patch('multiprocessing.Pool') as mock_pool_class:
        
        # Mock the pool context manager
        mock_pool = MagicMock()
        mock_pool_class.return_value.__enter__.return_value = mock_pool
        
        # Set up mock pool.imap_unordered to yield results
        mock_pool.imap_unordered.return_value = iter([
            {
                'strategy_file': 'strategy1.py',
                'strategy_name': 'strategy1',
                'success': True,
                'min_spd': 1000.0,
                'max_spd': 5000.0
            },
            {
                'strategy_file': 'strategy2.py',
                'strategy_name': 'strategy2',
                'success': True,
                'min_spd': 2000.0,
                'max_spd': 6000.0
            }
        ])
        
        # More mocks for the result processing
        with patch('core.spd.backtest_dynamic_dca') as mock_backtest, \
             patch('core.security.utils.get_bandit_threat_level') as mock_bandit, \
             patch('os.path.dirname') as mock_dirname, \
             patch('os.path.exists', return_value=True) as mock_exists, \
             patch('pandas.DataFrame.to_csv') as mock_to_csv:
            
            # Set up mock returns
            mock_dirname.return_value = '/mock/path'
            mock_backtest.return_value = pd.DataFrame({
                'dynamic_spd': [100, 200],
                'dynamic_pct': [20, 30],
                'excess_pct': [5, 10]
            }, index=['cycle1', 'cycle2'])
            mock_bandit.return_value = {
                'high_threat_count': 0,
                'medium_threat_count': 1,
                'low_threat_count': 2,
                'total_threat_count': 3
            }
            
            # Run the function
            result = backtest_all_strategies(sample_dataframe, 'test_output')
            
            # Verify list_strategies was called
            mock_list.assert_called_once()
            
            # Check that to_csv was called to save results
            assert mock_to_csv.call_count >= 1
            
            # Check that the function returned a DataFrame
            assert isinstance(result, pd.DataFrame)


def test_backtest_multiple_strategy_files(sample_dataframe):
    """Test backtest_multiple_strategy_files function"""
    # Create mock test data
    strategy_file1 = 'test_strategy1.py'
    strategy_file2 = 'test_strategy2.py'
    output_dir = 'test_output'
    
    # Mock the _run_single_backtest function to return success
    with patch('core.batch._run_single_backtest') as mock_run_single, \
         patch('os.makedirs') as mock_makedirs, \
         patch('pandas.DataFrame.to_csv') as mock_to_csv, \
         patch('core.batch.logger') as mock_logger:
        
        # Set up mock to return success for both files with metrics
        mock_run_single.side_effect = [
            {
                'strategy_file': 'test_strategy1',
                'strategy_name': 'strategy1',
                'success': True,
                'min_spd': 1000.0,
                'max_spd': 5000.0,
                'mean_spd': 2500.0
            },
            {
                'strategy_file': 'test_strategy2',
                'strategy_name': 'strategy2',
                'success': True,
                'min_spd': 2000.0,
                'max_spd': 6000.0,
                'mean_spd': 3500.0
            }
        ]
        
        # Call the function
        result = backtest_multiple_strategy_files(
            sample_dataframe,
            [strategy_file1, strategy_file2],
            output_dir,
            show_plots=False
        )
        
        # Check function calls
        assert mock_run_single.call_count == 2
        mock_run_single.assert_has_calls([
            call((sample_dataframe, strategy_file1, output_dir, False, True)),
            call((sample_dataframe, strategy_file2, output_dir, False, True))
        ], any_order=True)
        
        # Check that at least one DataFrame.to_csv was called (for results)
        assert mock_to_csv.call_count >= 1
        
        # Check result is a DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # One row per strategy


def test_backtest_multiple_strategy_files_with_timeout(sample_dataframe):
    """Test backtest_multiple_strategy_files function with timeout"""
    # Create mock test data
    strategy_file1 = 'test_strategy1.py'
    strategy_file2 = 'test_strategy2.py'
    output_dir = 'test_output'
    
    # Mock the _run_single_backtest function to return success
    with patch('core.batch._run_single_backtest') as mock_run_single, \
         patch('os.makedirs') as mock_makedirs, \
         patch('pandas.DataFrame.to_csv') as mock_to_csv, \
         patch('core.batch.logger') as mock_logger:
        
        # Set up mock to return success for both files
        mock_run_single.side_effect = [
            {
                'strategy_file': 'test_strategy1',
                'strategy_name': 'strategy1',
                'success': True,
                'min_spd': 1000.0
            },
            {
                'strategy_file': 'test_strategy2',
                'strategy_name': 'strategy2',
                'success': True,
                'min_spd': 2000.0
            }
        ]
        
        # Call the function with timeout
        result = backtest_multiple_strategy_files(
            sample_dataframe,
            [strategy_file1, strategy_file2],
            output_dir,
            show_plots=False,
            file_timeout=30
        )
        
        # Check function calls
        assert mock_run_single.call_count == 2
        
        # Check result is a DataFrame
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # One row per strategy


def test_backtest_multiple_strategy_files_empty(sample_dataframe):
    """Test backtest_multiple_strategy_files with no strategy files"""
    with patch('os.makedirs') as mock_makedirs, \
         patch('core.batch.logger') as mock_logger:
        
        # Run the function with no strategy files
        result = backtest_multiple_strategy_files(
            sample_dataframe,
            [],
            'test_output'
        )
        
        # Verify error was logged
        mock_logger.error.assert_called_once()
        
        # Verify result is an empty DataFrame, not None
        assert isinstance(result, pd.DataFrame)
        assert result.empty


def test_backtest_all_strategies_parallel_error(sample_dataframe):
    """Test error handling in parallel backtest_all_strategies"""
    # Mock strategies
    strategies = {
        'strategy1': 'Strategy 1 description',
        'strategy2': 'Strategy 2 description'
    }
    
    with patch('core.strategies.list_strategies', return_value=strategies) as mock_list, \
         patch('os.makedirs') as mock_makedirs, \
         patch('multiprocessing.cpu_count', return_value=4) as mock_cpu_count, \
         patch('core.batch.logger') as mock_logger, \
         patch('multiprocessing.Pool') as mock_pool_class:
        
        # Mock the pool context manager
        mock_pool = MagicMock()
        mock_pool_class.return_value.__enter__.return_value = mock_pool
        
        # Set up mock pool.imap_unordered to yield results with one error
        mock_pool.imap_unordered.return_value = iter([
            {
                'strategy_file': 'strategy1.py',
                'strategy_name': 'strategy1',
                'success': True
            },
            {
                'strategy_file': 'strategy2.py',
                'strategy_name': 'strategy2',
                'success': False
            }  # This strategy failed
        ])
        
        # More mocks for the result processing
        with patch('core.spd.backtest_dynamic_dca') as mock_backtest, \
             patch('core.security.utils.get_bandit_threat_level') as mock_bandit, \
             patch('os.path.dirname') as mock_dirname, \
             patch('os.path.exists', return_value=True) as mock_exists, \
             patch('pandas.DataFrame.to_csv') as mock_to_csv:
            
            # Set up mock returns
            mock_dirname.return_value = '/mock/path'
            mock_backtest.return_value = pd.DataFrame({
                'dynamic_spd': [100, 200],
                'dynamic_pct': [20, 30],
                'excess_pct': [5, 10]
            }, index=['cycle1', 'cycle2'])
            mock_bandit.return_value = {
                'high_threat_count': 0,
                'medium_threat_count': 1,
                'low_threat_count': 2,
                'total_threat_count': 3
            }
            
            # Reset mock logger to clear any previous calls
            mock_logger.warning.reset_mock()
            
            # Run the function
            result = backtest_all_strategies(sample_dataframe, 'test_output')
            
            # Verify warning was logged for failed strategy
            mock_logger.warning.assert_called_once_with('Strategy strategy2 processing failed, skipping')
            
            # Verify successful strategy was processed
            assert mock_backtest.call_count == 1
            mock_backtest.assert_called_once_with(sample_dataframe, strategy_name='strategy1', show_plots=False)
            
            # Verify output was generated
            assert isinstance(result, pd.DataFrame)
            assert mock_to_csv.call_count >= 1 