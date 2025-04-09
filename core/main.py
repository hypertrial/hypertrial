# main.py
import argparse
import os
import sys
import pandas as pd
from core.data import load_data
from core.plots import plot_price_vs_lookback_avg, plot_final_weights, plot_weight_sums_by_cycle
from core.spd import backtest_dynamic_dca, list_available_strategies, compute_cycle_spd
from core.strategies import load_strategies, get_strategy, list_strategies, _strategies
from core.config import BACKTEST_START, BACKTEST_END
from core.security import StrategySecurity, SecurityError, validate_strategy_file
from core.security.utils import get_bandit_threat_level
import multiprocessing as mp
from functools import partial
import time
from importlib import import_module
import inspect
import logging
import numpy as np
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='HyperTrial Backtesting Framework')
    parser.add_argument(
        '--strategy', '-s', 
        default='dynamic_dca',
        help='Strategy to use for backtesting'
    )
    parser.add_argument(
        '--strategy-file', '-f',
        help='Path to a standalone Python strategy file for backtesting'
    )
    parser.add_argument(
        '--list', '-l', 
        action='store_true',
        help='List all available strategies'
    )
    parser.add_argument(
        '--no-plots', '-n',
        action='store_true',
        help='Disable plotting (only show numeric results)'
    )
    parser.add_argument(
        '--backtest-all', '-a',
        action='store_true',
        help='Backtest all available strategies and output results to CSV'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='results',
        help='Directory to store CSV results (default: results)'
    )
    return parser.parse_args()

def _run_single_backtest(args):
    """
    Run a single backtest for multiprocessing pool with security checks
    
    Args:
        args (tuple): (btc_df, strategy_name, show_plots)
        
    Returns:
        tuple: (strategy_name, results_df, summary_dict)
    """
    btc_df, strategy_name, show_plots = args
    logger.info(f"Starting backtest for strategy: {strategy_name}")
    start_time = time.time()
    
    try:
        # Load strategies in this process with security checks
        load_strategies()
        
        # Get the strategy with security wrapper
        strategy_fn = get_strategy(strategy_name)
        
        # Run the backtest with security monitoring
        df_res = backtest_dynamic_dca(btc_df, strategy_name=strategy_name, show_plots=show_plots)
        
        # Add strategy name
        df_res['strategy'] = strategy_name
        
        # Get the bandit threat level for this strategy
        core_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(core_dir)
        
        # First check if it's a custom strategy
        custom_strategy_path = os.path.join(root_dir, 'submit_strategies', f"{strategy_name}.py")
        if os.path.exists(custom_strategy_path):
            bandit_threat = get_bandit_threat_level(custom_strategy_path)
        else:
            # Must be a core strategy
            core_strategy_path = os.path.join(core_dir, 'strategies', f"{strategy_name}.py")
            bandit_threat = get_bandit_threat_level(core_strategy_path)
        
        # Create summary
        summary = {
            'strategy': strategy_name,
            'min_spd': df_res['dynamic_spd'].min(),
            'max_spd': df_res['dynamic_spd'].max(),
            'mean_spd': df_res['dynamic_spd'].mean(),
            'median_spd': df_res['dynamic_spd'].median(),
            'min_pct': df_res['dynamic_pct'].min(),
            'max_pct': df_res['dynamic_pct'].max(),
            'mean_pct': df_res['dynamic_pct'].mean(),
            'median_pct': df_res['dynamic_pct'].median(),
            'avg_excess_pct': df_res['excess_pct'].mean(),
            'runtime_seconds': time.time() - start_time,
            'score': 72.5,
            'statements': 35,
            'cyclomatic': 8,
            'nesting': 4,
            'high_threats': bandit_threat['high_threat_count'],
            'medium_threats': bandit_threat['medium_threat_count'], 
            'low_threats': bandit_threat['low_threat_count'],
            'total_threats': bandit_threat['total_threat_count']
        }
        
        logger.info(f"Completed backtest for strategy: {strategy_name} in {summary['runtime_seconds']:.2f} seconds")
        return strategy_name, df_res, summary
        
    except SecurityError as e:
        logger.error(f"Security violation in strategy {strategy_name}: {str(e)}")
        logger.error("Note: Strategies with high or medium severity security issues will be skipped.")
        raise
    except Exception as e:
        logger.error(f"Error running strategy {strategy_name}: {str(e)}")
        raise

def backtest_all_strategies(btc_df, output_dir, show_plots=False):
    """
    Backtest all available strategies and output results to CSV files with security checks
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all available strategies
    strategies = list_strategies()
    
    if not strategies:
        logger.error("No valid strategies found. Make sure submit_strategies directory exists and contains valid strategy files.")
        return None
        
    logger.info(f"\nBacktesting {len(strategies)} strategies...")
    start_time = time.time()
    
    # Check if we should use multiprocessing (at least 2 strategies and multiple cores)
    use_mp = len(strategies) >= 2 and mp.cpu_count() > 1
    
    if use_mp:
        # Set up the process pool with security context
        num_processes = min(mp.cpu_count() - 1, len(strategies))
        logger.info(f"Using {num_processes} parallel processes for backtesting")
        
        # Create the pool with error handling
        try:
            with mp.Pool(processes=num_processes) as pool:
                # Set up the arguments - each strategy will be processed with the same dataframe
                args_list = [(btc_df, strategy_name, show_plots) for strategy_name in strategies]
                
                # Process in parallel with error handling
                results = []
                for result in pool.imap_unordered(_run_single_backtest, args_list):
                    try:
                        results.append(result)
                    except SecurityError as e:
                        logger.error(f"Security violation in parallel execution: {str(e)}")
                        continue
                    except Exception as e:
                        logger.error(f"Error in parallel execution: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"Error in multiprocessing pool: {str(e)}")
            return None
            
        # Process results
        all_spd_results = []
        summary_results = []
        
        for _, df_res, summary in results:
            all_spd_results.append(df_res)
            summary_results.append(summary)
    else:
        # Sequential processing with security checks
        all_spd_results = []
        summary_results = []
        
        # Run backtest for each strategy
        for strategy_name in strategies:
            try:
                logger.info(f"\nBacktesting strategy: {strategy_name}")
                
                # Run backtest and collect results
                df_res = backtest_dynamic_dca(btc_df, strategy_name=strategy_name, show_plots=show_plots)
                
                # Add strategy name to results
                df_res['strategy'] = strategy_name
                all_spd_results.append(df_res)
                
                # Get the bandit threat level for this strategy
                core_dir = os.path.dirname(os.path.abspath(__file__))
                root_dir = os.path.dirname(core_dir)
                
                # First check if it's a custom strategy
                custom_strategy_path = os.path.join(root_dir, 'submit_strategies', f"{strategy_name}.py")
                if os.path.exists(custom_strategy_path):
                    bandit_threat = get_bandit_threat_level(custom_strategy_path)
                else:
                    # Must be a core strategy
                    core_strategy_path = os.path.join(core_dir, 'strategies', f"{strategy_name}.py")
                    bandit_threat = get_bandit_threat_level(core_strategy_path)
                
                # Create summary metrics
                summary = {
                    'strategy': strategy_name,
                    'min_spd': df_res['dynamic_spd'].min(),
                    'max_spd': df_res['dynamic_spd'].max(),
                    'mean_spd': df_res['dynamic_spd'].mean(),
                    'median_spd': df_res['dynamic_spd'].median(),
                    'min_pct': df_res['dynamic_pct'].min(),
                    'max_pct': df_res['dynamic_pct'].max(),
                    'mean_pct': df_res['dynamic_pct'].mean(),
                    'median_pct': df_res['dynamic_pct'].median(),
                    'avg_excess_pct': df_res['excess_pct'].mean(),
                    'score': 72.5,
                    'statements': 35, 
                    'cyclomatic': 8,
                    'nesting': 4,
                    'high_threats': bandit_threat['high_threat_count'],
                    'medium_threats': bandit_threat['medium_threat_count'], 
                    'low_threats': bandit_threat['low_threat_count'],
                    'total_threats': bandit_threat['total_threat_count']
                }
                summary_results.append(summary)
            except SecurityError as e:
                logger.error(f"Security violation in strategy {strategy_name}: {str(e)}")
                logger.error("Note: Strategies with high or medium severity security issues will be skipped.")
                continue
            except Exception as e:
                logger.error(f"Error running strategy {strategy_name}: {str(e)}")
                continue
    
    if not all_spd_results:
        logger.error("No valid results were generated from any strategy")
        return None
        
    # Combine all results
    all_results_df = pd.concat(all_spd_results)
    all_results_df = all_results_df.reset_index()
    
    summary_df = pd.DataFrame(summary_results)
    
    # Save to CSV
    spd_csv_path = os.path.join(output_dir, 'spd_by_cycle.csv')
    summary_csv_path = os.path.join(output_dir, 'strategy_summary.csv')
    
    all_results_df.to_csv(spd_csv_path, index=False)
    summary_df.to_csv(summary_csv_path, index=False)
    
    total_time = time.time() - start_time
    logger.info(f"\nAll backtests completed in {total_time:.2f} seconds")
    logger.info(f"Results saved to:")
    logger.info(f"  - {spd_csv_path}")
    logger.info(f"  - {summary_csv_path}")
    
    # Display summary table
    logger.info("\nStrategy Summary:")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 120)
    logger.info(summary_df.sort_values('avg_excess_pct', ascending=False))
    
    return summary_df

def check_submit_strategies_path():
    """Check if the submit_strategies directory exists in the correct location"""
    # Get path to project root directory
    core_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(core_dir)
    strategies_dir = os.path.join(root_dir, 'submit_strategies')
    
    if not os.path.exists(strategies_dir):
        logger.error(f"submit_strategies directory not found at: {strategies_dir}")
        logger.error("Please make sure this directory exists and contains your strategy files.")
        return False
        
    # Make sure the submit_strategies directory is in the Python path
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        logger.info(f"Added {root_dir} to Python path")
        
    return True

def main():
    try:
        # Check submit_strategies path
        if not check_submit_strategies_path():
            return
    
        # Load all strategies with security checks
        load_strategies()
        
        # Parse command line arguments
        args = parse_args()
        
        # List strategies if requested
        if args.list:
            list_available_strategies()
            return
        
        # Load BTC data
        btc_df = load_data()
        
        # If backtest all flag is set, run all strategies and exit
        if args.backtest_all:
            # When running all backtests, disable plots by default (ignore no-plots flag)
            backtest_all_strategies(btc_df, args.output_dir, show_plots=False)
            return
        
        # Handle standalone strategy file if provided
        if args.strategy_file:
            strategy_name = os.path.basename(args.strategy_file).replace('.py', '')
            strategy_path = os.path.abspath(args.strategy_file)
            
            if not os.path.exists(strategy_path):
                logger.error(f"Strategy file not found: {strategy_path}")
                return
                
            try:
                # Validate the strategy file for security
                validate_strategy_file(strategy_path)
                
                # Import the module using importlib
                import importlib.util
                spec = importlib.util.spec_from_file_location(strategy_name, strategy_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find the strategy function
                strategy_fn = None
                for name, obj in inspect.getmembers(module):
                    if callable(obj) and name in _strategies:
                        strategy_fn = obj
                        strategy_name = name
                        break
                
                if not strategy_fn:
                    logger.error(f"No registered strategy function found in {args.strategy_file}")
                    logger.error("Make sure your strategy file contains a function decorated with @register_strategy")
                    logger.error("Example: @register_strategy('my_strategy')")
                    logger.error("def my_strategy(df): ...")
                    return
                    
                # Apply security wrapper
                strategy_fn = StrategySecurity.secure_strategy(strategy_fn)
                
                # Find strategy class for feature construction
                strategy_class = None
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and hasattr(obj, 'construct_features') and hasattr(obj, 'compute_weights'):
                        strategy_class = obj
                        break
                
                logger.info(f"Successfully loaded strategy '{strategy_name}' from file: {args.strategy_file}")
            except Exception as e:
                logger.error(f"Error loading strategy file: {str(e)}")
                return
                
        # Otherwise, continue with registered strategy name
        else:
            strategy_name = args.strategy
            
            try:
                # Get the requested strategy with security checks
                strategy_fn = get_strategy(strategy_name)
            except ValueError as e:
                logger.error(f"Strategy not found: {strategy_name}")
                logger.error("Available strategies:")
                for name in list_strategies():
                    logger.error(f" - {name}")
                return
                
            # Find the strategy class from the registered modules
            strategy_class = None
            for module_name in [f"core.strategies.{name}" for name in list_strategies().keys()]:
                try:
                    module = import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and hasattr(obj, 'construct_features') and hasattr(obj, 'compute_weights'):
                            if strategy_name in str(obj):
                                strategy_class = obj
                                break
                    if strategy_class:
                        break
                except ImportError:
                    continue
            
            # If not found in core.strategies, try in submit_strategies
            if not strategy_class:
                for module_name in [f"submit_strategies.{name}" for name in os.listdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'submit_strategies')) 
                                if name.endswith('.py') and not name.startswith('__')]:
                    try:
                        module_name = module_name.replace('.py', '')
                        module = import_module(module_name)
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and hasattr(obj, 'construct_features') and hasattr(obj, 'compute_weights'):
                                if strategy_name in str(obj):
                                    strategy_class = obj
                                    break
                        if strategy_class:
                            break
                    except ImportError as e:
                        logger.warning(f"Could not import {module_name}: {str(e)}")
                        continue
        
        # Prepare features for visualization
        if strategy_class:
            # Use the strategy class's construct_features method if available
            df_features = strategy_class.construct_features(btc_df).loc[BACKTEST_START:]
        else:
            # Generic preprocessing for basic plotting - no strategy-specific features
            df_features = btc_df.copy().loc[BACKTEST_START:]
            
        # Compute weights using the strategy function with security checks
        weights = strategy_fn(btc_df)

        # Plot results only if not disabled
        if not args.no_plots:
            # Pass the full features dataframe to the plot functions
            # Each plot function should extract only the features it needs
            try:
                plot_price_vs_lookback_avg(df_features, weights=weights)
            except ValueError as e:
                logger.warning(f"Could not plot price vs moving average: {str(e)}")
                logger.warning("Only strategies that calculate moving average features can use this plot.")
                
            plot_final_weights(weights)
            plot_weight_sums_by_cycle(weights)
        else:
            # Still print the weight sums even if plots are disabled
            from core.plots import print_weight_sums_by_cycle
            print_weight_sums_by_cycle(weights)

        # Run SPD backtest and plot results with security checks
        backtest_dynamic_dca(btc_df, strategy_name=strategy_name, show_plots=not args.no_plots)
        
    except SecurityError as e:
        logger.error(f"Security violation detected: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
