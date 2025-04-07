"""
SPD (Sats-Per-Dollar) Strategy Backtest Example.

This script demonstrates how to evaluate strategies using SPD metrics
over 4-year investment cycles instead of traditional backtest metrics.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from stacking_sats.core.data_loader import load_btc_data
from stacking_sats.strategies.examples.dynamic_allocation_strategy import DynamicAllocationStrategy

# Global configuration
BACKTEST_START = '2013-01-01'
BACKTEST_END = '2024-12-31'
ALPHA = 1.25
REBALANCE_WINDOW = 365 * 2
MIN_WEIGHT = 1e-4

def compute_cycle_spd(df, weight_fn):
    """
    Compute SPD (sats-per-dollar) metrics over 4-year investment cycles
    from BACKTEST_START to BACKTEST_END.
    
    Parameters:
        df (pd.DataFrame): DataFrame with btc_close column
        weight_fn (callable): Function that calculates weights from df
        
    Returns:
        pd.DataFrame: DataFrame with SPD metrics by cycle
    """
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()
    rows = []

    # Compute weights using the provided weight function
    full_weights = weight_fn(df).fillna(0).clip(lower=0)

    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        cycle = df_backtest.loc[current : min(cycle_end, df_backtest.index.max())]
        if cycle.empty:
            break

        cycle_label = f"{current.year}–{min(cycle_end.year, df_backtest.index.max().year)}"

        high, low = cycle['btc_close'].max(), cycle['btc_close'].min()
        min_spd = (1 / high) * 1e8  # Convert to sats (1 BTC = 100,000,000 sats)
        max_spd = (1 / low) * 1e8
        
        # Uniform DCA - equal weight each day
        uniform_weights = pd.Series(1/len(cycle), index=cycle.index)
        uniform_spd = ((uniform_weights / cycle['btc_close']).sum()) * 1e8

        # Dynamic strategy weights
        w_slice = full_weights.loc[cycle.index]
        dynamic_spd = ((w_slice / cycle['btc_close']).sum()) * 1e8

        # Calculate percentiles
        uniform_pct = (uniform_spd - min_spd) / (max_spd - min_spd) * 100
        dynamic_pct = (dynamic_spd - min_spd) / (max_spd - min_spd) * 100
        excess_pct = dynamic_pct - uniform_pct  # Excess SPD percentile difference

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
    """
    Plot comparison of Uniform DCA vs Dynamic DCA SPD values and their percentiles.
    
    Parameters:
        df_res (pd.DataFrame): DataFrame with SPD metrics by cycle
        strategy_name (str): Name of the strategy for plot labels
    """
    x = np.arange(len(df_res.index))

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_yscale('log')

    ax1.plot(x, df_res['min_spd'], marker='o', label='Min spd (High)')
    ax1.plot(x, df_res['max_spd'], marker='o', label='Max spd (Low)')
    ax1.plot(x, df_res['uniform_spd'], marker='o', label='Uniform DCA spd')
    ax1.plot(x, df_res['dynamic_spd'], marker='o', label=f"{strategy_name} spd")

    ax1.set_title(f"Uniform vs {strategy_name} DCA (SPD)")
    ax1.set_ylabel('Sats per Dollar (Log Scale)')
    ax1.set_xlabel("Cycle")
    ax1.grid(True, linestyle='--', linewidth=0.5)
    ax1.legend(loc='upper left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_res.index)

    ax2 = ax1.twinx()
    barw = 0.4
    ax2.bar(x - barw/2, df_res['uniform_pct'], width=barw, alpha=0.3, label='Uniform %')
    ax2.bar(x + barw/2, df_res['dynamic_pct'], width=barw, alpha=0.3, label=f"{strategy_name} %")
    ax2.set_ylabel('SPD Percentile (%)')
    ax2.set_ylim(0, 100)
    ax2.legend(loc='upper right')

    plt.tight_layout()
    plt.show()

def backtest_strategy_spd(df, weight_fn, strategy_name="Dynamic Strategy"):
    """
    Run a backtest using SPD metrics for the provided strategy over 4-year cycles.
    
    Parameters:
        df (pd.DataFrame): DataFrame with btc_close column
        weight_fn (callable): Function that calculates weights from df
        strategy_name (str): Name of the strategy for display and plots
    """
    # Compute SPD metrics
    df_res = compute_cycle_spd(df, weight_fn)

    # Calculate aggregated metrics
    dynamic_spd_metrics = {
        'min': df_res['dynamic_spd'].min(),
        'max': df_res['dynamic_spd'].max(),
        'mean': df_res['dynamic_spd'].mean(),
        'median': df_res['dynamic_spd'].median()
    }

    dynamic_pct_metrics = {
        'min': df_res['dynamic_pct'].min(),
        'max': df_res['dynamic_pct'].max(),
        'mean': df_res['dynamic_pct'].mean(),
        'median': df_res['dynamic_pct'].median()
    }

    # Print summary metrics
    print(f"\nAggregated Metrics for {strategy_name}:")
    print("Dynamic SPD:")
    for key, value in dynamic_spd_metrics.items():
        print(f"  {key}: {value:.2f}")
    print("Dynamic SPD Percentile:")
    for key, value in dynamic_pct_metrics.items():
        print(f"  {key}: {value:.2f}")
    
    # Print excess SPD percentile difference for each cycle
    print("\nExcess SPD Percentile Difference (Dynamic - Uniform) per Cycle:")
    for cycle, row in df_res.iterrows():
        print(f"  {cycle}: {row['excess_pct']:.2f}%")

    # Create visualization
    plot_spd_comparison(df_res, strategy_name)
    
    return df_res

def dynamic_allocation_weight_fn(df):
    """Wrapper function to get weights from a DynamicAllocationStrategy instance."""
    strategy = DynamicAllocationStrategy(
        backtest_start=BACKTEST_START,
        backtest_end=BACKTEST_END,
        alpha=ALPHA,
        rebalance_window=REBALANCE_WINDOW,
        min_weight=MIN_WEIGHT
    )
    
    # Prepare data and generate weights
    prepared_data = strategy.prepare_data(df)
    weights = strategy.generate_weights(prepared_data)
    
    return weights

def main():
    """Run a backtest using SPD metrics for the dynamic allocation strategy."""
    # Load BTC price data
    data = load_btc_data()
    
    # Ensure we're using actual historical data, not future data
    data = data.loc[:pd.Timestamp.now()]
    
    # Define strategy name
    strategy_name = "Threshold-Based DCA"
    
    # Run backtest using SPD metrics
    backtest_strategy_spd(data, dynamic_allocation_weight_fn, strategy_name=strategy_name)

if __name__ == "__main__":
    main() 