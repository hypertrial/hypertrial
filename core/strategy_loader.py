#!/usr/bin/env python3
"""
Strategy loading and management functionality for the Hypertrial framework.
"""
import os
import inspect
import importlib
import logging
import sys
from importlib import import_module
from core.security import StrategySecurity, SecurityError, validate_strategy_file
from core.strategies import load_strategies, get_strategy, list_strategies, _strategies
from core.spd import backtest_dynamic_dca

# Configure logging
logger = logging.getLogger(__name__)

def load_strategy_from_file(strategy_path):
    """
    Load a strategy from a file with security checks.
    
    Args:
        strategy_path (str): Path to the strategy file
        
    Returns:
        tuple: (strategy_name, strategy_fn, strategy_class)
    """
    if not os.path.exists(strategy_path):
        logger.error(f"Strategy file not found: {strategy_path}")
        return None, None, None
    
    # Validate the strategy file for security
    validate_strategy_file(strategy_path)
        
    try:
        # Generate a strategy name from the file name
        strategy_name = os.path.basename(strategy_path).replace('.py', '')
        logger.info(f"Loading strategy from file: {strategy_path}")
        
        # Import the module using importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(strategy_name, strategy_path)
        module = importlib.util.module_from_spec(spec)
        
        # Add the module to sys.modules so that @register_strategy works
        import sys
        sys.modules[strategy_name] = module
        
        # Get the registered strategies before loading
        from core.strategies import _strategies
        before_strategies = set(_strategies.keys())
        
        # Execute the module to register the strategy
        spec.loader.exec_module(module)
        
        # Find the newly registered strategy
        after_strategies = set(_strategies.keys())
        new_strategies = after_strategies - before_strategies
        
        if not new_strategies:
            logger.error(f"No registered strategy function found in {strategy_path}")
            logger.error("Make sure your strategy file contains a function decorated with @register_strategy")
            logger.error("Example: @register_strategy('my_strategy')")
            logger.error("def my_strategy(df): ...")
            return None, None, None
        
        # Use the newly registered strategy
        strategy_name = list(new_strategies)[0]
        strategy_fn = _strategies[strategy_name]
        logger.info(f"Successfully loaded strategy '{strategy_name}' from file: {strategy_path}")
        
        # Find strategy class for feature construction
        strategy_class = None
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, 'construct_features') and hasattr(obj, 'compute_weights'):
                strategy_class = obj
                break
        
        # Apply security wrapper
        strategy_fn = StrategySecurity.secure_strategy(strategy_fn)
        
        return strategy_name, strategy_fn, strategy_class
    except Exception as e:
        logger.error(f"Error loading strategy file: {str(e)}")
        return None, None, None

def find_strategy_class(strategy_name):
    """
    Find a strategy class by name from all available modules.
    
    Args:
        strategy_name (str): Name of the strategy
        
    Returns:
        class or None: Strategy class if found
    """
    # Special handling for tests with direct module mocking
    try:
        module = import_module("core.strategies")
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and hasattr(obj, 'construct_features') and hasattr(obj, 'compute_weights'):
                if name == strategy_name or strategy_name in name:
                    return obj
    except (ImportError, AttributeError):
        pass
        
    # Check in specific strategy modules
    for module_name in [f"core.strategies.{name}" for name in list_strategies().keys()]:
        try:
            module = import_module(module_name)
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, 'construct_features') and hasattr(obj, 'compute_weights'):
                    if name == strategy_name or strategy_name in name:
                        return obj
        except ImportError:
            continue
    
    # If not found, look in submit_strategies
    core_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(core_dir)
    submit_dir = os.path.join(root_dir, 'submit_strategies')
    
    if os.path.exists(submit_dir):
        for module_name in [f"submit_strategies.{name.replace('.py', '')}" for name in os.listdir(submit_dir) 
                        if name.endswith('.py') and not name.startswith('__')]:
            try:
                module = import_module(module_name)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and hasattr(obj, 'construct_features') and hasattr(obj, 'compute_weights'):
                        if name == strategy_name or strategy_name in name:
                            return obj
            except ImportError as e:
                logger.warning(f"Could not import {module_name}: {str(e)}")
                continue
    
    return None

def process_strategy_file(args):
    """
    Process a single strategy file for multiprocessing support.
    
    Args:
        args (tuple): (strategy_path, btc_df, show_plots)
        
    Returns:
        dict or None: Strategy results summary or None if processing failed
    """
    strategy_path, btc_df, show_plots = args
    
    if not os.path.exists(strategy_path):
        logger.error(f"Strategy file not found: {strategy_path}")
        return None
        
    try:
        # Validate the strategy file for security
        validate_strategy_file(strategy_path)
        
        # Generate a strategy name from the file name
        strategy_name = os.path.basename(strategy_path).replace('.py', '')
        logger.info(f"Backtesting strategy file: {strategy_path}")
        
        # Import the module using importlib
        import importlib.util
        spec = importlib.util.spec_from_file_location(strategy_name, strategy_path)
        module = importlib.util.module_from_spec(spec)
        
        # Add the module to sys.modules so that @register_strategy works
        import sys
        sys.modules[strategy_name] = module
        
        # Get the registered strategies before loading
        from core.strategies import _strategies
        before_strategies = set(_strategies.keys())
        
        # Execute the module to register the strategy
        spec.loader.exec_module(module)
        
        # Find the newly registered strategy
        after_strategies = set(_strategies.keys())
        new_strategies = after_strategies - before_strategies
        
        if not new_strategies:
            logger.error(f"No registered strategy function found in {strategy_path}")
            logger.error("Make sure your strategy file contains a function decorated with @register_strategy")
            return None
            
        # Use the newly registered strategy
        file_strategy_name = list(new_strategies)[0]
        strategy_fn = _strategies[file_strategy_name]
        
        # Apply security wrapper if needed
        from core.security import StrategySecurity
        strategy_fn = StrategySecurity.secure_strategy(strategy_fn)
        
        # Run backtest and collect results
        logger.info(f"Running backtest for strategy: {file_strategy_name}")
        df_res = backtest_dynamic_dca(btc_df, strategy_name=file_strategy_name, show_plots=show_plots)
        
        # Get the bandit threat level for this strategy
        from core.security.utils import get_bandit_threat_level
        bandit_threat = get_bandit_threat_level(strategy_path)
        
        # Create summary dict
        summary = {
            'strategy': file_strategy_name,
            'strategy_file': strategy_path,
            'min_spd': df_res['dynamic_spd'].min() if 'dynamic_spd' in df_res else 0.0,
            'max_spd': df_res['dynamic_spd'].max() if 'dynamic_spd' in df_res else 0.0,
            'avg_spd': df_res['dynamic_spd'].mean() if 'dynamic_spd' in df_res else 0.0,
            'median_spd': df_res['dynamic_spd'].median() if 'dynamic_spd' in df_res else 0.0,
            'min_excess_pct': df_res['excess_pct'].min() if 'excess_pct' in df_res else 0.0,
            'max_excess_pct': df_res['excess_pct'].max() if 'excess_pct' in df_res else 0.0, 
            'avg_excess_pct': df_res['excess_pct'].mean() if 'excess_pct' in df_res else 0.0,
            'median_excess_pct': df_res['excess_pct'].median() if 'excess_pct' in df_res else 0.0,
            'bandit_threat': bandit_threat,
            'raw_results': df_res  # Include the raw results for saving later
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error processing strategy file {strategy_path}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_strategy_file_with_timeout(args):
    """
    Process a strategy file with timeout protection to prevent hanging.
    
    Args:
        args (tuple): Same as process_strategy_file, plus timeout in seconds
        
    Returns:
        dict or None: Strategy results or None if processing failed or timed out
    """
    import signal
    from functools import wraps
    
    file_args, timeout = args
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Processing of {file_args[0]} timed out after {timeout} seconds")
    
    # Set the timeout handler
    original_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        # Process the file with the timeout
        result = process_strategy_file(file_args)
        return result
    except TimeoutError as e:
        logger.error(str(e))
        return None
    finally:
        # Cancel the alarm and restore the original handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler) 