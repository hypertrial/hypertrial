"""Utility functions for the security module."""

import os
import sys
import re
import logging
from core.security.config import ALLOWED_MODULES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_test_mode():
    """Check if the code is running in test mode (pytest)"""
    return 'pytest' in sys.modules or 'unittest' in sys.modules

def validate_strategy_file(file_path: str) -> None:
    """Validate a strategy file before execution"""
    from core.security import SecurityError
    from core.security.strategy_security import StrategySecurity
    
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