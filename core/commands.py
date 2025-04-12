#!/usr/bin/env python3
"""
Command orchestration for the Hypertrial framework.
This module contains the main function that processes command-line arguments
and coordinates the appropriate actions.
"""
import os
import sys
import glob
import logging
from core.file_utils import check_submit_strategies_path, find_strategy_files
from core.strategy_loader import load_strategy_from_file, find_strategy_class
from core.strategy_processor import process_single_strategy
from core.batch import backtest_all_strategies, backtest_multiple_strategy_files
from core.strategies import load_strategies, list_strategies
from core.data import load_data
from core.data.extract_data import extract_btc_data
from core.security import SecurityError
from core.spd import list_available_strategies
from core.spd_checks import check_strategy_submission_ready

# Configure logging
logger = logging.getLogger(__name__)

def main(args):
    """
    Main function for the Hypertrial framework that processes command-line arguments
    and dispatches to appropriate functions.
    
    Args:
        args: Command-line arguments from argparse
    """
    try:
        # Collect strategy files from various sources
        strategy_files = []
        
        # 1. Individual files specified with --strategy-files
        if args.strategy_files:
            strategy_files.extend([os.path.abspath(f) for f in args.strategy_files])
            logger.info(f"Added {len(args.strategy_files)} strategy files from --strategy-files argument")
            
        # 2. Directory of strategy files specified with --strategy-dir
        if args.strategy_dir:
            if not os.path.isdir(args.strategy_dir):
                logger.error(f"Strategy directory not found: {args.strategy_dir}")
                return
            
            dir_strategy_files = find_strategy_files(
                args.strategy_dir,
                recursive=args.recursive,
                exclude_dirs=args.exclude_dirs,
                exclude_patterns=args.exclude_patterns,
                include_patterns=args.include_patterns,
                max_files=args.max_files
            )
            
            logger.info(f"Found {len(dir_strategy_files)} strategy files in directory: {args.strategy_dir}")
            strategy_files.extend(dir_strategy_files)
        
        # 3. Glob pattern specified with --glob-pattern
        if args.glob_pattern:
            pattern_strategy_files = [os.path.abspath(f) for f in glob.glob(args.glob_pattern)]
            
            # Apply filtering with our new function
            filtered_files = []
            for file_path in pattern_strategy_files:
                file_name = os.path.basename(file_path)
                # Check exclusion patterns
                if not any(file_name == pattern or 
                         (pattern.endswith('*.py') and file_name.startswith(pattern[:-3])) 
                         for pattern in args.exclude_patterns):
                    # Check inclusion patterns
                    if not args.include_patterns or any(
                            file_name == pattern or 
                            (pattern.endswith('*.py') and file_name.startswith(pattern[:-3])) or
                            (pattern.endswith('.py') and file_name == pattern) or
                            ('*' not in pattern and pattern in file_name)
                            for pattern in args.include_patterns):
                        filtered_files.append(file_path)
                        
                        # Check max files limit
                        if args.max_files and len(filtered_files) >= args.max_files:
                            logger.info(f"Reached maximum file limit ({args.max_files}) for glob pattern")
                            break
            
            logger.info(f"Found {len(filtered_files)} strategy files matching pattern: {args.glob_pattern}")
            strategy_files.extend(filtered_files)
        
        # Check submit_strategies path if no files found yet
        if not (args.strategy_file and args.standalone) and not strategy_files:
            if not check_submit_strategies_path():
                return
    
        # Load all strategies with security checks unless in standalone mode
        if not (args.strategy_file and args.standalone) and not strategy_files:
            load_strategies()
        
        # List strategies if requested
        if args.list:
            list_available_strategies()
            return
        
        # Handle forced data download if requested
        if args.download_data:
            try:
                logger.info("Forcing download of fresh BTC price data from CoinMetrics...")
                btc_df = extract_btc_data(save_to_csv=True)
                logger.info(f"Successfully downloaded fresh BTC price data: {len(btc_df)} records")
            except Exception as e:
                logger.error(f"Failed to download fresh data: {str(e)}")
                logger.error("Continuing with existing data if available...")
        
        # Load BTC data
        try:
            btc_df = load_data(csv_path=args.data_file)
        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            logger.error("Please run with --download-data to fetch fresh data or ensure the data file exists.")
            return
        
        # If we have strategy files to process
        if strategy_files:
            # Remove duplicates while preserving order
            seen = set()
            unique_strategy_files = [f for f in strategy_files if not (f in seen or seen.add(f))]
            
            logger.info(f"Processing {len(unique_strategy_files)} unique strategy files")
            
            # Run backtest_multiple_strategy_files with process and batch parameters
            backtest_multiple_strategy_files(
                btc_df, 
                unique_strategy_files, 
                args.output_dir, 
                show_plots=not args.no_plots,
                processes=args.processes,
                batch_size=args.batch_size,
                file_timeout=args.file_timeout,
                validate=args.validate
            )
            return
            
        # If backtest all flag is set, run all strategies and exit
        if args.backtest_all:
            # When running all backtests, disable plots by default (ignore no-plots flag)
            backtest_all_strategies(btc_df, args.output_dir, show_plots=False, validate=args.validate)
            return
        
        # Process a single strategy (either from file or by name)
        if args.strategy_file:
            # Process strategy from file
            process_single_strategy(
                btc_df,
                strategy_file=os.path.abspath(args.strategy_file),
                show_plots=not args.no_plots,
                save_plots=args.save_plots,
                output_dir=args.output_dir,
                standalone=args.standalone,
                validate=args.validate
            )
        else:
            # Process strategy by name
            process_single_strategy(
                btc_df,
                strategy_name=args.strategy,
                show_plots=not args.no_plots,
                save_plots=args.save_plots,
                output_dir=args.output_dir,
                validate=args.validate
            )
    
    except SecurityError as e:
        logger.error(f"Security violation detected: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1) 