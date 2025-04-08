# dynamic_dca_50ma.py
import pandas as pd
import numpy as np
from core.config import BACKTEST_START, BACKTEST_END, ALPHA, REBALANCE_WINDOW, MIN_WEIGHT
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class DynamicDCA50MAStrategy(StrategyTemplate):
    """
    A dynamic DCA strategy that implements a constrained early bias rebalancing approach.
    For days where btc_close is below ma50, boosts the weight by a factor
    determined by the z-score and redistributes the excess weight.
    """
    
    @staticmethod
    def construct_features(df):
        """
        Constructs additional features for the strategy.
        Calculates:
          - 50-day moving average (ma50) of btc_close.
          - 50-day rolling standard deviation (std50) of btc_close.
        """
        df = df.copy()
        df['ma50'] = df['btc_close'].rolling(window=50, min_periods=1).mean()
        df['std50'] = df['btc_close'].rolling(window=50, min_periods=1).std()
        return df
    
    @staticmethod
    def compute_weights(df):
        """
        Implements a constrained early bias rebalancing strategy.
        For days where btc_close is below ma50, boosts the weight by a factor
        determined by the z-score and redistributes the excess weight.
        """
        df = df.loc[BACKTEST_START:BACKTEST_END]
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
                ma50 = group['ma50'].iloc[i]
                std50 = group['std50'].iloc[i]

                if price < ma50 and std50 > 0:
                    z = (ma50 - price) / std50
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

# Create a function wrapper that will be registered
@register_strategy("dynamic_dca_50ma")
def dynamic_rule_causal_50ma(df):
    """
    A dynamic DCA strategy that implements a constrained early bias rebalancing approach
    using a 50-day moving average.
    """
    return DynamicDCA50MAStrategy.get_strategy_function()(df) 