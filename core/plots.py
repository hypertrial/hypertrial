# plots.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from core.config import BACKTEST_START, BACKTEST_END, MIN_WEIGHT, REBALANCE_WINDOW

def plot_price_vs_lookback_avg(df, weights=None):
    """
    Plot BTC price vs a lookback moving average with optional weight heatmap
    
    Args:
        df (pd.DataFrame): DataFrame with btc_close and moving average columns
        weights (pd.Series, optional): Optional weights Series
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Check if moving average column exists
    if not any(col.startswith('ma') for col in df.columns):
        raise ValueError("No moving average column (starting with 'ma') found in the dataframe. "
                         "Make sure to use a strategy that calculates moving average features.")
    
    # Find the first moving average column (ma*)
    ma_col = next((col for col in df.columns if col.startswith('ma')), None)
    
    # Plot price and moving average
    ax.semilogy(df.index, df['btc_close'], label='BTC Price')
    ax.semilogy(df.index, df[ma_col], label=f'{ma_col} (Moving Average)', alpha=0.8)
    
    # If weights are provided, use them for coloring
    if weights is not None:
        # Normalize weights for visualization
        norm_weights = (weights - weights.min()) / (weights.max() - weights.min())
        
        # Plot scatter with weight-based coloring
        common_idx = df.index.intersection(norm_weights.index)
        scatter = ax.scatter(
            common_idx, 
            df.loc[common_idx, 'btc_close'],
            c=norm_weights.loc[common_idx],
            cmap='viridis',
            alpha=0.6,
            s=30
        )
        plt.colorbar(scatter, label='Relative Weight')
    
    # Add labels and grid
    ax.set_title('BTC Price vs Moving Average')
    ax.set_xlabel('Date')
    ax.set_ylabel('Price (USD, log scale)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_final_weights(weights):
    weights_bt = weights.loc[BACKTEST_START:BACKTEST_END].copy()
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = weights_bt.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    cmap = plt.colormaps.get_cmap('tab10')
    fig, ax = plt.subplots(figsize=(12, 5))

    for cycle, group in weights_bt.groupby(cycle_labels):
        label = f"{start_year + 4*cycle}–{start_year + 4*cycle + 3}"
        color = cmap(cycle % 10)
        ax.plot(group.index, group.values, label=label, color=color)
        N = len(group)
        uniform = 1.0 / N
        ax.hlines(uniform, group.index.min(), group.index.max(), color=color, linestyle='--', alpha=0.6)
        ax.hlines(MIN_WEIGHT, group.index.min(), group.index.max(), color=color, linestyle='--', alpha=0.6)
        rebalance_start_date = group.index[-REBALANCE_WINDOW]
        ax.axvline(x=rebalance_start_date, color=color, linestyle=':', alpha=0.7,
                   label=f'Rebalance start ({rebalance_start_date.strftime("%Y-%m-%d")})')

    ax.set_title("Daily Weights per 4-Year Cycle (with Uniform Benchmark & Rebalance Start)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Daily Weight")
    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.show()

def print_weight_sums_by_cycle(weights):
    """
    Print the sum of weights by cycle (without plotting)
    """
    weights_bt = weights.loc[BACKTEST_START:BACKTEST_END].copy()
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = weights_bt.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    weight_sums = weights_bt.groupby(cycle_labels).sum()
    print("Weight sums by cycle (should be close to 1.0):")
    for cycle, total in weight_sums.items():
        print(f"Cycle {(start_year + 4*cycle)}–{(start_year + 4*cycle + 3)}: {total:.4f}")
    return weight_sums

def plot_weight_sums_by_cycle(weights):
    """
    Plot the sum of weights by cycle
    """
    weight_sums = print_weight_sums_by_cycle(weights)
    
    start_year = pd.to_datetime(BACKTEST_START).year
    label_map = {i: f"{start_year + 4*i}–{start_year + 4*i + 3}" for i in weight_sums.index}
    plt.figure(figsize=(10, 4))
    plt.bar([label_map[i] for i in weight_sums.index], weight_sums.values, width=0.6, alpha=0.7)
    plt.axhline(1.0, linestyle='--', color='black', label='Target Budget = 1.0')
    plt.title("Sum of Weights by 4-Year Cycle")
    plt.xlabel("Cycle")
    plt.ylabel("Total Allocated Weight")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.show()
