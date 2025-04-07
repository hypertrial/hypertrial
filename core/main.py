# main.py
import argparse
from core.data import load_data
from core.plots import plot_price_vs_ma200, plot_final_weights, plot_weight_sums_by_cycle
from core.spd import backtest_dynamic_dca, list_available_strategies
from core.strategies import load_strategies, get_strategy
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
    return parser.parse_args()

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

    # Plot results
    plot_price_vs_ma200(df_features, weights=weights)
    plot_final_weights(weights)
    plot_weight_sums_by_cycle(weights)

    # Run SPD backtest and plot results
    backtest_dynamic_dca(btc_df, strategy_name=strategy_name)

if __name__ == '__main__':
    main()
