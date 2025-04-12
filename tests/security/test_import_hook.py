"""Tests for the ImportHook security class."""

import sys
import pytest
from unittest.mock import patch, MagicMock
from core.security.import_hook import ImportHook
from core.security import SecurityError

class TestImportHook:
    """Tests for ImportHook class"""
    
    def test_init(self):
        """Test ImportHook initialization"""
        hook = ImportHook()
        assert isinstance(hook.module_usage, dict)
        assert isinstance(hook.import_times, dict)
        assert isinstance(hook.suspicious_modules, set)
        assert hook.max_import_count > 0
        assert hook.min_import_interval > 0
    
    def test_enter_exit(self):
        """Test context manager functionality"""
        hook = ImportHook()
        
        # Check that __enter__ returns self
        assert hook.__enter__() is hook
        
        # Check that the hook is installed in sys.meta_path
        assert hook in sys.meta_path
        
        # Check that __exit__ removes the hook
        hook.__exit__(None, None, None)
        assert hook not in sys.meta_path
    
    def test_find_module_allowed(self):
        """Test find_module with allowed modules"""
        hook = ImportHook()
        
        # Test with allowed modules
        for module in ['pandas', 'numpy', 'core.strategies', 'submit_strategies.test_strategy', 'os']:
            result = hook.find_module(module)
            assert result is None  # None means allow standard import
            
            # Check that module usage is tracked
            assert module in hook.module_usage
            assert module in hook.import_times
            assert len(hook.import_times[module]) == 1
            assert hook.module_usage[module] == 1
    
    def test_find_module_blocked(self):
        """Test find_module with blocked modules"""
        hook = ImportHook()
        
        # Test with blocked modules
        for module in ['requests', 'subprocess', 'socket', 'urllib.request']:
            with pytest.raises(SecurityError, match=f"Import of module '{module}' is not allowed"):
                hook.find_module(module)
                
            # Check that module is tracked as suspicious
            assert module in hook.suspicious_modules
    
    def test_excessive_imports(self):
        """Test detection of excessive imports"""
        hook = ImportHook()
        
        # Set low threshold for testing
        hook.max_import_count = 3
        
        # Import the same module multiple times
        for _ in range(3):
            hook.find_module('pandas')
        
        # Next import should trigger warning but not block
        with patch('logging.Logger.warning') as mock_warning:
            hook.find_module('pandas')
            # Since we'll get two warnings (one for excessive and one for rapid)
            # Just verify it was called at least once
            assert mock_warning.call_count >= 1
        
        # Check that module is tracked as suspicious
        assert 'pandas' in hook.suspicious_modules
    
    def test_rapid_imports(self):
        """Test detection of rapid repeated imports"""
        hook = ImportHook()
        
        # Set high min interval for testing
        hook.min_import_interval = 1.0  # 1 second
        
        # First import
        hook.find_module('numpy')
        
        # Second import immediately after (should be flagged as rapid)
        with patch('logging.Logger.warning') as mock_warning:
            hook.find_module('numpy')
            mock_warning.assert_called_once()
        
        # Check that module is tracked as suspicious
        assert 'numpy' in hook.suspicious_modules
    
    def test_get_import_summary(self):
        """Test getting import summary"""
        hook = ImportHook()
        
        # Track some module usage
        hook.module_usage = {'pandas': 2, 'numpy': 1, 'requests': 1}
        hook.suspicious_modules = {'requests'}
        
        # Get summary
        summary = hook.get_import_summary()
        
        # Check summary contents - using the actual keys from the implementation
        assert 'module_usage_counts' in summary
        assert summary['module_usage_counts'] == {'pandas': 2, 'numpy': 1, 'requests': 1}
        
        assert 'suspicious_modules' in summary
        assert set(summary['suspicious_modules']) == {'requests'}
        
        assert 'import_times' in summary
    
    def test_multiple_hooks(self):
        """Test behavior with multiple hooks"""
        # Create two hooks
        hook1 = ImportHook()
        hook2 = ImportHook()
        
        # Install both
        with hook1, hook2:
            assert hook1 in sys.meta_path
            assert hook2 in sys.meta_path
        
        # Both should be removed
        assert hook1 not in sys.meta_path
        assert hook2 not in sys.meta_path 