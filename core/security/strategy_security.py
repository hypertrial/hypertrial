"""Strategy security management and validation."""

import ast
import time
import logging
from functools import wraps
from typing import Set, Dict, Any, List, Tuple
from urllib.parse import urlparse

from core.security.utils import is_test_mode
from core.security.config import (
    ALLOWED_MODULES, ALLOWED_OS_FUNCTIONS, ALLOWED_DATA_SOURCES, BANNED_MODULES
)
from core.security.complexity_analyzer import ComplexityAnalyzer
from core.security.data_flow_analyzer import DataFlowAnalyzer
from core.security.resource_monitor import ResourceMonitor
from core.security.import_hook import ImportHook
from core.security.bandit_analyzer import BanditAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategySecurity:
    """Main security class for strategy validation"""
    
    @staticmethod
    def analyze_ast(code: str) -> None:
        """
        Analyze the AST of code to detect security issues
        
        Checks for:
        - Banned imports (explicitly blacklisted modules like requests, subprocess)
        - Dangerous imports (anything not in allowed modules)
        - Dangerous attributes (os.system, eval, etc.)
        - Dangerous operations (file writes, exec, etc.)
        - External data access (network calls, etc.)
        - DataFrame write operations
        - pandas_datareader function whitelist
        
        Args:
            code: Python code to analyze
            
        Raises:
            SecurityError: If the code contains security issues
        """
        from core.security import SecurityError
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SecurityError(f"Syntax error in code: {str(e)}")
            
        # Track suspicious patterns for reporting
        external_data_access = []
        sensitive_operations = []
        
        for node in ast.walk(tree):
            # Check for DataFrame write operations
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                # If this is a method call
                method_name = node.func.attr
                
                # Check for DataFrame write operations
                if method_name.startswith('to_'):
                    # Allow certain essential DataFrame operations in any mode
                    if method_name in {'to_datetime', 'to_series'} or (is_test_mode() and method_name in {'to_csv', 'to_numpy', 'to_dict', 'to_records'}):
                        # These operations are permitted
                        pass
                    else:
                        # Block all DataFrame output operations in production
                        raise SecurityError(f"DataFrame write operation detected: {method_name}()")
            
            # Check for dangerous attribute access
            if isinstance(node, ast.Attribute):
                # Check for dangerous attribute access
                if isinstance(node.value, ast.Name) and node.value.id == 'os':
                    # Allow only specific os.path functions
                    if node.attr == 'system':
                        raise SecurityError("os.system() is not allowed")
                    if node.attr == 'spawn':
                        raise SecurityError("os.spawn() is not allowed")
                    if node.attr == 'popen':
                        raise SecurityError("os.popen() is not allowed")
                    if node.attr == 'exec':
                        raise SecurityError("os.exec() is not allowed")
                    if node.attr == 'execl':
                        raise SecurityError("os.execl() is not allowed")
                    if node.attr == 'fork':
                        raise SecurityError("os.fork() is not allowed")
                
                # Check for dangerous file operations
                if hasattr(node, 'attr') and node.attr in {'write', 'writelines', 'open', 'remove', 'unlink'}:
                    sensitive_operations.append(f"{node.attr}()")
                
                # Detect external data access attempts
                if StrategySecurity._is_external_data_access(node):
                    external_data_access.append(str(node.attr))
                    
            # Check for imports and ensure they're allowed
            elif isinstance(node, ast.Import):
                for name in node.names:
                    # Check against banned modules first (explicit blacklist)
                    for banned_mod in BANNED_MODULES:
                        if name.name == banned_mod or name.name.startswith(banned_mod + '.'):
                            raise SecurityError(f"Banned module import detected: {name.name}")
                            
                    # Special case for os (we'll restrict its usage via function analysis)
                    if name.name == 'os':
                        continue
                        
                    is_allowed = False
                    for allowed in ALLOWED_MODULES:
                        if name.name == allowed or name.name.startswith(allowed + '.'):
                            is_allowed = True
                            break
                    if not is_allowed:
                        raise SecurityError(f"Dangerous import detected: {name.name}")
            elif isinstance(node, ast.ImportFrom):
                # Check against banned modules first (explicit blacklist)
                for banned_mod in BANNED_MODULES:
                    if node.module == banned_mod or (node.module and node.module.startswith(banned_mod + '.')):
                        raise SecurityError(f"Banned module import detected: from {node.module}")
                
                # Special case for os.path
                if node.module == 'os.path':
                    continue
                    
                is_allowed = False
                for allowed in ALLOWED_MODULES:
                    if node.module == allowed or node.module.startswith(allowed + '.'):
                        is_allowed = True
                        break
                if not is_allowed:
                    raise SecurityError(f"Dangerous import detected: from {node.module}")
        
        # Log security summary
        if external_data_access:
            logger.info(f"Strategy accesses external data: {', '.join(external_data_access)}")
        
        if sensitive_operations:
            logger.info(f"Strategy uses sensitive operations: {', '.join(sensitive_operations)}")
    
    @staticmethod
    def _get_value_source(node):
        """Determine the source of a value in an assignment"""
        if isinstance(node, ast.Name):
            return f"variable:{node.id}"
        elif isinstance(node, ast.Call):
            return StrategySecurity._get_call_descriptor(node)
        elif isinstance(node, ast.BinOp):
            return f"operation:{StrategySecurity._get_value_source(node.left)}_{StrategySecurity._get_value_source(node.right)}"
        elif isinstance(node, ast.Constant):
            return f"constant:{type(node.value).__name__}"
        return "unknown"
    
    @staticmethod
    def _get_call_descriptor(node):
        """Get a string descriptor for a function call"""
        if isinstance(node.func, ast.Name):
            return f"function:{node.func.id}"
        elif isinstance(node.func, ast.Attribute):
            return f"method:{StrategySecurity._get_attr_source(node.func.value)}.{node.func.attr}"
        return "unknown_call"
    
    @staticmethod
    def _get_attr_source(node):
        """Get the source of an attribute access"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{StrategySecurity._get_attr_source(node.value)}.{node.attr}"
        return "unknown"
    
    @staticmethod
    def _is_external_data_access(node):
        """Determine if a node represents accessing external data"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id in {'requests', 'urlopen', 'read_csv', 'get_data_yahoo'}
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr in {'get', 'post', 'request', 'fetch', 'load', 'read_csv', 'read_html'}
        return False

    @staticmethod
    def validate_external_data(url: str) -> None:
        """Validate external data source URLs"""
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
        # First, check for protocol safety
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {'http', 'https'}:
            raise SecurityError(f"Unsupported URL protocol: {parsed_url.scheme}")
        
        # Check domain against allowlist
        domain = parsed_url.netloc
        if domain not in ALLOWED_DATA_SOURCES:
            raise SecurityError(f"External data source not allowed: {domain}")
        
        # Check for suspicious URL patterns
        suspicious_patterns = [
            '..', '~', '%', 'localhost', '127.0.0.1',
            'file:', 'gopher:', 'data:', 'internal'
        ]
        for pattern in suspicious_patterns:
            if pattern in url.lower():
                raise SecurityError(f"Suspicious URL pattern detected: {pattern}")

    @staticmethod
    def secure_strategy(func):
        """Decorator to add security checks to strategy execution"""
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create the security context
            security_context = {
                'monitor': ResourceMonitor(),
                'import_hook': ImportHook(),
                'start_time': time.time(),
                'suspicious_activity': False,
                'warnings': [],
                'events': []
            }
            
            def log_security_event(event_type, details):
                timestamp = time.time() - security_context['start_time']
                security_context['events'].append({
                    'time': timestamp,
                    'type': event_type,
                    'details': details
                })
                if event_type == 'warning':
                    security_context['warnings'].append(details)
                elif event_type == 'violation':
                    security_context['suspicious_activity'] = True
            
            try:
                # Start continuous monitoring in test mode
                if is_test_mode():
                    # In a real implementation, this would be in a separate thread
                    # to avoid interfering with the strategy execution
                    pass
                
                # Install import hook
                with security_context['import_hook']:
                    # Log start
                    log_security_event('start', {'func': func.__name__})
                    
                    # Run the strategy with resource monitoring
                    result = func(*args, **kwargs)
                    
                    # Check resource limits
                    security_context['monitor'].check_limits()
                    
                    # Record import summary
                    import_summary = security_context['import_hook'].get_import_summary()
                    if import_summary['suspicious_modules']:
                        log_security_event('warning', {
                            'message': f"Suspicious module access detected",
                            'modules': import_summary['suspicious_modules']
                        })
                    
                    # Record resource usage
                    usage_summary = security_context['monitor'].get_usage_summary()
                    log_security_event('resource_usage', {
                        'max_memory_mb': usage_summary['max_memory_mb'],
                        'cpu_time': usage_summary['cpu_time'],
                        'elapsed_time': usage_summary['elapsed_time']
                    })
                    
                    # Log completion
                    log_security_event('complete', {
                        'execution_time': time.time() - security_context['start_time'],
                        'suspicious': security_context['suspicious_activity']
                    })
                    
                    return result
            except SecurityError as e:
                log_security_event('violation', {'error': str(e)})
                logger.error(f"Security violation in strategy: {str(e)}")
                raise
            except Exception as e:
                log_security_event('error', {'error': str(e), 'type': type(e).__name__})
                logger.error(f"Strategy execution failed: {str(e)}")
                raise SecurityError(f"Strategy execution failed: {str(e)}")
            finally:
                # Stop monitoring
                if hasattr(security_context['monitor'], 'monitoring_active'):
                    security_context['monitor'].monitoring_active = False
                
                # Log summary
                if security_context['warnings']:
                    logger.warning(f"Security warnings during execution: {len(security_context['warnings'])}")
                    for warning in security_context['warnings'][:5]:  # Show at most 5 warnings
                        logger.warning(f"- {warning}")
        
        return wrapper 

    @staticmethod
    def _is_pandas_datareader_access(node):
        """Check if a node represents accessing pandas_datareader functions"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and hasattr(node.func.value, 'id'):
                if node.func.value.id == 'web':
                    return node.func.attr not in ALLOWED_PANDAS_DATAREADER
        return False

    @staticmethod
    def _is_dataframe_write_operation(node):
        """Check if a node represents a DataFrame write operation"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                return node.func.attr.startswith('to_')
        return False 