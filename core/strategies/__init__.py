# strategies/__init__.py
import os
import importlib
import logging
from typing import Dict, Any, Callable
from core.security import validate_strategy_file, StrategySecurity

logger = logging.getLogger(__name__)

# Dictionary to store registered strategies
_strategies: Dict[str, Callable] = {}

# Expose _strategies as available_strategies for backward compatibility
available_strategies = _strategies

def register_strategy(name: str) -> Callable:
    """Decorator to register a strategy with security checks"""
    def decorator(func: Callable) -> Callable:
        # Apply security decorator
        func = StrategySecurity.secure_strategy(func)
        
        # Register the strategy
        _strategies[name] = func
        logger.info(f"Registered strategy: {name}")
        return func
    return decorator

def load_strategies() -> None:
    """Load all strategies from both core/strategies and submit_strategies directories"""
    # Load core strategies first
    core_strategies_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Loading core strategies from: {core_strategies_dir}")
    
    # Load core strategies (no security validation needed)
    for filename in os.listdir(core_strategies_dir):
        if filename.endswith('.py') and not filename.startswith('__') and filename != 'base_strategy.py' and filename != 'utils.py':
            try:
                # Import the module
                module_name = f"core.strategies.{filename[:-3]}"
                importlib.import_module(module_name)
                logger.info(f"Successfully loaded core strategy from {filename}")
            except Exception as e:
                logger.error(f"Failed to load core strategy from {filename}: {str(e)}")
                continue
    
    # Load user-submitted strategies
    # Get path to project root directory (parent of core directory)
    core_dir = os.path.dirname(os.path.dirname(__file__))
    root_dir = os.path.dirname(core_dir)
    strategies_dir = os.path.join(root_dir, 'submit_strategies')
    
    logger.info(f"Loading user strategies from: {strategies_dir}")
    
    if not os.path.exists(strategies_dir):
        logger.error(f"User strategy directory not found: {strategies_dir}")
        return
    
    # Validate each user strategy file
    for filename in os.listdir(strategies_dir):
        if filename.endswith('.py') and not filename.startswith('__') and filename != 'strategy_template.py':
            file_path = os.path.join(strategies_dir, filename)
            try:
                # Validate the strategy file
                validate_strategy_file(file_path)
                
                # Import the module
                module_name = f"submit_strategies.{filename[:-3]}"
                importlib.import_module(module_name)
                
                logger.info(f"Successfully loaded user strategy from {filename}")
            except Exception as e:
                logger.error(f"Failed to load user strategy from {filename}: {str(e)}")
                continue
                
    logger.info(f"Total strategies loaded: {len(_strategies)}")

def get_strategy(name: str) -> Callable:
    """Get a registered strategy by name"""
    if name not in _strategies:
        raise ValueError(f"Strategy '{name}' not found")
    return _strategies[name]

def list_strategies() -> Dict[str, str]:
    """List all registered strategies with their docstrings"""
    return {name: func.__doc__ or "No description" for name, func in _strategies.items()}

__version__ = "0.1.10"
