# main.py
import argparse
import os
import pandas as pd
from core.data import load_data
from core.plots import plot_price_vs_ma200, plot_final_weights, plot_weight_sums_by_cycle
from core.spd import backtest_dynamic_dca, list_available_strategies, compute_cycle_spd
from core.strategies import load_strategies, get_strategy, list_strategies
from core.config import BACKTEST_START

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='HyperTrial Backtesting Framework')
    parser.add_argument(
        '--strategy', '-s', 
        default='dynamic_dca',
        help='Strategy to use for backtesting'
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

def backtest_all_strategies(btc_df, output_dir, show_plots=False):
    """
    Backtest all available strategies and output results to CSV files
    
    Args:
        btc_df (pd.DataFrame): Bitcoin price data
        output_dir (str): Directory to save results
        show_plots (bool): Whether to display plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Get all available strategies
    strategies = list_strategies()
    
    # Create results dataframes
    all_spd_results = []
    summary_results = []
    
    print(f"\nBacktesting {len(strategies)} strategies...")
    
    # Run backtest for each strategy
    for strategy_name in strategies:
        print(f"\nBacktesting strategy: {strategy_name}")
        
        # Run backtest and collect results
        df_res = backtest_dynamic_dca(btc_df, strategy_name=strategy_name, show_plots=show_plots)
        
        # Add strategy name to results
        df_res['strategy'] = strategy_name
        all_spd_results.append(df_res)
        
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
            'avg_excess_pct': df_res['excess_pct'].mean()
        }
        summary_results.append(summary)
    
    # Combine all results
    all_results_df = pd.concat(all_spd_results)
    all_results_df = all_results_df.reset_index()
    
    summary_df = pd.DataFrame(summary_results)
    
    # Save to CSV
    spd_csv_path = os.path.join(output_dir, 'spd_by_cycle.csv')
    summary_csv_path = os.path.join(output_dir, 'strategy_summary.csv')
    
    all_results_df.to_csv(spd_csv_path, index=False)
    summary_df.to_csv(summary_csv_path, index=False)
    
    print(f"\nResults saved to:")
    print(f"  - {spd_csv_path}")
    print(f"  - {summary_csv_path}")
    
    # Display summary table
    print("\nStrategy Summary:")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 120)
    print(summary_df.sort_values('avg_excess_pct', ascending=False))
    
    return summary_df

def main():
    # Load all strategies
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
        backtest_all_strategies(btc_df, args.output_dir, show_plots=not args.no_plots)
        return
    
    # Otherwise, continue with single strategy backtest
    print(btc_df.info())
    print(btc_df.head())
    
    # Get the requested strategy
    strategy_name = args.strategy
    strategy_fn = get_strategy(strategy_name)
    
    # Import the strategy class dynamically to access its methods
    from importlib import import_module
    import inspect
    
    # Find the strategy class from the registered modules
    strategy_class = None
    for module_name in [f"core.strategies.{name}" for name in ["dynamic_dca", "uniform_dca"]]:
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
    
    if not strategy_class:
        # Fallback: use the registered function directly
        # Basic preprocessing for plotting
        df_features = btc_df.copy()
        if 'ma200' not in df_features.columns:
            df_features['ma200'] = df_features['btc_close'].rolling(window=200, min_periods=1).mean()
        df_features = df_features.loc[BACKTEST_START:]
    else:
        # Use the class's construct_features method
        df_features = strategy_class.construct_features(btc_df).loc[BACKTEST_START:]
        
    # Compute weights using the strategy function
    weights = strategy_fn(btc_df)

    # Plot results only if not disabled
    if not args.no_plots:
        plot_price_vs_ma200(df_features, weights=weights)
        plot_final_weights(weights)
        plot_weight_sums_by_cycle(weights)
    else:
        # Still print the weight sums even if plots are disabled
        from core.plots import print_weight_sums_by_cycle
        print_weight_sums_by_cycle(weights)

    # Run SPD backtest and plot results
    backtest_dynamic_dca(btc_df, strategy_name=strategy_name, show_plots=not args.no_plots)

if __name__ == '__main__':
    main()
