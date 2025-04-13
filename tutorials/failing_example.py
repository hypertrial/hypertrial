# ---------------------------
# dynamic_rule_causal strategy
# ---------------------------
import pandas as pd
import numpy as np
from typing import Dict, Any
from core.config import BACKTEST_START, BACKTEST_END, MIN_WEIGHT
from core.strategies import register_strategy

# Strategy constants
REBALANCE_WINDOW = 365 * 2
ALPHA = 1.25

@register_strategy("dynamic_rule_causal")
def dynamic_rule_causal(df: pd.DataFrame) -> pd.Series:
    """
    A dynamic DCA strategy that implements a constrained early bias rebalancing approach.
    """
    # Create a working copy of the dataframe
    df_work = df.copy()
    
    # Calculate features
    df_work['ma200'] = df_work['btc_close'].rolling(window=200, min_periods=1).mean()
    df_work['std200'] = df_work['btc_close'].rolling(window=200, min_periods=1).std()
    
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
            ma = group['ma200'].iloc[i]
            std = group['std200'].iloc[i]
            
            # Skip if we don't have valid MA data (beginning of time series)
            if pd.isna(ma) or pd.isna(std) or std <= 0:
                continue
            
            # Apply strategy logic
            if price < ma:
                z = (ma - price) / std
                boost = 1 + ALPHA * z
                boosted = temp_weights[i] * boost
                excess = boosted - temp_weights[i]
                
                # Calculate redistribution
                start_idx = max(N - REBALANCE_WINDOW, i + 1)
                if start_idx >= N:
                    continue
                
                # Get indices for redistribution
                idxs = np.arange(start_idx, N)
                if len(idxs) == 0:
                    continue
                    
                reduction = excess / len(idxs)
                projected = temp_weights[idxs] - reduction
                
                # Check if the redistribution would violate minimum weight constraints
                if np.all(projected >= MIN_WEIGHT):
                    temp_weights[i] = boosted
                    temp_weights[idxs] -= reduction
                else:
                    strategy_active = False
        
        # Assign weights for this cycle
        weights.loc[group.index] = temp_weights
    
    return weights