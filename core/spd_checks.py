import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.config import BACKTEST_START, BACKTEST_END, MIN_WEIGHT
from core.strategies import get_strategy, list_strategies

def compute_cycle_spd(df, strategy_name):
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()
    rows = []
    
    weight_fn = get_strategy(strategy_name)
    full_weights = weight_fn(df).fillna(0).clip(lower=0)
    inverted_prices = (1 / df_backtest['btc_close']) * 1e8

    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        
        if cycle.empty:
            break

        cycle_label = f"{current.year}–{end_date.year}"
        cycle_prices = cycle['btc_close'].values
        high, low = np.max(cycle_prices), np.min(cycle_prices)
        min_spd = (1 / high) * 1e8
        max_spd = (1 / low) * 1e8

        cycle_inverted = inverted_prices.loc[cycle.index]
        w_slice = full_weights.loc[cycle.index]
        dynamic_spd = (w_slice * cycle_inverted).sum()
        uniform_spd = cycle_inverted.mean()

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

def backtest_dynamic_dca(df, strategy_name="dynamic_dca"):
    df_res = compute_cycle_spd(df, strategy_name)
    
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
    
    return df_res

def check_strategy_submission_ready(df, strategy_name, return_details=False):
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()

    weight_fn = get_strategy(strategy_name)
    full_weights = weight_fn(df).fillna(0)

    passed = True
    validation_results = {
        'validation_passed': True,
        'has_negative_weights': False,
        'has_below_min_weights': False,
        'weights_not_sum_to_one': False,
        'underperforms_uniform': False,
    }
    
    cycle_issues = {}

    # --- Criteria 1–3: per-cycle checks ---
    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        w_slice = full_weights.loc[cycle.index]

        cycle_label = f"{current.year}–{end_date.year}"
        cycle_issues[cycle_label] = {}

        # Criterion 1: strictly positive
        if (w_slice <= 0).any():
            print(f"[{cycle_label}] ❌ Some weights are zero or negative.")
            passed = False
            validation_results['has_negative_weights'] = True
            cycle_issues[cycle_label]['has_negative_weights'] = True

        # Criterion 2: above minimum threshold
        if (w_slice < MIN_WEIGHT).any():
            print(f"[{cycle_label}] ❌ Some weights are below MIN_WEIGHT = {MIN_WEIGHT}.")
            passed = False
            validation_results['has_below_min_weights'] = True
            cycle_issues[cycle_label]['has_below_min_weights'] = True

        # Criterion 3: weights must sum to 1 over the entire cycle
        total_weight = w_slice.sum().sum() if isinstance(w_slice, pd.DataFrame) else w_slice.sum()
        if not np.isclose(total_weight, 1.0, rtol=1e-5, atol=1e-8):
            print(f"[{cycle_label}] ❌ Total weights across the cycle do not sum to 1 (sum = {total_weight:.6f}).")
            passed = False
            validation_results['weights_not_sum_to_one'] = True
            cycle_issues[cycle_label]['weights_not_sum_to_one'] = True
            cycle_issues[cycle_label]['weight_sum'] = float(total_weight)

        current += cycle_length

    # --- Criterion 4: SPD performance must be ≥ uniform ---
    spd_results = compute_cycle_spd(df, strategy_name)
    for cycle, row in spd_results.iterrows():
        if cycle not in cycle_issues:
            cycle_issues[cycle] = {}
            
        if row['dynamic_pct'] < row['uniform_pct']:
            print(f"[{cycle}] ❌ Dynamic SPD percentile ({row['dynamic_pct']:.2f}%) is less than uniform ({row['uniform_pct']:.2f}%).")
            passed = False
            validation_results['underperforms_uniform'] = True
            cycle_issues[cycle]['underperforms_uniform'] = True
            cycle_issues[cycle]['dynamic_pct'] = float(row['dynamic_pct'])
            cycle_issues[cycle]['uniform_pct'] = float(row['uniform_pct'])

    # --- Final verdict ---
    if passed:
        print("✅ Strategy is ready for submission.")
    else:
        print("⚠️ Fix the issues above before submission.")
    
    validation_results['validation_passed'] = passed
    validation_results['cycle_issues'] = cycle_issues if not passed else {}
    
    if return_details:
        return validation_results
    
    return passed 