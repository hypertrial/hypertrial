import pandas as pd
import numpy as np
from typing import Dict, Any
from core.config import BACKTEST_START, BACKTEST_END, MIN_WEIGHT
from core.strategies import register_strategy

_GLOBAL_CACHE = {}

def construct_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Shift the btc_close column by one to use only past data for our calculations
    past_close = df['btc_close'].shift(1)
    df['ma200'] = past_close.rolling(window=200, min_periods=1).mean()
    df['std200'] = past_close.rolling(window=200, min_periods=1).std()
    return df

@register_strategy("dynamic_dca_200ma")
def compute_weights(df: pd.DataFrame) -> pd.Series:
    #global _GLOBAL_CACHE
    
    REBALANCE_WINDOW = 365 * 2
    ALPHA = 1.25
    
    cache_key = f"{df.shape[0]}_{df.index.min().strftime('%Y%m%d')}_{df.index.max().strftime('%Y%m%d')}"
    
    if cache_key in _GLOBAL_CACHE:
        return _GLOBAL_CACHE[cache_key].copy()
    
    df_work = df.copy()

    df_work = construct_features(df)
    
    df_backtest = df_work.loc[BACKTEST_START:BACKTEST_END]
    weights = pd.Series(index=df_backtest.index, dtype=float)
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
            ma200 = group['ma200'].iloc[i]
            std200 = group['std200'].iloc[i]
            
            if pd.isna(ma200) or pd.isna(std200) or std200 <= 0:
                continue
            
            if price < ma200:
                z = (ma200 - price) / std200
                boost_multiplier = 1 + ALPHA * z
                current_weight = temp_weights[i]
                boosted_weight = current_weight * boost_multiplier
                excess = boosted_weight - current_weight
                
                start_redistribution = max(N - REBALANCE_WINDOW, i + 1)
                if start_redistribution >= N:
                    continue
                
                redistribution_idx = np.arange(start_redistribution, N)
                if len(redistribution_idx) == 0:
                    continue
                    
                reduction = excess / len(redistribution_idx)
                projected = temp_weights[redistribution_idx] - reduction
                
                if np.all(projected >= MIN_WEIGHT):
                    temp_weights[i] = boosted_weight
                    temp_weights[redistribution_idx] -= reduction
                else:
                    strategy_active = False
        
        weights.loc[group.index] = temp_weights
    
    _GLOBAL_CACHE[cache_key] = weights.copy()
    return weights
