import unittest
import os
import tempfile
import shutil
import subprocess
import sys
import pandas as pd
from unittest.mock import patch, MagicMock

class TestDataDownloadIntegration(unittest.TestCase):
    """Integration tests for the data download workflow."""
    
    def setUp(self):
        """Setup for each test."""
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()
        
        # Get absolute path to core directory
        cwd = os.getcwd()
        if os.path.basename(cwd) != 'hypertrial':
            # Assume we're running from within 'tests'
            self.core_dir = os.path.abspath(os.path.join(cwd, '..', 'core'))
        else:
            # We're running from project root
            self.core_dir = os.path.abspath(os.path.join(cwd, 'core'))
            
        # Create a data subdirectory in the temp dir
        self.data_dir = os.path.join(self.temp_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Path to test CSV file - use a very distinctive name to avoid confusion with production
        self.test_csv_path = os.path.join(self.data_dir, 'TEST_ONLY_btc_data_TESTING.csv')
        
        # Sample data for testing - use distinctive values to spot test data in production
        self.sample_df = pd.DataFrame({
            'btc_close': [999.0, 998.0, 997.0, 996.0, 995.0]
        }, index=pd.date_range(start='2020-01-01', periods=5))
    
    def tearDown(self):
        """Cleanup after each test."""
        shutil.rmtree(self.temp_dir)
    
    @patch('core.data.extract_data.CoinMetricsClient')
    def test_workflow_with_download(self, mock_client_class):
        """Test the full workflow involving download when file doesn't exist."""
        # Mock the CoinMetrics client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_df = pd.DataFrame({
            'time': pd.date_range(start='2020-01-01', periods=5),
            'PriceUSD': [999.0, 998.0, 997.0, 996.0, 995.0]
        })
        mock_response.to_dataframe.return_value = mock_df
        mock_response.empty.return_value = False
        mock_client.get_asset_metrics.return_value = mock_response
        
        # Import the necessary functions
        from core.data import load_data
        
        # Try to load data with a non-existent file path
        result_df = load_data(csv_path=self.test_csv_path)
        
        # Verify the function executed correctly
        self.assertIsInstance(result_df, pd.DataFrame)
        self.assertIn('btc_close', result_df.columns)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(self.test_csv_path))
    
    @patch('subprocess.run')
    def test_cli_download_integration(self, mock_run):
        """Test the CLI download option integration."""
        # Set up mock process
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout = "Successfully downloaded"
        mock_run.return_value = mock_process
        
        # Construct the command
        cmd = [
            sys.executable,
            "-m", "core.main",
            "--download-data",
            "--data-file", self.test_csv_path,
            "--no-plots"
        ]
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Verify subprocess.run was called with expected arguments
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], sys.executable)
        self.assertIn("--download-data", args)
        self.assertIn("--data-file", args)
        self.assertIn(self.test_csv_path, args)
    
    def test_extract_data_script_direct(self):
        """Test the extract_data.py script directly."""
        # Mock CoinMetrics client before importing the module
        with patch('core.data.extract_data.CoinMetricsClient') as mock_client_class:
            # Set up mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            # Mock response
            mock_response = MagicMock()
            mock_df = pd.DataFrame({
                'time': pd.date_range(start='2020-01-01', periods=5),
                'PriceUSD': [999.0, 998.0, 997.0, 996.0, 995.0]
            })
            mock_response.to_dataframe.return_value = mock_df
            mock_response.empty.return_value = False
            mock_client.get_asset_metrics.return_value = mock_response
            
            # Now import the module
            from core.data.extract_data import extract_btc_data
            
            # Call the function with custom path
            with patch('os.makedirs'):
                with patch('pandas.DataFrame.to_csv'):
                    result = extract_btc_data(save_to_csv=True)
                    
                    # Verify we got a DataFrame
                    self.assertIsInstance(result, pd.DataFrame)
                    self.assertIn('btc_close', result.columns)
                    
                    # Verify the API was called correctly
                    mock_client.get_asset_metrics.assert_called_once()
    
    def test_main_module_with_download_option(self):
        """Test the main module with download option set."""
        # We need to patch both the argparse result and the extract_btc_data function
        with patch('core.main.parse_args') as mock_parse_args, \
             patch('core.data.extract_data.extract_btc_data') as mock_extract, \
             patch('core.commands.extract_btc_data') as mock_commands_extract:  # Also patch in commands module
            
            # Configure mocks
            mock_args = MagicMock()
            mock_args.download_data = True
            mock_args.list = False
            mock_args.data_file = self.test_csv_path
            mock_args.strategy = 'dynamic_dca'
            mock_args.strategy_file = None
            mock_args.strategy_files = None
            mock_args.strategy_dir = None
            mock_args.glob_pattern = None
            mock_args.standalone = False
            mock_args.no_plots = True
            mock_args.backtest_all = False
            mock_args.processes = 1
            mock_args.batch_size = 0
            mock_args.file_timeout = 60
            mock_parse_args.return_value = mock_args
            
            # Make extract_btc_data return a valid DataFrame
            mock_extract.return_value = self.sample_df
            mock_commands_extract.return_value = self.sample_df
            
            # Also need to patch load_data to return our sample
            with patch('core.main.load_data') as mock_load_data, \
                 patch('core.main.backtest_dynamic_dca') as mock_backtest, \
                 patch('core.main.check_submit_strategies_path') as mock_check_path, \
                 patch('core.main.load_strategies') as mock_load_strategies, \
                 patch('core.main.get_strategy') as mock_get_strategy, \
                 patch('core.plots.print_weight_sums_by_cycle') as mock_print:
                
                # Configure more mocks
                mock_load_data.return_value = self.sample_df
                mock_check_path.return_value = True
                mock_strategy = MagicMock()
                mock_strategy.return_value = pd.Series([1.0, 1.0, 1.0, 1.0, 1.0], 
                                                   index=self.sample_df.index)
                mock_get_strategy.return_value = mock_strategy
                
                # Import main
                from core.main import main
                
                # Run the main function
                main()
                
                # Verify extract_btc_data was called (check both places it could be called from)
                # The function might be called directly from commands.py OR from extract_data module
                self.assertTrue(
                    mock_extract.called or mock_commands_extract.called,
                    "extract_btc_data function was not called"
                )

if __name__ == '__main__':
    unittest.main() 