"""
Security package for managing execution and validation of strategies.

This package includes components for:
- Resource monitoring (memory, CPU)
- Code complexity analysis
- AST-based security checks
- Data flow analysis
- Import security
- Bandit static code security analysis
"""

# Import key components
from core.security.resource_monitor import ResourceMonitor
from core.security.import_hook import ImportHook
from core.security.complexity_analyzer import ComplexityAnalyzer
from core.security.data_flow_analyzer import DataFlowAnalyzer
from core.security.strategy_security import StrategySecurity
from core.security.bandit_analyzer import BanditAnalyzer
from core.security.config import (
    ALLOWED_MODULES, ALLOWED_OS_FUNCTIONS, ALLOWED_DATA_SOURCES, BANNED_MODULES,
    MAX_MEMORY_MB, MAX_CPU_TIME, MAX_EXECUTION_TIME, 
    MAX_CYCLOMATIC_COMPLEXITY, MAX_NESTED_DEPTH, MAX_FUNCTION_COMPLEXITY,
    MAX_MODULE_COMPLEXITY, TEST_MAX_CPU_TIME, TEST_MAX_EXECUTION_TIME
)

# Define the error class for security violations
class SecurityError(Exception):
    """Custom exception for security violations"""
    pass

# Helper functions
from core.security.utils import is_test_mode, validate_strategy_file

# Export the decorator for easy access
from core.security.strategy_security import StrategySecurity
secure_strategy = StrategySecurity.secure_strategy

__version__ = "0.1.11"
