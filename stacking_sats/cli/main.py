"""
Main entry point for the command-line interface.
"""
import argparse
import sys
from typing import List, Dict, Any, Optional

from stacking_sats.core.data_loader import load_btc_data
from stacking_sats.core.backtest import backtest
from stacking_sats.core.config.config_manager import ConfigManager
from stacking_sats.core.logger import setup_logger
from stacking_sats.cli.strategy_loader import get_available_strategies, load_strategy
from stacking_sats.cli.utils import parse_strategy_params, print_spd_metrics


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.
    
    Args:
        args: Command-line arguments (if None, uses sys.argv)
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Set up logger
    logger = setup_logger("stacking_sats.cli")
    
    # Load config
    config_manager = ConfigManager()
    backtest_config = config_manager.get("backtest")
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Stacking Sats: Bitcoin investment strategy backtester")
    
    # Create a mutually exclusive group for strategy selection or list_strategies
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list-strategies', action='store_true',
                     help="List available strategies and exit")
    group.add_argument('strategy', nargs='?',
                     help="Name of the strategy to backtest")
    
    parser.add_argument('--param', '-p', action='append', default=[],
                       help="Strategy parameters in format 'name=value'")
    
    parser.add_argument('--start-date', default=backtest_config.get("default_start_date"),
                       help="Start date for backtest (YYYY-MM-DD)")
    
    parser.add_argument('--end-date', default=backtest_config.get("default_end_date"),
                       help="End date for backtest (YYYY-MM-DD)")
    
    parser.add_argument('--capital', type=float, 
                       default=backtest_config.get("default_initial_capital"),
                       help="Initial capital for backtest")
    
    parser.add_argument('--fee', type=float, 
                       default=backtest_config.get("default_fee_pct") * 100,
                       help="Trading fee percentage")
    
    parser.add_argument('--no-plot', action='store_true',
                       help="Disable all plots")
    
    parser.add_argument('--show-portfolio', action='store_true',
                       help="Show portfolio performance plot (disabled by default)")
    
    parser.add_argument('--no-weights', action='store_true',
                       help="Hide allocation weights plot")
    
    parser.add_argument('--no-spd', action='store_true',
                       help="Hide SPD metrics plots")
    
    parser.add_argument('--save-dir', default=None,
                       help="Directory to save results to")
    
    parser.add_argument('--config', type=str, default=None,
                       help="Path to config file")
    
    parser.add_argument('--save-config', action='store_true',
                       help="Save current parameters as default config")
    
    parsed_args = parser.parse_args(args)
    
    # If custom config file provided, load it
    if parsed_args.config:
        try:
            logger.info(f"Loading config from {parsed_args.config}")
            # TODO: Implement config file loading
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return 1
    
    # List available strategies if requested
    if parsed_args.list_strategies:
        strategies = get_available_strategies()
        print("Available strategies:")
        for strat in strategies:
            print(f"  - {strat}")
        return 0
    
    # Load data
    logger.info("Loading Bitcoin price data...")
    try:
        data = load_btc_data()
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return 1
    
    # Parse strategy parameters
    strategy_params = parse_strategy_params(parsed_args.param)
    
    # Check for saved strategy config and merge with command-line params
    if parsed_args.strategy:
        saved_params = config_manager.get_strategy_config(parsed_args.strategy)
        # Command-line params override saved params
        for key, value in saved_params.items():
            if key not in strategy_params:
                strategy_params[key] = value
    
    # Load strategy
    try:
        logger.info(f"Initializing strategy: {parsed_args.strategy}")
        strategy = load_strategy(parsed_args.strategy, **strategy_params)
    except Exception as e:
        logger.error(f"Error initializing strategy: {e}")
        return 1
    
    # Save parameters as config if requested
    if parsed_args.save_config:
        logger.info(f"Saving strategy parameters to config")
        config_manager.save_strategy_config(parsed_args.strategy, strategy_params)
        
        # Update backtest defaults if specified
        if parsed_args.capital is not None:
            config_manager.set("backtest", "default_initial_capital", parsed_args.capital)
        if parsed_args.fee is not None:
            config_manager.set("backtest", "default_fee_pct", parsed_args.fee / 100.0)
        if parsed_args.start_date is not None:
            config_manager.set("backtest", "default_start_date", parsed_args.start_date)
        if parsed_args.end_date is not None:
            config_manager.set("backtest", "default_end_date", parsed_args.end_date)
    
    # Run backtest
    logger.info("Running backtest...")
    try:
        results = backtest(
            data=data,
            strategy=strategy,
            start_date=parsed_args.start_date,
            end_date=parsed_args.end_date,
            initial_capital=parsed_args.capital,
            fee_pct=parsed_args.fee / 100.0 if parsed_args.fee else 0.0,
            plot=not parsed_args.no_plot,
            plot_portfolio=parsed_args.show_portfolio,
            plot_weights=not parsed_args.no_weights,
            plot_spd=not parsed_args.no_spd,
            save_dir=parsed_args.save_dir
        )
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return 1
    
    # Print SPD metrics
    if 'spd_metrics' in results:
        print_spd_metrics(results['spd_metrics'])
    else:
        # Traditional metrics as fallback
        logger.info("No SPD metrics found, showing traditional metrics instead")
        print("\nBacktest Results:")
        print("-" * 40)
        for key, value in results['metrics'].items():
            if isinstance(value, float):
                print(f"{key.replace('_', ' ').title()}: {value:.2%}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 