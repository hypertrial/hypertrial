# spd.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import get_strategy, list_strategies

def compute_cycle_spd(df, strategy_name):
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()
    rows = []
    
    # Get the strategy function by name and pre-compute weights once
    weight_fn = get_strategy(strategy_name)
    full_weights = weight_fn(df).fillna(0).clip(lower=0)
    
    # Pre-calculate inverted prices multiplied by 1e8 for efficiency
    inverted_prices = (1 / df_backtest['btc_close']) * 1e8

    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        
        if cycle.empty:
            break

        cycle_label = f"{current.year}–{end_date.year}"
        
        # More efficient min/max calculation
        cycle_prices = cycle['btc_close'].values
        high, low = np.max(cycle_prices), np.min(cycle_prices)
        min_spd = (1 / high) * 1e8
        max_spd = (1 / low) * 1e8
        
        # Vectorized calculation of uniform SPD
        cycle_inverted = inverted_prices.loc[cycle.index]
        uniform_spd = cycle_inverted.mean()
        
        # Vectorized calculation of dynamic SPD
        w_slice = full_weights.loc[cycle.index]
        dynamic_spd = (w_slice * cycle_inverted).sum()
        
        # Calculate percentiles
        spd_range = max_spd - min_spd
        uniform_pct = (uniform_spd - min_spd) / spd_range * 100
        dynamic_pct = (dynamic_spd - min_spd) / spd_range * 100
        excess_pct = dynamic_pct - uniform_pct

        rows.append({
            'cycle': cycle_label,
            'min_spd': min_spd,
            'max_spd': max_spd,
            'uniform_spd': uniform_spd,
            'dynamic_spd': dynamic_spd,
            'uniform_pct': uniform_pct,
            'dynamic_pct': dynamic_pct,
            'excess_pct': excess_pct
        })

        current += cycle_length

    return pd.DataFrame(rows).set_index('cycle')

def plot_spd_comparison(df_res, strategy_name):
    x = np.arange(len(df_res.index))
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_yscale('log')
    
    # Plot all lines in one call for better performance
    lines = ax1.plot(
        x, df_res['min_spd'], 'o-',
        x, df_res['max_spd'], 'o-',
        x, df_res['uniform_spd'], 'o-',
        x, df_res['dynamic_spd'], 'o-'
    )
    
    # Set labels after plotting
    ax1.set_title(f"Uniform vs {strategy_name} DCA (SPD)")
    ax1.set_ylabel('Sats per Dollar (Log Scale)')
    ax1.set_xlabel("Cycle")
    ax1.grid(True, linestyle='--', linewidth=0.5)
    ax1.legend(lines, ['Min spd (High)', 'Max spd (Low)', 'Uniform DCA spd', f"{strategy_name} spd"], loc='upper left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_res.index)

    ax2 = ax1.twinx()
    barw = 0.4
    
    # Call bar separately for each series instead of trying to pass lists of arrays
    bar1 = ax2.bar(x - barw/2, df_res['uniform_pct'], width=barw, alpha=0.3)
    bar2 = ax2.bar(x + barw/2, df_res['dynamic_pct'], width=barw, alpha=0.3)
    
    ax2.set_ylabel('SPD Percentile (%)')
    ax2.set_ylim(0, 100)
    ax2.legend([bar1, bar2], ['Uniform %', f"{strategy_name} %"], loc='upper right')

    plt.tight_layout()
    plt.show()

def backtest_dynamic_dca(df, strategy_name="dynamic_dca", show_plots=True):
    df_res = compute_cycle_spd(df, strategy_name)
    
    # Calculate metrics with vectorized operations
    dynamic_spd = df_res['dynamic_spd']
    dynamic_pct = df_res['dynamic_pct']
    
    dynamic_spd_metrics = {
        'min': dynamic_spd.min(),
        'max': dynamic_spd.max(),
        'mean': dynamic_spd.mean(),
        'median': dynamic_spd.median()
    }
    
    dynamic_pct_metrics = {
        'min': dynamic_pct.min(),
        'max': dynamic_pct.max(),
        'mean': dynamic_pct.mean(),
        'median': dynamic_pct.median()
    }

    print(f"\nAggregated Metrics for {strategy_name}:")
    print("Dynamic SPD:")
    for key, value in dynamic_spd_metrics.items():
        print(f"  {key}: {value:.2f}")
    print("Dynamic SPD Percentile:")
    for key, value in dynamic_pct_metrics.items():
        print(f"  {key}: {value:.2f}")

    print("\nExcess SPD Percentile Difference (Dynamic - Uniform) per Cycle:")
    for cycle, row in df_res.iterrows():
        print(f"  {cycle}: {row['excess_pct']:.2f}%")

    if show_plots:
        plot_spd_comparison(df_res, strategy_name)
    
    return df_res

def list_available_strategies():
    """
    Print a list of all available strategies with their descriptions
    """
    strategies = list_strategies()
    
    if not strategies:
        print("\nNo strategies available. Please check your installation.")
        return strategies
    
    print("\nAvailable Strategies:")
    print("=====================")
    
    # Group by core and custom strategies
    core_strategies = {}
    custom_strategies = {}
    
    for name, description in strategies.items():
        if any(name.startswith(prefix) for prefix in ['dynamic_dca', 'uniform_dca']):
            core_strategies[name] = description
        else:
            custom_strategies[name] = description
    
    # Print core strategies
    if core_strategies:
        print("\nCore Strategies:")
        print("-----------------")
        for name, description in sorted(core_strategies.items()):
            print(f"  {name:20}: {description.split('.')[0] if description else 'No description'}")
    
    # Print custom strategies
    if custom_strategies:
        print("\nCustom Strategies:")
        print("------------------")
        for name, description in sorted(custom_strategies.items()):
            print(f"  {name:20}: {description.split('.')[0] if description else 'No description'}")
    
    return strategies
