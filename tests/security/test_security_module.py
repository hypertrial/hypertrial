import pytest
import os
from unittest.mock import patch, MagicMock

from core.security import (
    SecurityError,
    StrategySecurity,
    validate_strategy_file,
    secure_strategy,
)


def test_strategy_security_methods():
    """Test that StrategySecurity class has expected methods"""
    # Check the actual methods that exist
    assert hasattr(StrategySecurity, 'secure_strategy')
    assert hasattr(StrategySecurity, 'analyze_ast')


def test_validate_strategy_file():
    """Test the validate_strategy_file functionality with proper mocking"""
    # Create a mock file that "exists"
    test_file = 'test_strategy.py'
    
    # Mock os.path.exists to return True for our test file
    with patch('os.path.exists', return_value=True), \
         patch('os.path.getsize', return_value=5 * 1024), \
         patch('builtins.open', MagicMock()), \
         patch('core.security.strategy_security.StrategySecurity.analyze_ast'), \
         patch('core.security.utils.logger'), \
         patch('core.security.utils.re.search', return_value=None), \
         patch('core.security.utils.is_test_mode', return_value=True), \
         patch('core.security.bandit_analyzer.BanditAnalyzer') as mock_bandit:
        
        # Configure mock Bandit analyzer
        mock_bandit_instance = mock_bandit.return_value
        mock_bandit_instance.analyze.return_value = (True, [])
        mock_bandit_instance.get_summary.return_value = {
            'issues_count': 0,
            'high_severity_count': 0,
            'medium_severity_count': 0,
            'low_severity_count': 0
        }
        
        # Call the function
        result = validate_strategy_file(test_file)
        
        # In the actual implementation, validate_strategy_file doesn't return anything
        # and will only raise an exception if validation fails
        assert result is None


def test_secure_strategy_existence():
    """Test that secure_strategy exists and is callable"""
    # Simple test to verify the secure_strategy decorator exists
    assert callable(secure_strategy)
    
    # Test that it can be applied to a function without error
    try:
        # Define a simple strategy function
        @secure_strategy
        def simple_strategy(df):
            return df
    except Exception as e:
        pytest.fail(f"secure_strategy decorator raised an exception: {e}")


def test_security_module_imports():
    """Test that all expected symbols are exported from the security module"""
    import core.security
    
    # Check that all expected symbols are exported
    expected_symbols = [
        'SecurityError',
        'ResourceMonitor',
        'ImportHook',
        'ComplexityAnalyzer',
        'DataFlowAnalyzer',
        'StrategySecurity',
        'secure_strategy',
        'validate_strategy_file',
        'is_test_mode',
        'ALLOWED_MODULES',
        'ALLOWED_OS_FUNCTIONS',
        'ALLOWED_DATA_SOURCES',
        'MAX_MEMORY_MB',
        'MAX_CPU_TIME',
        'MAX_EXECUTION_TIME',
        'MAX_CYCLOMATIC_COMPLEXITY',
        'MAX_NESTED_DEPTH',
        'MAX_FUNCTION_COMPLEXITY',
        'MAX_MODULE_COMPLEXITY',
        'TEST_MAX_CPU_TIME',
        'TEST_MAX_EXECUTION_TIME'
    ]
    
    for symbol in expected_symbols:
        assert hasattr(core.security, symbol), f"Symbol {symbol} not exported from core.security"


def test_analyze_ast_additional_cases():
    """Test additional edge cases in analyze_ast method"""
    from core.security import SecurityError
    from core.security.strategy_security import StrategySecurity
    
    # Test handling of external data access using a direct DataFrame write operation
    external_data_code = """
import pandas as pd
df = pd.DataFrame()
df.to_json('output.json')  # This is a banned write operation
"""
    try:
        StrategySecurity.analyze_ast(external_data_code)
        assert False, "Should raise SecurityError for DataFrame write operation"
    except SecurityError:
        pass

    # Test handling of DataFrame write operations
    dataframe_write_code = """
import pandas as pd
df = pd.DataFrame()
df.to_excel('output.xlsx')  # This is a banned write operation
"""
    try:
        StrategySecurity.analyze_ast(dataframe_write_code)
        assert False, "Should raise SecurityError for DataFrame write operation"
    except SecurityError:
        pass
    
    # Test forbidden module imports that are explicitly banned
    forbidden_import_code = """
import subprocess
subprocess.call(['ls'])
"""
    try:
        StrategySecurity.analyze_ast(forbidden_import_code)
        assert False, "Should raise SecurityError for forbidden module import"
    except SecurityError:
        pass


def test_validate_external_data_additional_cases():
    """Test additional edge cases for validate_external_data method"""
    from core.security import SecurityError
    from core.security.strategy_security import StrategySecurity
    
    # Test valid URL
    valid_url = "https://api.coinmetrics.io/v4/timeseries/asset-metrics"
    try:
        StrategySecurity.validate_external_data(valid_url)
    except SecurityError:
        assert False, "Should not raise SecurityError for allowed domain"
    
    # Test invalid protocol
    invalid_protocol_url = "file:///etc/passwd"
    try:
        StrategySecurity.validate_external_data(invalid_protocol_url)
        assert False, "Should raise SecurityError for invalid protocol"
    except SecurityError:
        pass
    
    # Test suspicious URL patterns
    suspicious_url = "https://example.com/..%2f..%2fetc/passwd"
    try:
        StrategySecurity.validate_external_data(suspicious_url)
        assert False, "Should raise SecurityError for suspicious URL pattern"
    except SecurityError:
        pass 