# strategy_template.py
"""
Template for creating a new strategy.

To create a new strategy:
1. Copy this file to a new file in the 'submit_strategies' directory (e.g., my_strategy.py)
2. Rename the strategy function and update the docstring
3. Implement your strategy logic
4. Register the strategy with a unique name using the @register_strategy decorator
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy

# Use a global variable to cache the results
_GLOBAL_CACHE = {}

@register_strategy("strategy_template")
def strategy_template(df: pd.DataFrame) -> pd.Series:
    """
    A simple template strategy that uses uniform weight allocation.
    
    This basic strategy assigns equal weights to all trading days within each 4-year cycle.
    It serves as a starting point for creating more sophisticated strategies.
    """
    global _GLOBAL_CACHE
    
    # Simple cache key based on dataframe shape and date range
    cache_key = f"{df.shape[0]}_{df.index.min().strftime('%Y%m%d')}_{df.index.max().strftime('%Y%m%d')}"
    
    # Return cached result if available
    if cache_key in _GLOBAL_CACHE:
        return _GLOBAL_CACHE[cache_key].copy()
    
    # Create a working copy of the dataframe
    df_work = df.copy()
    
    # EXAMPLE FEATURE CALCULATIONS (uncomment and modify as needed):
    # --------------------------------------------------------------
    # 1. Moving averages
    # df_work['ma_20'] = df_work['btc_close'].rolling(window=20, min_periods=1).mean()
    # df_work['ma_50'] = df_work['btc_close'].rolling(window=50, min_periods=1).mean()
    # df_work['ma_200'] = df_work['btc_close'].rolling(window=200, min_periods=1).mean()
    
    # 2. Price relative to moving average
    # df_work['price_to_ma_ratio'] = df_work['btc_close'] / df_work['ma_50']
    # df_work['pct_from_ma'] = (df_work['btc_close'] / df_work['ma_50'] - 1) * 100
    
    # 3. Volatility measures
    # df_work['volatility'] = df_work['btc_close'].pct_change().rolling(window=20).std()
    
    # 4. Momentum indicators
    # df_work['momentum'] = df_work['btc_close'].pct_change(periods=14)
    
    # 5. Binary indicators
    # df_work['below_ma'] = (df_work['btc_close'] < df_work['ma_50']).astype(int)
    
    # Extract backtest period
    df_backtest = df_work.loc[BACKTEST_START:BACKTEST_END]
    
    # Initialize weights Series
    weights = pd.Series(index=df_backtest.index, dtype=float)
    
    # Group by cycle (4-year periods)
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    
    # EXAMPLE WEIGHTING STRATEGIES (uncomment and modify as needed):
    # --------------------------------------------------------------
    
    # Process each cycle
    for cycle, group in df_backtest.groupby(cycle_labels):
        N = len(group)
        
        # 1. Uniform weighting (baseline)
        temp_weights = np.full(N, 1.0 / N)
        
        # 2. Weight based on distance from moving average
        # for i in range(N):
        #     price = group['btc_close'].iloc[i]
        #     ma_value = group['ma_50'].iloc[i]
        #     if pd.notna(ma_value) and price < ma_value:
        #         # Increase weight when price is below MA
        #         temp_weights[i] *= 1.5
        
        # 3. Higher weights in bearish periods (below MA)
        # bearish_indices = group['btc_close'] < group['ma_50']
        # temp_weights[bearish_indices] *= 2.0
        
        # 4. Custom strategy logic - modify to implement your approach
        # ...
        
        # Ensure weights sum to 1.0 within the cycle
        if sum(temp_weights) > 0:
            temp_weights = temp_weights / sum(temp_weights)
        
        # Assign weights for this cycle
        weights.loc[group.index] = temp_weights
    
    # Cache the result
    _GLOBAL_CACHE[cache_key] = weights.copy()
    
    return weights 