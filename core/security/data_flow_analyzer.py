"""Data flow analyzer for security validation."""

import ast
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            parent_vars = info.get('parent_vars', [])
            # Handle empty parent_vars array
            if not parent_vars:
                return "derived from unknown sources"
            
            # Filter out None values and ensure there are valid parents
            valid_parents = [parent for parent in parent_vars if parent is not None]
            if not valid_parents:
                return "derived from unknown sources"
            
            # Process each parent and handle potential None values
            parent_chains = []
            for parent in valid_parents:
                chain = self._get_source_chain(parent)
                if chain is not None:
                    parent_chains.append(chain)
                else:
                    parent_chains.append("unknown")
                
            # Make sure we have at least one item
            if not parent_chains:
                return "derived from unknown sources"
            
            return f"derived from {', '.join(parent_chains)}"
        
        return "unknown source"
    
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