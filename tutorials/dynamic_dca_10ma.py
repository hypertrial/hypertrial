# dynamic_dca_10ma.py
"""
A dynamic DCA strategy that implements a constrained early bias rebalancing approach
using a 10-day moving average.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from core.config import BACKTEST_START, BACKTEST_END, ALPHA, REBALANCE_WINDOW, MIN_WEIGHT
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class DynamicDCA10MAStrategy(StrategyTemplate):
    """
    A dynamic DCA strategy that implements a constrained early bias rebalancing approach.
    
    For days where btc_close is below the 10-day moving average, boosts the weight by a factor
    determined by the z-score and redistributes the excess weight to future dates.
    
    This strategy works best in volatile markets where there are significant price drops
    below the 10-day moving average.
    """
    
    @staticmethod
    def construct_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Constructs additional features needed for the strategy.
        
        Args:
            df (pd.DataFrame): Input price data with at least 'btc_close' column
            
        Returns:
            pd.DataFrame: DataFrame with 10-day moving average and standard deviation features
        """
        df = df.copy()
        
        # Calculate 10-day moving average and standard deviation
        df['ma10'] = df['btc_close'].rolling(window=10, min_periods=1).mean()
        df['std10'] = df['btc_close'].rolling(window=10, min_periods=1).std()
        
        return df
    
    @staticmethod
    def compute_weights(df: pd.DataFrame) -> pd.Series:
        """
        Compute the weight allocation for each day in the dataframe.
        
        Args:
            df (pd.DataFrame): Input data with features
            
        Returns:
            pd.Series: Series of weights indexed by date
        """
        df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
        weights = pd.Series(index=df_backtest.index, dtype=float)
        
        # Group by 4-year cycles
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        for cycle, group in df_backtest.groupby(cycle_labels):
            N = len(group)
            base_weight = 1.0 / N
            temp_weights = np.full(N, base_weight)
            strategy_active = True
            
            for i in range(N):
                if not strategy_active:
                    break
                    
                price = group['btc_close'].iloc[i]
                ma10 = group['ma10'].iloc[i]
                std10 = group['std10'].iloc[i]
                
                # Apply boost when price is below 10-day moving average and std is positive
                if price < ma10 and std10 > 0:
                    # Calculate z-score
                    z = (ma10 - price) / std10
                    
                    # Boost weight based on z-score
                    boost_multiplier = 1 + ALPHA * z
                    current_weight = temp_weights[i]
                    boosted_weight = current_weight * boost_multiplier
                    excess = boosted_weight - current_weight
                    
                    # Determine where to redistribute the excess weight
                    start_redistribution = max(N - REBALANCE_WINDOW, i + 1)
                    if start_redistribution >= N:
                        continue
                        
                    # Calculate how much to reduce future weights
                    redistribution_idx = np.arange(start_redistribution, N)
                    reduction = excess / len(redistribution_idx)
                    projected = temp_weights[redistribution_idx] - reduction
                    
                    # Apply changes only if all future weights remain above minimum threshold
                    if np.all(projected >= MIN_WEIGHT):
                        temp_weights[i] = boosted_weight
                        temp_weights[redistribution_idx] -= reduction
                    else:
                        strategy_active = False
                        
            # Assign weights for this cycle
            weights.loc[group.index] = temp_weights
            
        return weights

@register_strategy("dynamic_dca_10ma")
def dynamic_rule_causal_10ma(df: pd.DataFrame) -> pd.Series:
    """
    A dynamic DCA strategy with 10-day moving average that boosts purchases 
    when BTC price drops below the short-term average.
    """
    return DynamicDCA10MAStrategy.get_strategy_function()(df) 