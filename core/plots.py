# plots.py
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from config import BACKTEST_START, BACKTEST_END, MIN_WEIGHT, REBALANCE_WINDOW

def plot_price_vs_ma200(df_features, weights=None):
    df_plot = df_features.loc[BACKTEST_START:BACKTEST_END].copy()

    plt.figure(figsize=(12, 5))
    plt.plot(df_plot.index, df_plot['btc_close'], label='BTC Price', alpha=0.6)
    plt.plot(df_plot.index, df_plot['ma200'], label='200-day MA', alpha=0.9)
    plt.fill_between(
        df_plot.index,
        df_plot['btc_close'],
        df_plot['ma200'],
        where=(df_plot['btc_close'] < df_plot['ma200']),
        color='green',
        alpha=0.1,
        label='Signal (Price < MA200)'
    )

    if weights is not None:
        signal_mask = df_plot['btc_close'] < df_plot['ma200']
        uniform_dates = df_plot.index[~signal_mask]
        plt.scatter(uniform_dates, df_plot.loc[~signal_mask, 'btc_close'],
                    marker='o', edgecolors='blue', facecolors='none', label='Uniform Weight Marker', s=20)
        dynamic_dates = df_plot.index[signal_mask]
        plt.scatter(dynamic_dates, df_plot.loc[signal_mask, 'btc_close'],
                    marker='o', color='red', label='Dynamic Weight Marker', s=20)

    plt.title("BTC Close vs MA200 (With Weight Markers)")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.legend()
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

def plot_weight_sums_by_cycle(weights):
    weights_bt = weights.loc[BACKTEST_START:BACKTEST_END].copy()
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = weights_bt.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    weight_sums = weights_bt.groupby(cycle_labels).sum()
    print("Weight sums by cycle (should be close to 1.0):")
    for cycle, total in weight_sums.items():
        print(f"Cycle {(start_year + 4*cycle)}–{(start_year + 4*cycle + 3)}: {total:.4f}")
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
