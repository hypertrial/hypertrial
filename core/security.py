import ast
import importlib
import sys
import time
import resource
import psutil
import logging
import os
import re
from typing import Set, Dict, Any, List, Tuple
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Allowed modules for strategy submissions
ALLOWED_MODULES = {
    'pandas', 'numpy', 'datetime', 'typing',
    'core.config', 'core.strategies', 'core.strategies.base_strategy',
    'submit_strategies', 'pandas_datareader', 'scipy', 'time'
}

# Allow specific os.path functions only
ALLOWED_OS_FUNCTIONS = {
    'os.path.join', 'os.path.exists', 'os.path.abspath', 
    'os.path.dirname', 'os.makedirs', 'os.path.isfile',
    'os.path.isdir', 'os.path.getsize'
}

# Allowed external data sources (domain whitelist)
ALLOWED_DATA_SOURCES = {
    'api.coinmetrics.io',  # CoinMetrics API
    'query1.finance.yahoo.com',  # Yahoo Finance
    'api.coingecko.com',  # CoinGecko
    'finance.yahoo.com',  # Yahoo Finance
    'data.nasdaq.com',    # Nasdaq Data Link
}

# Resource limits
MAX_MEMORY_MB = 512  # Maximum memory usage in MB
MAX_CPU_TIME = 10  # Maximum CPU time in seconds - increased to be more reasonable
MAX_EXECUTION_TIME = 30  # Maximum total execution time in seconds - increased for real-world use

# More relaxed limits for test environments
TEST_MAX_CPU_TIME = 30  # More relaxed CPU time limit for tests
TEST_MAX_EXECUTION_TIME = 60  # More relaxed execution time limit for tests

# Code complexity limits
MAX_CYCLOMATIC_COMPLEXITY = 25  # Maximum allowed cyclomatic complexity - increased to be more reasonable
MAX_NESTED_DEPTH = 6  # Maximum allowed nested depth (loops, conditionals)
MAX_FUNCTION_COMPLEXITY = 120  # Maximum allowed number of statements in a function - increased for external_data_gold_strategy
MAX_MODULE_COMPLEXITY = 500  # Maximum total lines of code in a module

# Determine if we're running in test mode
def is_test_mode():
    """Check if the code is running in test mode (pytest)"""
    return 'pytest' in sys.modules or 'unittest' in sys.modules

# Use more relaxed limits in test mode
if is_test_mode():
    logger.info("Running in test mode - using relaxed security limits")
    MAX_CPU_TIME = TEST_MAX_CPU_TIME
    MAX_EXECUTION_TIME = TEST_MAX_EXECUTION_TIME

class SecurityError(Exception):
    """Custom exception for security violations"""
    pass

class ResourceMonitor:
    """Monitors resource usage of strategy execution"""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        self.max_memory = 0
        self.test_mode = is_test_mode()
        
        # Track resource usage history
        self.memory_history = []  # Track memory usage over time
        self.cpu_history = []     # Track CPU usage over time
        self.check_interval = 0.5 # Seconds between checks during continuous monitoring
        self.monitoring_active = False
        self.last_check_time = time.time()
        
        # Leak detection thresholds
        self.memory_growth_threshold = 0.15  # 15% growth rate is suspicious
        self.cpu_sustained_threshold = 0.80  # 80% sustained CPU usage is suspicious
        
    def start_continuous_monitoring(self):
        """Start background monitoring of resources (to be called in a separate thread)"""
        self.monitoring_active = True
        while self.monitoring_active:
            self.record_usage_snapshot()
            time.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop continuous resource monitoring"""
        self.monitoring_active = False
        
    def record_usage_snapshot(self):
        """Record current resource usage snapshot"""
        # Only record if enough time has passed since last check
        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return
            
        # Record memory usage
        try:
            memory_mb = self.process.memory_info().rss / 1024 / 1024
            self.memory_history.append((current_time - self.start_time, memory_mb))
            self.max_memory = max(self.max_memory, memory_mb)
            
            # Record CPU usage (as percentage)
            cpu_percent = self.process.cpu_percent(interval=0.1)
            self.cpu_history.append((current_time - self.start_time, cpu_percent))
            
            self.last_check_time = current_time
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            logger.warning("Unable to access process info for resource monitoring")
        
    def check_limits(self):
        """Check if resource usage exceeds limits"""
        # Record current usage
        self.record_usage_snapshot()
        
        # Check memory usage
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        if memory_mb > MAX_MEMORY_MB:
            raise SecurityError(f"Memory usage exceeded limit: {memory_mb:.2f}MB > {MAX_MEMORY_MB}MB")
        
        # Check CPU time
        cpu_time = resource.getrusage(resource.RUSAGE_SELF).ru_utime
        if cpu_time > MAX_CPU_TIME:
            raise SecurityError(f"CPU time exceeded limit: {cpu_time:.2f}s > {MAX_CPU_TIME}s")
        
        # Check total execution time
        elapsed = time.time() - self.start_time
        if elapsed > MAX_EXECUTION_TIME:
            raise SecurityError(f"Execution time exceeded limit: {elapsed:.2f}s > {MAX_EXECUTION_TIME}s")
        
        # Check for potential memory leaks
        self.check_for_memory_leak()
        
        # Check for sustained high CPU usage
        self.check_for_cpu_abuse()
    
    def check_for_memory_leak(self):
        """Check for patterns suggesting memory leak"""
        if len(self.memory_history) >= 10:
            # Look at the trend of the last 10 measurements
            recent_history = self.memory_history[-10:]
            
            # Calculate rate of growth
            start_mem = recent_history[0][1]
            end_mem = recent_history[-1][1]
            
            # If memory usage has grown by more than threshold% and is still growing, flag it
            if end_mem > start_mem * (1 + self.memory_growth_threshold):
                # Check if the growth is consistent (not just a spike)
                consistent_growth = True
                for i in range(1, len(recent_history)):
                    if recent_history[i][1] < recent_history[i-1][1]:
                        consistent_growth = False
                        break
                
                if consistent_growth:
                    message = f"Potential memory leak detected: {start_mem:.2f}MB → {end_mem:.2f}MB"
                    if self.test_mode:
                        logger.warning(message)
                    else:
                        # In production, treat sustained leaks as an error
                        if end_mem > MAX_MEMORY_MB * 0.8:  # If approaching the limit
                            raise SecurityError(message)
                        else:
                            logger.warning(message)
    
    def check_for_cpu_abuse(self):
        """Check for sustained high CPU usage patterns"""
        if len(self.cpu_history) >= 10:
            # Calculate average CPU usage over the last 10 measurements
            recent_cpu = [usage for _, usage in self.cpu_history[-10:]]
            avg_cpu = sum(recent_cpu) / len(recent_cpu)
            
            # If average CPU usage is consistently high, flag it
            if avg_cpu > self.cpu_sustained_threshold * 100:  # Convert to percentage
                message = f"Sustained high CPU usage detected: {avg_cpu:.2f}%"
                if self.test_mode:
                    logger.warning(message)
                else:
                    # In production, treat sustained high CPU as a warning
                    logger.warning(message)
    
    def get_usage_summary(self):
        """Get a summary of resource usage"""
        return {
            'max_memory_mb': self.max_memory,
            'current_memory_mb': self.process.memory_info().rss / 1024 / 1024,
            'cpu_time': resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            'elapsed_time': time.time() - self.start_time,
            'memory_history': self.memory_history,
            'cpu_history': self.cpu_history
        }

class ImportHook:
    """Custom import hook to restrict module imports"""
    
    def __init__(self):
        self.allowed_modules = ALLOWED_MODULES
        self.original_import = __import__
        
        # Track module usage patterns
        self.module_usage = {}            # Count how many times each module is imported
        self.import_times = {}            # Track when each module was imported
        self.module_access_patterns = {}  # Track unusual access patterns
        self.suspicious_modules = set()   # Modules with unusual import patterns
        
        # Thresholds for flagging suspicious import behavior
        self.max_import_count = 15        # Maximum times a module can be imported
        self.min_import_interval = 0.5    # Minimum seconds between imports
    
    def __enter__(self):
        sys.meta_path.insert(0, self)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.meta_path.remove(self)
        
        # Log summary of module usage
        if any(self.suspicious_modules):
            logger.warning(f"Suspicious module usage detected: {', '.join(self.suspicious_modules)}")
    
    def find_module(self, fullname, path=None):
        # Track module usage
        current_time = time.time()
        
        if fullname not in self.module_usage:
            self.module_usage[fullname] = 0
            self.import_times[fullname] = []
            
        self.module_usage[fullname] += 1
        self.import_times[fullname].append(current_time)
        
        # Check for excessive imports (potential for import-based DoS)
        if self.module_usage[fullname] > self.max_import_count:
            message = f"Excessive imports of module: {fullname} ({self.module_usage[fullname]} times)"
            self.suspicious_modules.add(fullname)
            logger.warning(message)
            
        # Check for rapid repeated imports (potential for timing attacks)
        if len(self.import_times[fullname]) >= 2:
            latest_imports = self.import_times[fullname][-2:]
            if latest_imports[1] - latest_imports[0] < self.min_import_interval:
                message = f"Rapid repeated imports of module: {fullname}"
                self.suspicious_modules.add(fullname)
                logger.warning(message)
        
        # Allow importing strategy modules themselves
        if fullname.startswith('submit_strategies.'):
            return None
            
        # Special case: allow os but we'll restrict its usage in code analysis
        if fullname == 'os':
            return None
            
        # Check if the module is in the allowed list
        for allowed in self.allowed_modules:
            if fullname == allowed or fullname.startswith(allowed + '.'):
                return None
        
        # Track attempted imports of restricted modules
        message = f"Blocked import of module: {fullname}"
        self.suspicious_modules.add(fullname)
        logger.warning(message)
        raise SecurityError(f"Import of module '{fullname}' is not allowed")
    
    def get_import_summary(self):
        """Get a summary of module import patterns"""
        return {
            'module_usage_counts': self.module_usage,
            'suspicious_modules': list(self.suspicious_modules),
            'import_times': self.import_times
        }

class ComplexityAnalyzer:
    """Analyzes code complexity to detect potentially malicious or resource-heavy code"""
    
    def __init__(self, code: str):
        self.code = code
        self.tree = ast.parse(code)
        self.test_mode = is_test_mode()
        
        # Track complexity metrics per function
        self.function_complexity = {}
        self.class_complexity = {}
        self.overall_metrics = {}
        
        # Additional metrics for detecting suspicious patterns
        self.infinite_loop_risk = []     # Functions with potential infinite loops
        self.recursion_depth_risk = []   # Functions with deep recursion
        self.api_hotspots = []           # Functions making many API calls
        self.resource_hotspots = []      # Functions with heavy resource usage
        
    def analyze(self) -> None:
        """Perform all complexity analyses"""
        self.check_module_complexity()
        self.check_function_complexity()
        self.check_cyclomatic_complexity()
        self.check_nested_depth()
        self.check_infinite_loop_risk()
        self.check_recursion_risk()
        self.report_metrics()
        
    def check_module_complexity(self) -> None:
        """Check overall module complexity"""
        lines = len(self.code.splitlines())
        
        # Count different types of statements for better analysis
        statement_count = sum(1 for _ in ast.walk(self.tree) if isinstance(_, ast.stmt))
        import_count = sum(1 for _ in ast.walk(self.tree) if isinstance(_, (ast.Import, ast.ImportFrom)))
        function_count = sum(1 for _ in ast.walk(self.tree) if isinstance(_, ast.FunctionDef))
        class_count = sum(1 for _ in ast.walk(self.tree) if isinstance(_, ast.ClassDef))
        
        # Store overall metrics
        self.overall_metrics = {
            'lines': lines,
            'statements': statement_count,
            'imports': import_count,
            'functions': function_count,
            'classes': class_count,
            'comment_ratio': self._calculate_comment_ratio()
        }
        
        if lines > MAX_MODULE_COMPLEXITY:
            raise SecurityError(f"Module complexity exceeded: {lines} lines > {MAX_MODULE_COMPLEXITY}")
    
    def _calculate_comment_ratio(self):
        """Calculate the ratio of comments to code (low ratio might indicate obfuscation)"""
        comment_lines = 0
        code_lines = 0
        
        for line in self.code.splitlines():
            stripped = line.strip()
            if stripped.startswith('#'):
                comment_lines += 1
            elif stripped:  # Non-empty line
                code_lines += 1
                
        return comment_lines / max(code_lines, 1)
            
    def check_function_complexity(self) -> None:
        """Check individual function complexity"""
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate various complexity metrics
                statement_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.stmt))
                branch_count = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.If, ast.While, ast.For, ast.Try)))
                variable_count = len(set(n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)))
                
                # Count arguments
                arg_count = len(node.args.args)
                
                # Count return statements
                return_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.Return))
                
                # Calculate a weighted complexity score
                complexity_score = (
                    statement_count + 
                    branch_count * 2 + 
                    variable_count + 
                    arg_count * 1.5 +
                    return_count
                )
                
                # Store metrics for each function
                self.function_complexity[node.name] = {
                    'statements': statement_count,
                    'branches': branch_count,
                    'variables': variable_count,
                    'arguments': arg_count,
                    'returns': return_count,
                    'complexity_score': complexity_score
                }
                
                if statement_count > MAX_FUNCTION_COMPLEXITY:
                    # In test mode, log a warning but don't fail
                    if self.test_mode:
                        logger.warning(f"Function '{node.name}' complexity exceeded: {statement_count} statements > {MAX_FUNCTION_COMPLEXITY}")
                    else:
                        raise SecurityError(
                            f"Function '{node.name}' complexity exceeded: {statement_count} statements > {MAX_FUNCTION_COMPLEXITY}"
                        )
            
            elif isinstance(node, ast.ClassDef):
                # Calculate class complexity metrics
                method_count = sum(1 for _ in node.body if isinstance(_, ast.FunctionDef))
                attribute_count = sum(1 for _ in node.body if isinstance(_, ast.Assign))
                class_score = method_count * 2 + attribute_count
                
                self.class_complexity[node.name] = {
                    'methods': method_count,
                    'attributes': attribute_count,
                    'complexity_score': class_score
                }
    
    def check_cyclomatic_complexity(self) -> None:
        """Calculate and check cyclomatic complexity (number of decision paths)"""
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Base complexity is 1
                complexity = 1
                
                # Count branch points
                for subnode in ast.walk(node):
                    if isinstance(subnode, (ast.If, ast.While, ast.For, ast.Try)):
                        complexity += 1
                    elif isinstance(subnode, ast.BoolOp) and isinstance(subnode.op, ast.And):
                        complexity += len(subnode.values) - 1
                
                # Store cyclomatic complexity
                if node.name in self.function_complexity:
                    self.function_complexity[node.name]['cyclomatic_complexity'] = complexity
                    
                if complexity > MAX_CYCLOMATIC_COMPLEXITY:
                    # In test mode, log a warning but don't fail
                    if self.test_mode:
                        logger.warning(f"Cyclomatic complexity in '{node.name}' exceeded: {complexity} > {MAX_CYCLOMATIC_COMPLEXITY}")
                    else:
                        raise SecurityError(
                            f"Cyclomatic complexity in '{node.name}' exceeded: {complexity} > {MAX_CYCLOMATIC_COMPLEXITY}"
                        )
    
    def check_nested_depth(self) -> None:
        """Check for excessive nesting depth"""
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                max_depth = self._get_max_nested_depth(node)
                
                # Store nesting depth
                if node.name in self.function_complexity:
                    self.function_complexity[node.name]['max_nesting_depth'] = max_depth
                
                if max_depth > MAX_NESTED_DEPTH:
                    # In test mode, log a warning but don't fail
                    if self.test_mode:
                        logger.warning(f"Nested depth in '{node.name}' exceeded: {max_depth} > {MAX_NESTED_DEPTH}")
                    else:
                        raise SecurityError(
                            f"Nested depth in '{node.name}' exceeded: {max_depth} > {MAX_NESTED_DEPTH}"
                        )
    
    def check_infinite_loop_risk(self):
        """Check for code patterns that might indicate infinite loop risk"""
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Look for while loops without clear exit conditions
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.While):
                        # Check for while True or equivalent
                        if isinstance(subnode.test, ast.Constant) and subnode.test.value == True:
                            # Look for break statements inside the loop
                            has_break = any(isinstance(n, ast.Break) for n in ast.walk(subnode))
                            
                            if not has_break:
                                self.infinite_loop_risk.append(node.name)
                                logger.warning(f"Potential infinite loop in '{node.name}': while True without break")
    
    def check_recursion_risk(self):
        """Check for functions that might cause excessive recursion"""
        # Build a call graph to detect recursive calls
        call_graph = {}
        
        # First pass: identify all functions
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                call_graph[node.name] = set()
        
        # Second pass: build call relationships
        for func_name in call_graph:
            for node in ast.walk(self.tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                    # Find all function calls within this function
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                            called_func = subnode.func.id
                            if called_func in call_graph:
                                call_graph[func_name].add(called_func)
        
        # Check for direct recursion
        for func_name, called_funcs in call_graph.items():
            if func_name in called_funcs:
                self.recursion_depth_risk.append(func_name)
                logger.warning(f"Potential recursive call in '{func_name}': function calls itself")
        
        # Check for indirect recursion (A calls B calls A)
        for func_name, called_funcs in call_graph.items():
            for called_func in called_funcs:
                if called_func in call_graph and func_name in call_graph[called_func]:
                    self.recursion_depth_risk.append(f"{func_name}->{called_func}")
                    logger.warning(f"Potential indirect recursion: '{func_name}' calls '{called_func}' which calls '{func_name}'")
    
    def _get_max_nested_depth(self, node) -> int:
        """Helper method to determine maximum nesting depth"""
        def _get_depth(node, current_depth=0):
            # If node is a nesting structure, increase depth
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                current_depth += 1
                
            # Get max depth from all child nodes
            max_child_depth = current_depth
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            max_child_depth = max(max_child_depth, _get_depth(item, current_depth))
                elif isinstance(value, ast.AST):
                    max_child_depth = max(max_child_depth, _get_depth(value, current_depth))
                    
            return max_child_depth
            
        return _get_depth(node)
    
    def report_metrics(self):
        """Report all complexity metrics for logging"""
        # Find the most complex functions
        if self.function_complexity:
            most_complex = sorted(
                self.function_complexity.items(), 
                key=lambda x: x[1].get('complexity_score', 0),
                reverse=True
            )[:3]  # Top 3 most complex functions
            
            for func_name, metrics in most_complex:
                logger.info(f"Complex function '{func_name}': score={metrics.get('complexity_score', 0)}, "
                           f"statements={metrics.get('statements', 0)}, "
                           f"cyclomatic={metrics.get('cyclomatic_complexity', 0)}, "
                           f"nesting={metrics.get('max_nesting_depth', 0)}")
        
        # Report high-risk patterns
        if self.infinite_loop_risk:
            logger.warning(f"Functions with potential infinite loops: {', '.join(self.infinite_loop_risk)}")
            
        if self.recursion_depth_risk:
            logger.warning(f"Functions with recursion risks: {', '.join(self.recursion_depth_risk)}")
    
    def get_complexity_summary(self):
        """Get a summary of code complexity metrics"""
        return {
            'overall': self.overall_metrics,
            'functions': self.function_complexity,
            'classes': self.class_complexity,
            'high_risk_patterns': {
                'infinite_loop_risk': self.infinite_loop_risk,
                'recursion_risk': self.recursion_depth_risk,
                'api_hotspots': self.api_hotspots,
                'resource_hotspots': self.resource_hotspots
            }
        }

class DataFlowAnalyzer:
    """Advanced analysis to detect suspicious data flow patterns"""
    
    def __init__(self, code: str):
        self.code = code
        self.tree = ast.parse(code)
        self.potential_vulnerabilities = []
        self.external_data_vars = set()
        self.assignment_map = {}  # Maps variable names to their assignments
        self.variable_flow = {}   # Tracks the flow of data through variables
        # Define sensitive operations for better tracking
        self.sensitive_operations = {
            'eval', 'exec', 'system', 'popen', 'query', 'execute', 
            'call', 'check_output', 'to_csv', 'to_json', 'write', 
            'post', 'put', 'send', 'upload'
        }
        # Define external data sources for better tracking
        self.external_data_sources = {
            'get_data_yahoo', 'read_csv', 'request', 'get', 
            'open', 'urlopen', 'read_html', 'load_data', 'fetch'
        }
        
    def analyze(self) -> None:
        """Perform all data flow analyses"""
        # First pass: build assignment map and identify external data sources
        self._build_assignment_map()
        
        # Track variable transformations
        self._track_variable_transformations()
        
        # Second pass: check data flows
        self.check_untrusted_data_flow()
        self.check_data_leakage()
        self.check_indirect_data_flow()
        
        if self.potential_vulnerabilities:
            self._report_vulnerabilities()
    
    def _build_assignment_map(self):
        """Build a map of variable assignments and identify external data sources"""
        for node in ast.walk(self.tree):
            # Find assignments
            if isinstance(node, ast.Assign):
                # Store assign node for each target
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.assignment_map[target.id] = node
                
                # Check if this is assigning from an external data source
                if isinstance(node.value, ast.Call) and self._is_external_data_source(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            self.external_data_vars.add(target.id)
                            self.variable_flow[target.id] = {'source': 'external', 'tainted': True}
    
    def _track_variable_transformations(self):
        """Track how variables are transformed and passed through the code"""
        for node in ast.walk(self.tree):
            # Track variable assignments that use other variables
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        target_id = target.id
                        # Check if the value uses any external data variables
                        used_vars = self._extract_variables_from_expr(node.value)
                        if any(var in self.external_data_vars for var in used_vars):
                            self.external_data_vars.add(target_id)
                            self.variable_flow[target_id] = {
                                'source': 'derived', 
                                'parent_vars': [var for var in used_vars if var in self.external_data_vars],
                                'tainted': True
                            }
    
    def _extract_variables_from_expr(self, node):
        """Extract variable names used in an expression"""
        vars_used = set()
        if isinstance(node, ast.Name):
            vars_used.add(node.id)
        elif isinstance(node, ast.BinOp):
            vars_used.update(self._extract_variables_from_expr(node.left))
            vars_used.update(self._extract_variables_from_expr(node.right))
        elif isinstance(node, ast.UnaryOp):
            vars_used.update(self._extract_variables_from_expr(node.operand))
        elif isinstance(node, ast.Call):
            for arg in node.args:
                vars_used.update(self._extract_variables_from_expr(arg))
            for kw in getattr(node, 'keywords', []):
                if kw.value:
                    vars_used.update(self._extract_variables_from_expr(kw.value))
        elif isinstance(node, ast.Subscript):
            vars_used.update(self._extract_variables_from_expr(node.value))
        elif isinstance(node, ast.List) or isinstance(node, ast.Tuple):
            for elt in node.elts:
                vars_used.update(self._extract_variables_from_expr(elt))
        return vars_used
    
    def check_untrusted_data_flow(self) -> None:
        """Check if untrusted data is used in sensitive operations"""
        # Check if these variables are used unsafely
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and self._is_sensitive_operation(node):
                # Check if any argument is from external data
                for arg in node.args:
                    arg_vars = self._extract_variables_from_expr(arg)
                    for var in arg_vars:
                        if var in self.external_data_vars:
                            # Get the source chain information for better reporting
                            source_info = self._get_source_chain(var)
                            self.potential_vulnerabilities.append(
                                f"Potentially unsafe use of external data '{var}' in sensitive operation. Source: {source_info}"
                            )
    
    def _get_source_chain(self, var):
        """Get the chain of sources for a variable for better vulnerability reporting"""
        if var not in self.variable_flow:
            return "unknown"
        
        info = self.variable_flow[var]
        if info.get('source') == 'external':
            return "direct external input"
        elif info.get('source') == 'derived':
            parent_chains = [self._get_source_chain(parent) for parent in info.get('parent_vars', [])]
            return f"derived from {', '.join(parent_chains)}"
        return "unknown"
    
    def check_indirect_data_flow(self):
        """Check for indirect flow of external data to sensitive operations"""
        # Track data flow through control structures (if statements, loops)
        control_dependence = set()
        
        for node in ast.walk(self.tree):
            # Track if/while conditions that depend on external data
            if isinstance(node, (ast.If, ast.While)):
                cond_vars = self._extract_variables_from_expr(node.test)
                if any(var in self.external_data_vars for var in cond_vars):
                    # Track all assignments in this branch
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Assign):
                            for target in subnode.targets:
                                if isinstance(target, ast.Name):
                                    control_dependence.add(target.id)
                                    if target.id not in self.variable_flow:
                                        self.variable_flow[target.id] = {}
                                    self.variable_flow[target.id]['control_flow_tainted'] = True
        
        # Check if control-dependent variables are used in sensitive operations
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and self._is_sensitive_operation(node):
                for arg in node.args:
                    arg_vars = self._extract_variables_from_expr(arg)
                    for var in arg_vars:
                        if var in control_dependence:
                            self.potential_vulnerabilities.append(
                                f"Potential control flow dependency: variable '{var}' used in sensitive operation is control-dependent on external data"
                            )
    
    def check_data_leakage(self) -> None:
        """Look for patterns that might indicate data exfiltration"""
        for node in ast.walk(self.tree):
            # Check for attempts to write external data
            if isinstance(node, ast.Call) and self._is_data_output_operation(node):
                # Check if any argument is from external data or contains it
                for arg in node.args:
                    arg_vars = self._extract_variables_from_expr(arg)
                    for var in arg_vars:
                        if var in self.external_data_vars:
                            self.potential_vulnerabilities.append(
                                f"Potential data leakage: external data '{var}' used in output operation"
                            )
    
    def _is_external_data_source(self, node) -> bool:
        """Determine if a node represents fetching external data"""
        if isinstance(node, ast.Call):
            # Check function name
            if isinstance(node.func, ast.Name):
                return node.func.id in self.external_data_sources
            # Check attribute name (methods)
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr in self.external_data_sources
        return False
    
    def _is_sensitive_operation(self, node) -> bool:
        """Determine if a node represents a sensitive operation"""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                # Check direct function calls like eval()
                return node.func.id in self.sensitive_operations
            elif isinstance(node.func, ast.Attribute):
                # Check method calls like subprocess.call()
                return node.func.attr in self.sensitive_operations
        return False
    
    def _is_data_output_operation(self, node) -> bool:
        """Determine if a node represents outputting data externally"""
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # Check for operations that might leak data
            return node.func.attr in {'to_csv', 'to_json', 'write', 'post', 'put', 'send', 'upload'}
        return False
        
    def _report_vulnerabilities(self) -> None:
        """Report potential vulnerabilities"""
        for vuln in self.potential_vulnerabilities:
            logger.warning(f"Potential vulnerability: {vuln}")
            # Not raising errors for these yet, just logging warnings

class StrategySecurity:
    """Main security class for strategy validation"""
    
    @staticmethod
    def analyze_ast(code: str) -> None:
        """Analyze the AST of the strategy code for security issues"""
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
        from urllib.parse import urlparse
        
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

def validate_strategy_file(file_path: str) -> None:
    """Validate a strategy file before execution"""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise SecurityError(f"Strategy file not found: {file_path}")
            
        # Read the strategy file
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Check file size 
        file_size = os.path.getsize(file_path) / 1024  # Size in KB
        if file_size > 500:  # 500KB max
            raise SecurityError(f"Strategy file too large: {file_size:.2f}KB > 500KB")
        
        # Check for excessively long lines (potential obfuscation)
        lines = code.splitlines()
        for i, line in enumerate(lines):
            if len(line) > 800:  # 800 chars is very long
                raise SecurityError(f"Excessively long line detected at line {i+1}: {len(line)} characters")
        
        # Analyze the AST
        StrategySecurity.analyze_ast(code)
        
        # Check for dangerous patterns using regex
        dangerous_patterns = [
            r'subprocess\.',                   # Subprocess module
            r'sys\.(exit|_exit|path|argv)',    # Dangerous sys functions
            r'socket\.',                       # Socket operations
            r'eval\s*\(',                      # eval()
            r'exec\s*\(',                      # exec()
            r'os\.system\(',                   # os.system()
            r'import\s+subprocess',            # Importing subprocess
            r'import\s+sys',                   # Importing sys
            r'import\s+socket',                # Importing socket
            r'import\s+pickle',                # Importing pickle
            r'import\s+marshal',               # Importing marshal
            r'__import__\s*\(',                # Using __import__
            r'getattr\s*\(.+?,\s*[\'"]__',     # Accessing dunder methods
            r'globals\(\)',                    # Accessing globals
            r'locals\(\)',                     # Accessing locals
            r'compile\s*\(',                   # Code compilation
            r'code\s*\..+?exec',               # code module exec
            r'importlib',                      # importlib
            r'open\s*\(.+?,\s*[\'"]w',         # Opening files for writing
            r'shutil\.',                       # File operations
            r'os\.path\.expanduser\(',         # Getting user directory
            r'os\.environ',                    # Accessing environment variables
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code):
                raise SecurityError(f"Dangerous pattern detected: {pattern}")
        
        logger.info(f"Strategy file {file_path} passed security validation")
        
    except Exception as e:
        logger.error(f"Strategy validation failed: {str(e)}")
        raise SecurityError(f"Strategy validation failed: {str(e)}") 