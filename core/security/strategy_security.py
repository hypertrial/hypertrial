"""Strategy security management and validation."""

import ast
import time
import logging
from functools import wraps
from typing import Set, Dict, Any, List, Tuple
from urllib.parse import urlparse

from core.security.utils import is_test_mode
from core.security.config import (
    ALLOWED_MODULES, ALLOWED_OS_FUNCTIONS, ALLOWED_DATA_SOURCES
)
from core.security.complexity_analyzer import ComplexityAnalyzer
from core.security.data_flow_analyzer import DataFlowAnalyzer
from core.security.resource_monitor import ResourceMonitor
from core.security.import_hook import ImportHook

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategySecurity:
    """Main security class for strategy validation"""
    
    @staticmethod
    def analyze_ast(code: str) -> None:
        """Analyze the AST of the strategy code for security issues"""
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
        tree = ast.parse(code)
        
        # Run complexity analysis
        complexity_analyzer = ComplexityAnalyzer(code)
        complexity_analyzer.analyze()
        
        # Get complexity summary for additional checks
        complexity_summary = complexity_analyzer.get_complexity_summary()
        
        # Run data flow analysis
        data_flow_analyzer = DataFlowAnalyzer(code)
        data_flow_analyzer.analyze()
        
        # Track variable assignments and their sources for deeper analysis
        variable_sources = {}
        sensitive_operations = set()
        external_data_access = set()
        
        # Track disallowed os attribute usage
        def is_allowed_os_function(node):
            """Check if an os module function call is in the allowed list"""
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == 'os':
                    # Allow os.path.*
                    if node.attr == 'path':
                        return True
                    # Allow makedirs
                    if node.attr == 'makedirs':
                        return True
                    # Block all other os attributes
                    return False
            return True
        
        def is_allowed_os_path_call(node):
            """Check if an os.path function call is in the allowed list"""
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check for os.path.* calls
                    if isinstance(node.func.value, ast.Attribute) and isinstance(node.func.value.value, ast.Name):
                        if node.func.value.value.id == 'os' and node.func.value.attr == 'path':
                            # Get the full function name: os.path.join, etc.
                            full_func_name = f"os.path.{node.func.attr}"
                            return full_func_name in ALLOWED_OS_FUNCTIONS
                    # Check for os.makedirs calls        
                    elif isinstance(node.func.value, ast.Name) and node.func.value.id == 'os':
                        full_func_name = f"os.{node.func.attr}"
                        return full_func_name in ALLOWED_OS_FUNCTIONS
            return True
        
        # Track variable assignments for data flow analysis
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Record the source of this variable
                        variable_sources[target.id] = StrategySecurity._get_value_source(node.value)
        
        # Check for dangerous operations and suspicious patterns
        for node in ast.walk(tree):
            # Check for dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in {'eval', 'exec', 'open', 'system'}:
                        raise SecurityError(f"Dangerous function call detected: {node.func.id}")
                    sensitive_operations.add(node.func.id)
                
                # Track method calls
                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in {'eval', 'exec', 'system', 'query', 'execute'}:
                        sensitive_operations.add(f"{StrategySecurity._get_attr_source(node.func.value)}.{node.func.attr}")
                
                # Check os.* function calls
                if not is_allowed_os_path_call(node):
                    raise SecurityError(f"Disallowed os function call detected")
                
                # Check for external data access
                if StrategySecurity._is_external_data_access(node):
                    external_data_access.add(StrategySecurity._get_call_descriptor(node))
            
            # Check for dangerous os attribute access
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == 'os':
                    if not is_allowed_os_function(node):
                        raise SecurityError(f"Disallowed os module attribute: os.{node.attr}")
            
            # Check for dangerous imports
            if isinstance(node, ast.Import):
                for name in node.names:
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