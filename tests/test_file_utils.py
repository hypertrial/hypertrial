import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open, ANY

from core.file_utils import check_submit_strategies_path, find_strategy_files
from core.data import load_data

class TestFileUtils(unittest.TestCase):
    """Tests for file utility functions in core/file_utils.py"""
    
    def setUp(self):
        """Set up test environment and temporary directories"""
        # Create temporary directory for tests
        self.temp_dir = tempfile.mkdtemp()
        
        # Create subdirectories
        self.strategies_dir = os.path.join(self.temp_dir, "strategies")
        os.makedirs(self.strategies_dir, exist_ok=True)
        
        self.submit_dir = os.path.join(self.temp_dir, "submit_strategies")
        os.makedirs(self.submit_dir, exist_ok=True)
        
        # Create sample strategy files
        with open(os.path.join(self.strategies_dir, "strategy1.py"), "w") as f:
            f.write("# Test strategy 1")
        
        with open(os.path.join(self.strategies_dir, "strategy2.py"), "w") as f:
            f.write("# Test strategy 2")
        
        with open(os.path.join(self.submit_dir, "submit_strategy1.py"), "w") as f:
            f.write("# Test submit strategy 1")
        
        # Create a non-strategy file
        with open(os.path.join(self.strategies_dir, "not_a_strategy.txt"), "w") as f:
            f.write("This is not a strategy file")
    
    def tearDown(self):
        """Clean up temporary directory after tests"""
        shutil.rmtree(self.temp_dir)
    
    def create_empty_file(self, filepath):
        """Helper to create an empty file"""
        with open(filepath, 'w') as f:
            f.write("")
    
    @patch('core.file_utils.logger')
    @patch('os.path.exists')
    @patch('sys.path')
    def test_check_submit_strategies_path_exists(self, mock_sys_path, mock_exists, mock_logger):
        """Test check_submit_strategies_path when directory exists"""
        # Mock the directory exists
        mock_exists.return_value = True
        mock_sys_path.insert = MagicMock()
        
        # Call the function
        result = check_submit_strategies_path()
        
        # Verify the result
        self.assertTrue(result)
        # Verify logging was called
        mock_logger.info.assert_called()
    
    @patch('core.file_utils.logger')
    @patch('os.path.exists')
    def test_check_submit_strategies_path_not_exists(self, mock_exists, mock_logger):
        """Test check_submit_strategies_path when directory doesn't exist"""
        # Mock the directory doesn't exist
        mock_exists.return_value = False
        
        # Call the function
        result = check_submit_strategies_path()
        
        # Verify the result
        self.assertFalse(result)
        # Verify error logging was called
        mock_logger.error.assert_called()
    
    def test_find_strategy_files(self):
        """Test finding strategy files in both directories"""
        # Create a temporary directory structure for testing
        with patch('os.listdir') as mock_listdir:
            # Mock os.listdir to return our test files
            mock_listdir.return_value = ['strategy1.py', 'strategy2.py', 'not_a_strategy.txt']
            
            # Test calling the function with proper parameters
            all_files = find_strategy_files(root_dir=self.strategies_dir)
            
            # Verify correct files were found (should include .py files only)
            self.assertEqual(len(all_files), 2)  # Should find 2 .py files
            
            # Verify file paths are correct
            file_names = [os.path.basename(f) for f in all_files]
            self.assertIn('strategy1.py', file_names)
            self.assertIn('strategy2.py', file_names)
            self.assertNotIn('not_a_strategy.txt', file_names)
    
    @patch('pandas.read_csv')
    @patch('os.path.exists')
    def test_load_data(self, mock_exists, mock_read_csv):
        """Test loading BTC prices from CSV"""
        # Configure mocks
        mock_exists.return_value = True
        
        # Configure mock_read_csv to return a non-empty DataFrame
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.__len__.return_value = 100
        mock_df.index.min.return_value = '2010-01-01'
        mock_df.index.max.return_value = '2023-12-31'
        mock_read_csv.return_value = mock_df
        
        # Call function
        load_data()
        
        # Verify read_csv was called at least once with appropriate parameters
        mock_read_csv.assert_called()
        
        # Check that parameters include index_col and parse_dates in at least one call
        found_valid_call = False
        for call in mock_read_csv.call_args_list:
            args, kwargs = call
            if 'index_col' in kwargs and kwargs['index_col'] in [0, 'date']:
                if 'parse_dates' in kwargs and kwargs['parse_dates']:
                    found_valid_call = True
                    break
        
        self.assertTrue(found_valid_call, "No call to read_csv had proper parameters")

if __name__ == "__main__":
    unittest.main() 