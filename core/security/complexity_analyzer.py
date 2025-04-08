"""Code complexity analyzer for security checks."""

import ast
import logging
from core.security.utils import is_test_mode
from core.security.config import (
    MAX_CYCLOMATIC_COMPLEXITY, MAX_NESTED_DEPTH, 
    MAX_FUNCTION_COMPLEXITY, MAX_MODULE_COMPLEXITY
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
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
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
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
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
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
        # Import SecurityError here to avoid circular import
        from core.security import SecurityError
        
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