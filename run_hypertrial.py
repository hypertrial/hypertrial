#!/usr/bin/env python3
"""
Hypertrial entry point script.
Run strategies directly without module import warnings.
"""
import sys
import os
from core.main import main, parse_args

if __name__ == "__main__":
    # Run the main function directly
    main() 