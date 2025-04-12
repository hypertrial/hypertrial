import pytest
import os
import sys
from unittest.mock import patch, MagicMock, mock_open

from core.strategies.utils import load_strategy


def test_load_strategy_from_registry():
    """Test loading a strategy from the registry"""
    mock_strategy_func = MagicMock()
    
    # Patch the _strategies to include a test strategy
    with patch.dict('core.strategies._strategies', {'test_strategy': mock_strategy_func}, clear=True):
        # Call the function
        result = load_strategy('test_strategy')
        
        # Verify the result is the strategy function from the registry
        assert result == mock_strategy_func


def test_load_strategy_from_submit_strategies():
    """Test loading a strategy from the submit_strategies directory"""
    # Mock strategy function
    mock_strategy_func = MagicMock()
    
    # Set up all the patches we need at once
    with patch.dict('core.strategies._strategies', {}, clear=True), \
         patch('importlib.import_module') as mock_import, \
         patch('os.path.dirname') as mock_dirname, \
         patch('os.path.join', return_value='/mock/submit_strategies') as mock_join, \
         patch('os.listdir', return_value=['test_module.py']) as mock_listdir, \
         patch('sys.path', new=MagicMock()) as mock_path:
        
        # Create a mock module that contains the strategy function
        mock_module = MagicMock()
        setattr(mock_module, 'test_strategy', mock_strategy_func)
        mock_import.return_value = mock_module
        
        # Set up the paths correctly
        mock_dirname.return_value = '/mock/path'
        
        # Call the function
        result = load_strategy('test_strategy')
        
        # Verify the result is the strategy function from the module
        assert result == mock_strategy_func


def test_load_strategy_not_found():
    """Test that ValueError is raised when strategy is not found"""
    # Set up all the patches we need at once
    with patch.dict('core.strategies._strategies', {}, clear=True), \
         patch('importlib.import_module') as mock_import, \
         patch('os.path.dirname') as mock_dirname, \
         patch('os.path.join', return_value='/mock/submit_strategies') as mock_join, \
         patch('os.listdir', return_value=['test_module.py']) as mock_listdir, \
         patch('sys.path', new=MagicMock()):
         
        # Set up the mocks
        mock_import.side_effect = ImportError()
        mock_dirname.return_value = '/mock/path'
        
        # Call the function and verify ValueError is raised
        with pytest.raises(ValueError, match="Strategy 'nonexistent_strategy' not found"):
            load_strategy('nonexistent_strategy')


def test_load_strategy_directory_error():
    """Test handling of errors when accessing the submit_strategies directory"""
    # Patch the registry to be empty
    with patch.dict('core.strategies._strategies', {}, clear=True):
        # Mock os.listdir to raise an exception
        with patch('os.listdir', side_effect=FileNotFoundError()) as mock_listdir:
            # Mock print to capture error message
            with patch('builtins.print') as mock_print:
                # Call the function and verify ValueError is raised
                with pytest.raises(ValueError, match="Strategy 'test_strategy' not found"):
                    load_strategy('test_strategy')
                
                # Verify error message was printed
                mock_print.assert_called_once()
                assert "Error" in mock_print.call_args[0][0]


def test_load_strategy_import_error():
    """Test handling of import errors"""
    # Set up all the patches we need at once
    with patch.dict('core.strategies._strategies', {}, clear=True), \
         patch('importlib.import_module') as mock_import, \
         patch('os.path.dirname') as mock_dirname, \
         patch('os.path.join', return_value='/mock/submit_strategies') as mock_join, \
         patch('os.listdir', return_value=['test_module.py']) as mock_listdir, \
         patch('sys.path', new=MagicMock()), \
         patch('builtins.print') as mock_print:
         
        # Set up the mocks
        mock_import.side_effect = ImportError("Bad import")
        mock_dirname.return_value = '/mock/path'
        
        # Call the function and verify ValueError is raised
        with pytest.raises(ValueError, match="Strategy 'test_strategy' not found"):
            load_strategy('test_strategy')


def test_load_strategy_attribute_error():
    """Test handling of AttributeError when the module doesn't have the strategy function"""
    # Set up all the patches we need at once
    with patch.dict('core.strategies._strategies', {}, clear=True), \
         patch('importlib.import_module') as mock_import, \
         patch('os.path.dirname') as mock_dirname, \
         patch('os.path.join', return_value='/mock/submit_strategies') as mock_join, \
         patch('os.listdir', return_value=['test_module.py']) as mock_listdir, \
         patch('sys.path', new=MagicMock()):
         
        # Create a mock module that doesn't have the strategy function
        mock_module = MagicMock(spec=[])  # No strategy attribute
        mock_import.return_value = mock_module
        
        # Set up the paths correctly
        mock_dirname.return_value = '/mock/path'
        
        # Call the function and verify ValueError is raised
        with pytest.raises(ValueError, match="Strategy 'nonexistent_strategy' not found"):
            load_strategy('nonexistent_strategy') 