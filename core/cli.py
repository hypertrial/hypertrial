#!/usr/bin/env python3
"""
Hypertrial CLI entry point.
This module provides a clean entry point for the command-line interface
that avoids the circular import warnings that can occur with direct module execution.
"""
import sys
import argparse
import logging
from core.commands import main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Hypertrial Backtesting Framework')
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
        '--strategy-files', '-fs',
        nargs='+',
        help='List of paths to Python strategy files for batch backtesting'
    )
    parser.add_argument(
        '--strategy-dir', '-sd',
        help='Directory containing Python strategy files to backtest (all .py files will be processed)'
    )
    parser.add_argument(
        '--glob-pattern', '-gp',
        help='Glob pattern for finding strategy files (e.g., "strategies/*.py")'
    )
    parser.add_argument(
        '--processes', '-p',
        type=int,
        default=0,
        help='Number of parallel processes to use for backtesting (0=auto, 1=sequential)'
    )
    parser.add_argument(
        '--batch-size', '-bs',
        type=int,
        default=0,
        help='Process strategies in batches of this size to manage memory (0=no batching)'
    )
    parser.add_argument(
        '--file-timeout', '-ft',
        type=int,
        default=60,
        help='Maximum seconds allowed per strategy file (0=no timeout)'
    )
    parser.add_argument(
        '--exclude-dirs', '-ed',
        nargs='+',
        default=['.git', '.pytest_cache', '__pycache__', 'venv', 'test_venv', 'build', 'dist', 'hypertrial.egg-info'],
        help='Directories to exclude when searching for strategy files'
    )
    parser.add_argument(
        '--exclude-patterns', '-ep',
        nargs='+',
        default=['__init__.py', 'test_*.py', 'conftest.py'],
        help='File patterns to exclude when searching for strategy files'
    )
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Recursively search for Python files in subdirectories'
    )
    parser.add_argument(
        '--include-patterns', '-ip',
        nargs='+',
        default=[],
        help='File patterns to include when searching (only files matching these patterns will be processed)'
    )
    parser.add_argument(
        '--max-files', '-mf',
        type=int,
        default=100,
        help='Maximum number of files to process (default: 100)'
    )
    parser.add_argument(
        '--standalone', '-st',
        action='store_true',
        help='Run only the specified strategy file without loading other strategies'
    )
    parser.add_argument(
        '--save-plots', '-sp',
        action='store_true',
        help='Save plots to files in the output directory'
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
    parser.add_argument(
        '--download-data', '-d',
        action='store_true',
        help='Force download of fresh price data from CoinMetrics API'
    )
    parser.add_argument(
        '--data-file', '-df',
        default='core/data/btc_price_data.csv',
        help='Path to the price data CSV file'
    )
    parser.add_argument(
        '--no-validate', '-nv',
        action='store_true',
        help='Disable strategy validation against submission criteria'
    )
    return parser.parse_args()

def cli_main():
    """
    Command-line interface entry point that avoids the 
    'found in sys.modules after import of package' warning.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        # Parse arguments and pass to main function
        args = parse_args()
        # Set validate to True by default, unless --no-validate is specified
        args.validate = not args.no_validate
        main(args)
        return 0
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(cli_main()) 