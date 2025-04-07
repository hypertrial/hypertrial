# strategies/__init__.py
import os
import importlib
import inspect
from typing import Callable, Dict, Any

# Dictionary to store all available strategies
_available_strategies = {}

# Expose the strategies dictionary for testing
available_strategies = _available_strategies

def register_strategy(name: str = None):
    """
    Decorator to register a strategy function
    
    Args:
        name (str, optional): The name of the strategy. If None, the function name will be used.
    """
    def decorator(func: Callable):
        strategy_name = name or func.__name__
        _available_strategies[strategy_name] = func
        return func
    return decorator

def get_strategy(name: str) -> Callable:
    """
    Get a strategy by name
    
    Args:
        name (str): The name of the strategy
    
    Returns:
        Callable: The strategy function
    """
    if name not in _available_strategies:
        raise ValueError(f"Strategy '{name}' not found. Available strategies: {list(_available_strategies.keys())}")
    return _available_strategies[name]

def list_strategies() -> Dict[str, str]:
    """
    Get a list of all available strategies with their descriptions
    
    Returns:
        Dict[str, str]: A dictionary mapping strategy names to their docstrings
    """
    return {name: func.__doc__ or "No description available" 
            for name, func in _available_strategies.items()}

def load_strategies():
    """
    Load all strategy modules from the strategies directory
    """
    strategies_dir = os.path.dirname(os.path.abspath(__file__))
    for filename in os.listdir(strategies_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]  # Remove .py extension
            module = importlib.import_module(f'core.strategies.{module_name}')
            
            # Find all functions in the module with the register_strategy decorator
            for _, obj in inspect.getmembers(module):
                if callable(obj) and hasattr(obj, '__module__') and obj.__module__ == module.__name__:
                    # The function will be automatically registered if decorated
                    pass 