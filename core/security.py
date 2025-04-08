"""
Security module for managing execution and validation of strategies.

This module is maintained for backward compatibility.
All functionality is now provided by the core.security package.
"""

# Re-export everything from the security package
from core.security import (
    SecurityError,
    ResourceMonitor,
    ImportHook,
    ComplexityAnalyzer,
    DataFlowAnalyzer,
    StrategySecurity,
    secure_strategy,
    validate_strategy_file,
    is_test_mode,
    ALLOWED_MODULES,
    ALLOWED_OS_FUNCTIONS,
    ALLOWED_DATA_SOURCES,
    MAX_MEMORY_MB,
    MAX_CPU_TIME,
    MAX_EXECUTION_TIME,
    MAX_CYCLOMATIC_COMPLEXITY,
    MAX_NESTED_DEPTH,
    MAX_FUNCTION_COMPLEXITY,
    MAX_MODULE_COMPLEXITY,
    TEST_MAX_CPU_TIME,
    TEST_MAX_EXECUTION_TIME
)

# For backward compatibility
def validate_external_data(url):
    """Backward compatibility function for validating external data sources"""
    return StrategySecurity.validate_external_data(url)

def analyze_ast(code):
    """Backward compatibility function for analyzing AST"""
    return StrategySecurity.analyze_ast(code) 