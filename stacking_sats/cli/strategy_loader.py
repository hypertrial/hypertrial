"""
Strategy loading utilities for the CLI.
"""
import os
import importlib
import inspect
from typing import List, Dict, Any, Type

from stacking_sats.strategies.base_strategy import BaseStrategy
from stacking_sats.core.logger import logger


def get_available_strategies() -> List[str]:
    """
    Return a list of available strategy classes.
    
    Returns:
        List of strategy names
    """
    # Get the path to the examples directory
    try:
        # Try importing the module to get its path
        import stacking_sats.strategies.examples as examples_module
        examples_dir = os.path.dirname(os.path.abspath(examples_module.__file__))
    except (ImportError, AttributeError):
        # Fallback to using the current file's location to find strategies directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(current_dir))
        examples_dir = os.path.join(base_dir, 'strategies', 'examples')
    
    # List all Python files in the examples directory
    try:
        strategy_files = [f for f in os.listdir(examples_dir) 
                         if f.endswith('_strategy.py') and not f.startswith('__')]
    except FileNotFoundError:
        logger.warning(f"Strategy examples directory not found: {examples_dir}")
        return []
    
    # Extract strategy names
    strategy_names = []
    for filename in strategy_files:
        # Get proper class name by converting file name to camel case
        name_parts = filename[:-3].split('_')  # Remove .py and split
        class_name = ''.join(part.capitalize() for part in name_parts)
        strategy_names.append(class_name)
    
    return strategy_names


def load_strategy(strategy_name: str, **kwargs) -> BaseStrategy:
    """
    Dynamically load a strategy class by name and initialize it with given parameters.
    
    Args:
        strategy_name: Name of the strategy class
        **kwargs: Parameters to pass to the strategy constructor
    
    Returns:
        Initialized strategy instance
        
    Raises:
        ValueError: If strategy cannot be found or initialized
    """
    # First try to import from examples
    try:
        module = importlib.import_module(f"stacking_sats.strategies.examples")
        strategy_class = getattr(module, strategy_name)
    except (ImportError, AttributeError):
        # If not in examples, try importing directly
        try:
            module_path = f"stacking_sats.strategies.examples.{strategy_name.lower()}_strategy"
            module = importlib.import_module(module_path)
            # Find the strategy class in the module
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                    strategy_class = obj
                    break
            else:
                raise ValueError(f"Could not find strategy class in {module_path}")
        except (ImportError, AttributeError) as e:
            # Try looking in the user's strategies directory
            try:
                # First try to find the user's strategies directory
                from stacking_sats.core.config.config_manager import ConfigManager
                config = ConfigManager()
                user_strategies_dir = config.get("data", "user_strategies_dir", 
                                                default=os.path.expanduser("~/.stacking_sats/strategies"))
                
                if os.path.exists(user_strategies_dir):
                    # Look for the strategy file
                    strategy_filename = f"{strategy_name.lower()}_strategy.py"
                    strategy_path = os.path.join(user_strategies_dir, strategy_filename)
                    
                    if os.path.exists(strategy_path):
                        # Load the module from file
                        spec = importlib.util.spec_from_file_location(
                            f"user_strategy.{strategy_name.lower()}_strategy", 
                            strategy_path
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # Find the strategy class
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                                strategy_class = obj
                                break
                        else:
                            raise ValueError(f"Could not find strategy class in {strategy_path}")
                    else:
                        raise ValueError(f"Strategy file not found: {strategy_path}")
                else:
                    raise ValueError(f"User strategies directory not found: {user_strategies_dir}")
            except Exception as user_strategy_error:
                # Combine the original error with the user strategy error
                raise ValueError(f"Strategy '{strategy_name}' not found. Original error: {e}. "
                               f"Also failed to load as user strategy: {user_strategy_error}")
    
    # Initialize the strategy with provided parameters
    try:
        return strategy_class(**kwargs)
    except Exception as e:
        raise ValueError(f"Error initializing strategy '{strategy_name}': {e}")


def get_strategy_parameters(strategy_name: str) -> Dict[str, Any]:
    """
    Get default parameters for a strategy.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Dictionary of parameter names and default values
        
    Raises:
        ValueError: If strategy cannot be found
    """
    try:
        # Load the strategy class definition
        module_path = f"stacking_sats.strategies.examples.{strategy_name.lower()}_strategy"
        module = importlib.import_module(module_path)
        
        # Find the strategy class
        strategy_class = None
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, BaseStrategy) and obj != BaseStrategy:
                strategy_class = obj
                break
        
        if strategy_class is None:
            raise ValueError(f"Could not find strategy class in {module_path}")
        
        # Get parameter defaults from __init__ signature
        params = {}
        signature = inspect.signature(strategy_class.__init__)
        for param_name, param in signature.parameters.items():
            if param_name not in ('self', 'args', 'kwargs') and param.default is not inspect.Parameter.empty:
                params[param_name] = param.default
        
        return params
    except Exception as e:
        raise ValueError(f"Error getting parameters for strategy '{strategy_name}': {e}") 