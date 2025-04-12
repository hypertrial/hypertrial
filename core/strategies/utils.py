"""
Utility functions for loading and managing strategies.
"""
import importlib
import os
import sys
import pandas as pd
from typing import Callable, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def load_strategy(strategy_name: str) -> Callable:
    """
    Load a strategy by name.
    
    Args:
        strategy_name: Name of the strategy to load
        
    Returns:
        Strategy function
        
    Raises:
        ValueError: If strategy not found
    """
    # First, check if it's in the registry
    from core.strategies import _strategies
    
    if strategy_name in _strategies:
        return _strategies[strategy_name]
    
    # Try to load from the submit_strategies directory
    try:
        submit_strategies_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'submit_strategies')
        sys.path.insert(0, submit_strategies_dir)
        
        # Try to find and import a module with the strategy name
        for file in os.listdir(submit_strategies_dir):
            if file.endswith('.py'):
                module_name = file[:-3]  # Remove .py extension
                try:
                    module = importlib.import_module(f"submit_strategies.{module_name}")
                    if hasattr(module, strategy_name):
                        return getattr(module, strategy_name)
                except (ImportError, AttributeError):
                    continue
    except Exception as e:
        print(f"Error looking for strategy in submit_strategies: {e}")
    
    raise ValueError(f"Strategy '{strategy_name}' not found") 