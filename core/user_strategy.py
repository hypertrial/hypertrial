# user_strategy.py
import numpy as np
import pandas as pd
from config import BACKTEST_START, BACKTEST_END, ALPHA, REBALANCE_WINDOW, MIN_WEIGHT

def construct_features(df):
    """
    Constructs additional features for the strategy.
    Calculates:
      - 200-day moving average (ma200) of btc_close.
      - 200-day rolling standard deviation (std200) of btc_close.
    """
    df = df.copy()
    df['ma200'] = df['btc_close'].rolling(window=200, min_periods=1).mean()
    df['std200'] = df['btc_close'].rolling(window=200, min_periods=1).std()
    return df

def dynamic_budget_allocation(df):
    """
    Implements a constrained early bias rebalancing strategy.
    For days where btc_close is below ma200, boosts the weight by a factor
    determined by the z-score and redistributes the excess weight.
    """
    weights = pd.Series(index=df.index, dtype=float)
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = df.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)

    for cycle, group in df.groupby(cycle_labels):
        N = len(group)
        base_weight = 1.0 / N
        temp_weights = np.full(N, base_weight)
        strategy_active = True

        for i in range(N):
            if not strategy_active:
                break

            price = group['btc_close'].iloc[i]
            ma200 = group['ma200'].iloc[i]
            std200 = group['std200'].iloc[i]

            if price < ma200 and std200 > 0:
                z = (ma200 - price) / std200
                boost_multiplier = 1 + ALPHA * z
                current_weight = temp_weights[i]
                boosted_weight = current_weight * boost_multiplier
                excess = boosted_weight - current_weight

                start_redistribution = max(N - REBALANCE_WINDOW, i + 1)
                if start_redistribution >= N:
                    continue

                redistribution_idx = np.arange(start_redistribution, N)
                reduction = excess / len(redistribution_idx)
                projected = temp_weights[redistribution_idx] - reduction

                if np.all(projected >= MIN_WEIGHT):
                    temp_weights[i] = boosted_weight
                    temp_weights[redistribution_idx] -= reduction
                else:
                    strategy_active = False

        weights.loc[group.index] = temp_weights

    return weights

def dynamic_rule_causal(df):
    """
    Orchestrates the dynamic strategy by constructing features,
    limiting the DataFrame to the backtest period, and computing weights.
    """
    df_features = construct_features(df)
    df_features = df_features.loc[BACKTEST_START:BACKTEST_END]
    weights = dynamic_budget_allocation(df_features)
    return weights
