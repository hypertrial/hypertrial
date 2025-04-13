# dynamic_dca_200ma.py
"""
A dynamic DCA strategy that implements a constrained early bias rebalancing approach
using a 200-day moving average.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from core.config import BACKTEST_START, BACKTEST_END, ALPHA, REBALANCE_WINDOW, MIN_WEIGHT
from core.strategies import register_strategy

# Use a global variable to cache the results
_GLOBAL_CACHE = {}

@register_strategy("dynamic_dca_200ma")
def dynamic_rule_causal_200ma(df: pd.DataFrame) -> pd.Series:
    """
    A dynamic DCA strategy with 200-day moving average that boosts purchases 
    when BTC price drops below the short-term average.
    
    This implementation is strictly causal, using only past data for all calculations.
    """
    global _GLOBAL_CACHE
    
    # Simple cache key based on dataframe shape and date range
    cache_key = f"{df.shape[0]}_{df.index.min().strftime('%Y%m%d')}_{df.index.max().strftime('%Y%m%d')}"
    
    # Return cached result if available
    if cache_key in _GLOBAL_CACHE:
        return _GLOBAL_CACHE[cache_key].copy()
    
    # Create a working copy of the dataframe
    df_work = df.copy()
    
    # Create the shifted prices first (exclude today's price from calculation)
    past_prices = df_work['btc_close'].shift(1)
    
    # Calculate features using only past data
    df_work['ma200'] = past_prices.rolling(window=200, min_periods=1).mean()
    df_work['std200'] = past_prices.rolling(window=200, min_periods=1).std()
    
    # Extract backtest period
    df_backtest = df_work.loc[BACKTEST_START:BACKTEST_END]
    
    # Initialize weights Series
    weights = pd.Series(index=df_backtest.index, dtype=float)
    
    # Group by cycle (4-year periods)
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    
    # Process each cycle
    for cycle, group in df_backtest.groupby(cycle_labels):
        N = len(group)
        base_weight = 1.0 / N
        temp_weights = np.full(N, base_weight)
        strategy_active = True
        
        # Process each day in the cycle
        for i in range(N):
            if not strategy_active:
                break
            
            price = group['btc_close'].iloc[i]
            ma200 = group['ma200'].iloc[i]
            std200 = group['std200'].iloc[i]
            
            # Skip if we don't have valid MA data (beginning of time series)
            if pd.isna(ma200) or pd.isna(std200) or std200 <= 0:
                continue
            
            # Apply strategy logic
            if price < ma200:
                z = (ma200 - price) / std200
                boost_multiplier = 1 + ALPHA * z
                current_weight = temp_weights[i]
                boosted_weight = current_weight * boost_multiplier
                excess = boosted_weight - current_weight
                
                # Calculate redistribution
                start_redistribution = max(N - REBALANCE_WINDOW, i + 1)
                if start_redistribution >= N:
                    continue
                
                # Get indices for redistribution
                redistribution_idx = np.arange(start_redistribution, N)
                if len(redistribution_idx) == 0:
                    continue
                    
                reduction = excess / len(redistribution_idx)
                projected = temp_weights[redistribution_idx] - reduction
                
                # Check if the redistribution would violate minimum weight constraints
                if np.all(projected >= MIN_WEIGHT):
                    temp_weights[i] = boosted_weight
                    temp_weights[redistribution_idx] -= reduction
                else:
                    strategy_active = False
        
        # Assign weights for this cycle
        weights.loc[group.index] = temp_weights
    
    # Cache the result
    _GLOBAL_CACHE[cache_key] = weights.copy()
    
    return weights 