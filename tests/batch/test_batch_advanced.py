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
        # Mock successful processing
        mock_process.return_value = True
        
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
            validate=True
        )
        
        # Check return value
        assert result == ('test_strategy', True)


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
                validate=True
            )
            
            # Verify error was printed
            mock_print.assert_any_call("Error processing test_strategy.py: Processing error")
            
            # Check return value
            assert result == ('test_strategy', False)


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
            ('strategy1', True),
            ('strategy2', True)
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
            
            # Verify Pool was created with correct number of processes
            mock_pool_class.assert_called_once_with(processes=2)
            
            # Verify imap_unordered was called with _run_single_backtest
            mock_pool.imap_unordered.assert_called_once()
            
            # Verify to_csv was called to save results
            assert mock_to_csv.call_count >= 2
            
            # Check that the function returned a DataFrame
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 2  # One row per strategy


def test_backtest_multiple_strategy_files(sample_dataframe):
    """Test backtest_multiple_strategy_files function"""
    # Mock strategy files
    strategy_files = ['strategy1.py', 'strategy2.py']
    
    with patch('os.makedirs') as mock_makedirs, \
         patch('core.batch.logger') as mock_logger, \
         patch('core.batch._run_single_backtest') as mock_run_backtest, \
         patch('pandas.DataFrame.to_csv') as mock_to_csv, \
         patch('core.strategy_processor.process_single_strategy') as mock_process_single_strategy:
        
        # Set up mock returns
        mock_run_backtest.side_effect = [
            ('strategy1', True),
            ('strategy2', True)
        ]
        
        # Run the function with sequential processing
        result = backtest_multiple_strategy_files(
            sample_dataframe, 
            strategy_files, 
            'test_output', 
            processes=0
        )
        
        # Verify _run_single_backtest was called for each file
        assert mock_run_backtest.call_count == 2
        mock_run_backtest.assert_has_calls([
            call((sample_dataframe, 'strategy1.py', 'test_output', False, True)),
            call((sample_dataframe, 'strategy2.py', 'test_output', False, True))
        ], any_order=True)
        
        # Reset mocks
        mock_run_backtest.reset_mock()
        
        # Test with parallel processing
        with patch('multiprocessing.Pool') as mock_pool_class:
            # Mock the pool context manager
            mock_pool = MagicMock()
            mock_pool_class.return_value.__enter__.return_value = mock_pool
            
            # Set up mock pool.imap_unordered to yield results
            mock_pool.imap_unordered.return_value = iter([
                ('strategy1', True),
                ('strategy2', True)
            ])
            
            # Run the function with parallel processing
            result = backtest_multiple_strategy_files(
                sample_dataframe, 
                strategy_files, 
                'test_output', 
                processes=2
            )
            
            # Verify Pool was created with correct number of processes
            mock_pool_class.assert_called_once_with(processes=2)
            
            # Verify imap_unordered was called
            mock_pool.imap_unordered.assert_called_once()


def test_backtest_multiple_strategy_files_with_timeout(sample_dataframe):
    """Test backtest_multiple_strategy_files with a timeout for each file"""
    # Mock strategy files
    strategy_files = ['strategy1.py', 'strategy2.py']
    
    with patch('os.makedirs') as mock_makedirs, \
         patch('core.batch.logger') as mock_logger, \
         patch('core.batch._run_single_backtest') as mock_run_backtest, \
         patch('pandas.DataFrame.to_csv') as mock_to_csv:
        
        # Set up mock return values
        mock_run_backtest.side_effect = [
            ('strategy1', True),
            ('strategy2', True)
        ]
        
        # Run the function
        result = backtest_multiple_strategy_files(
            sample_dataframe,
            strategy_files,
            'test_output',
            file_timeout=10
        )
        
        # Verify _run_single_backtest was called for each file
        assert mock_run_backtest.call_count == 2
        
        # Verify to_csv was called to save results
        assert mock_to_csv.call_count >= 1


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
            ('strategy1', True),
            ('strategy2', False)  # This strategy failed
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
            
            # Verify warning was logged for failed strategy
            mock_logger.warning.assert_called_once()
            
            # Verify Pool was created with correct number of processes
            mock_pool_class.assert_called_once_with(processes=2)
            
            # One successful strategy should still be processed
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1  # Only the successful strategy should be in the result 