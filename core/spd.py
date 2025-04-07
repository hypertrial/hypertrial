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
    
    # Get the strategy function by name
    weight_fn = get_strategy(strategy_name)
    full_weights = weight_fn(df).fillna(0).clip(lower=0)

    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        cycle = df_backtest.loc[current : min(cycle_end, df_backtest.index.max())]
        if cycle.empty:
            break

        cycle_label = f"{current.year}–{min(cycle_end.year, df_backtest.index.max().year)}"
        high, low = cycle['btc_close'].max(), cycle['btc_close'].min()
        min_spd = (1 / high) * 1e8
        max_spd = (1 / low) * 1e8
        uniform_spd = ((1 / cycle['btc_close']).sum() / len(cycle)) * 1e8
        w_slice = full_weights.loc[cycle.index]
        dynamic_spd = ((w_slice / cycle['btc_close']).sum()) * 1e8
        uniform_pct = (uniform_spd - min_spd) / (max_spd - min_spd) * 100
        dynamic_pct = (dynamic_spd - min_spd) / (max_spd - min_spd) * 100
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

def backtest_dynamic_dca(df, strategy_name="dynamic_dca"):
    df_res = compute_cycle_spd(df, strategy_name)
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

    plot_spd_comparison(df_res, strategy_name)

def list_available_strategies():
    """
    Print a list of all available strategies with their descriptions
    """
    strategies = list_strategies()
    print("\nAvailable Strategies:")
    for name, description in strategies.items():
        print(f"  {name}: {description}")
    return strategies
