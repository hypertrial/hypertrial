#!/usr/bin/env python3
"""
Main module for the Hypertrial backtesting framework.

This module is maintained for backward compatibility and imports 
functionality from specialized modules.
"""
import os
import sys
import logging

# Import all functionality for backward compatibility
from core.cli import parse_args
from core.file_utils import check_submit_strategies_path, find_strategy_files
from core.strategy_loader import (
    load_strategy_from_file, 
    find_strategy_class, 
    process_strategy_file, 
    process_strategy_file_with_timeout
)
from core.strategy_processor import process_single_strategy
from core.batch import (
    _run_single_backtest, 
    backtest_all_strategies, 
    backtest_multiple_strategy_files
)
from core.commands import main as commands_main

# Import data loading functions
from core.data import load_data, extract_btc_data

# Import backtest functions
from core.spd import backtest_dynamic_dca, compute_cycle_spd, list_available_strategies

# Import strategy functions
from core.strategies import load_strategies, get_strategy, list_strategies

# Import SPD validation checks
from core.spd_checks import check_strategy_submission_ready, compute_cycle_spd as checks_compute_cycle_spd

# Import plotting functions
from core.plots import (
    plot_price_vs_lookback_avg,
    plot_final_weights,
    plot_weight_sums_by_cycle,
    print_weight_sums_by_cycle
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Wrapper function for tests that import main directly
def main():
    """
    Wrapper function that parses command-line arguments and calls the main function
    from core.commands. This is used for tests that import main directly.
    """
    args = parse_args()
    # Set validate to True by default, unless --no-validate is specified
    args.validate = not args.no_validate
    return commands_main(args)

if __name__ == "__main__":
    try:
        args = parse_args()
        # Set validate to True by default, unless --no-validate is specified
        args.validate = not args.no_validate
        commands_main(args)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)