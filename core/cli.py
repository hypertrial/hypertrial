#!/usr/bin/env python3
"""
Hypertrial CLI entry point.
This module provides a clean entry point for the command-line interface
that avoids the circular import warnings that can occur with direct module execution.
"""
import sys
from core.main import main

def cli_main():
    """
    Command-line interface entry point that avoids the 
    'found in sys.modules after import of package' warning.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        main()
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(cli_main()) 