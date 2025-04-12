#!/usr/bin/env python3
"""
Utility script to validate strategy imports against allowed modules from requirements.txt.

This script analyzes a Python file to detect imports and checks if they're allowed
according to the security configuration.

Usage:
    python validate_strategy_imports.py <strategy_file.py>
"""

import ast
import os
import sys
import importlib.util
from typing import List, Set, Tuple

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import security config
try:
    from core.security.config import ALLOWED_MODULES, BANNED_MODULES
except ImportError:
    print("Error: Could not import security configuration.")
    print("Make sure you're running this script from the project root.")
    sys.exit(1)

def extract_imports(file_path: str) -> Tuple[Set[str], List[str]]:
    """
    Extract all imports from a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Tuple of (set of imported modules, list of error messages)
    """
    imports = set()
    errors = []
    
    try:
        with open(file_path, 'r') as f:
            code = f.read()
            
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            # Check for regular imports
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name.split('.')[0])  # Get the top-level module
            
            # Check for from imports
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])  # Get the top-level module
    except Exception as e:
        errors.append(f"Error parsing file: {str(e)}")
        
    return imports, errors

def validate_imports(imports: Set[str]) -> Tuple[bool, List[str]]:
    """
    Validate if all imports are allowed.
    
    Args:
        imports: Set of imported modules
        
    Returns:
        Tuple of (validation result, list of error messages)
    """
    valid = True
    errors = []
    
    for module in imports:
        # Skip standard library modules that are always allowed
        if module in {'os', 'sys', 'time', 'datetime', 'typing', 'math', 'random', 'collections', 're'}:
            continue
            
        # Check if module is explicitly banned
        if any(module == banned or module.startswith(banned + '.') for banned in BANNED_MODULES):
            valid = False
            errors.append(f"ERROR: Import of banned module '{module}' is not allowed")
            continue
            
        # Check if module is in allowed list
        if not any(module == allowed or module.startswith(allowed + '.') for allowed in ALLOWED_MODULES):
            valid = False
            errors.append(f"ERROR: Import of module '{module}' is not in the allowed list")
            
    return valid, errors

def check_module_availability(imports: Set[str]) -> List[str]:
    """
    Check if the imported modules are installed and available.
    
    Args:
        imports: Set of imported modules
        
    Returns:
        List of error messages for unavailable modules
    """
    errors = []
    
    for module in imports:
        # Skip checking built-in modules
        if module in {'os', 'sys', 'time', 'datetime', 'typing', 'math', 'random', 'collections', 're'}:
            continue
            
        # Try to find the module
        spec = importlib.util.find_spec(module)
        if spec is None:
            errors.append(f"WARNING: Module '{module}' is not installed. Make sure it's in requirements.txt and run pip install.")
            
    return errors

def print_result(valid: bool, errors: List[str], module_errors: List[str]) -> None:
    """Print validation results with colors."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    
    if valid and not module_errors:
        print(f"{GREEN}✓ All imports are allowed and available.{RESET}")
    else:
        if not valid:
            print(f"{RED}✗ Import validation failed.{RESET}")
            
        for error in errors:
            if error.startswith("ERROR"):
                print(f"{RED}{error}{RESET}")
            else:
                print(error)
                
        for error in module_errors:
            print(f"{YELLOW}{error}{RESET}")
            
    if valid and module_errors:
        print(f"\n{YELLOW}⚠ Strategy imports are valid, but some modules might not be installed.{RESET}")
        print(f"{YELLOW}  Run 'pip install --upgrade -r requirements.txt' to install all required packages.{RESET}")
    
def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_strategy_imports.py <strategy_file.py>")
        sys.exit(1)
        
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
        
    if not file_path.endswith('.py'):
        print(f"Error: '{file_path}' is not a Python file.")
        sys.exit(1)
        
    print(f"Validating imports in '{file_path}'...\n")
    
    imports, parse_errors = extract_imports(file_path)
    
    if parse_errors:
        for error in parse_errors:
            print(f"Error: {error}")
        sys.exit(1)
        
    print(f"Found imports: {', '.join(sorted(imports))}\n")
    
    valid, errors = validate_imports(imports)
    module_errors = check_module_availability(imports)
    
    print_result(valid, errors, module_errors)
    
    return 0 if valid else 1

if __name__ == "__main__":
    sys.exit(main()) 