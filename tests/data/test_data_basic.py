import unittest
import os
import tempfile
import shutil
import pandas as pd
import sys
from unittest.mock import patch, MagicMock

class TestDataDownloadBasic(unittest.TestCase):
    """Basic tests for the data downloading functionality."""
    
    def setUp(self):
        """Setup for each test."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.temp_csv_path = os.path.join(self.temp_dir, 'TEST_ONLY_basic_btc_data_TESTING.csv')
        
        # Create a small sample dataframe for testing with very distinctive values
        self.sample_df = pd.DataFrame({
            'btc_close': [999.0, 998.0, 997.0, 996.0, 995.0]
        }, index=pd.date_range(start='2020-01-01', periods=5))
        
        # Save it to a CSV
        self.sample_df.to_csv(self.temp_csv_path)
    
    def tearDown(self):
        """Cleanup after each test."""
        # Remove temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_load_csv_with_different_separators(self):
        """Test loading CSV files with different separators."""
        # Import the load_data function after setting up the test files
        from core.data import load_data
        
        # Create different CSV files with different separators
        for sep, filename in zip([',', ';', '\t'], ['comma.csv', 'semicolon.csv', 'tab.csv']):
            filepath = os.path.join(self.temp_dir, filename)
            
            # Create a DataFrame with the right separator
            with open(filepath, 'w') as f:
                f.write(f"date{sep}btc_close\n")
                for i, date in enumerate(pd.date_range(start='2020-01-01', periods=5)):
                    f.write(f"{date.strftime('%Y-%m-%d')}{sep}{999-i}\n")
            
            # Try loading with the load_data function
            df = load_data(csv_path=filepath)
            
            # Verify it loads correctly
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 5)
            self.assertIn('btc_close', df.columns)
            self.assertEqual(df['btc_close'].iloc[0], 999.0)
    
    def test_cli_with_custom_data_file(self):
        """Test that the CLI respects the --data-file parameter."""
        # Import the main function to see if it works
        from core.main import parse_args
        
        # Create a mock for sys.argv
        with patch('sys.argv', ['core.main', '--data-file', self.temp_csv_path, '--no-plots']):
            args = parse_args()
            self.assertEqual(args.data_file, self.temp_csv_path)
    
    def test_download_data_flag(self):
        """Test that the --download-data flag is recognized."""
        # Import the parse_args function
        from core.main import parse_args
        
        # Create a mock for sys.argv
        with patch('sys.argv', ['core.main', '--download-data', '--no-plots']):
            args = parse_args()
            self.assertTrue(args.download_data)

if __name__ == '__main__':
    unittest.main() 