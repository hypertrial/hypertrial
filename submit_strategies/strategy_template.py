# strategy_template.py
"""
Template for creating a new strategy.

To create a new strategy:
1. Copy this file to a new file in the 'submit_strategies' directory (e.g., my_strategy.py)
2. Rename the strategy function and update the docstring
3. Implement your strategy logic
4. Register the strategy with your Ethereum wallet address using the @register_strategy decorator
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from core.config import BACKTEST_START, BACKTEST_END, MIN_WEIGHT
from core.strategies import register_strategy

def construct_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construct technical indicators used for the strategy.
    Uses only past data for calculations to avoid look-ahead bias.
    
    Args:
        df: DataFrame with price data
        
    Returns:
        DataFrame with added technical indicators
    """
    df = df.copy()
    
    # Shift the btc_close column by one to use only past data for our calculations
    past_close = df['btc_close'].shift(1)
    
    # EXAMPLE FEATURE CALCULATIONS (uncomment and modify as needed):
    # --------------------------------------------------------------
    
    # 1. Moving averages
    # df['ma_20'] = past_close.rolling(window=20, min_periods=1).mean()
    # df['ma_50'] = past_close.rolling(window=50, min_periods=1).mean()
    # df['ma_200'] = past_close.rolling(window=200, min_periods=1).mean()
    
    # 2. Volatility measures
    # df['volatility'] = past_close.pct_change().rolling(window=20).std()
    
    # 3. Momentum indicators
    # df['momentum'] = past_close.pct_change(periods=14)
    
    # 4. Binary indicators
    # df['below_ma'] = (past_close < df['ma_50']).astype(int)
    
    return df

# IMPORTANT: Replace this with your own Ethereum wallet address
ETH_WALLET_ADDRESS = "0x0000000000000000000000000000000000000000"

@register_strategy(ETH_WALLET_ADDRESS)
def compute_weights(df: pd.DataFrame) -> pd.Series:
    """
    A simple template strategy that uses uniform weight allocation.
    
    This basic strategy assigns equal weights to all trading days within each 4-year cycle.
    It serves as a starting point for creating more sophisticated strategies.
    
    Args:
        df: DataFrame with BTC price data
        
    Returns:
        Series of daily investment weights, summing to 1.0 per market cycle
    """
    # Create a working copy and add features
    df_work = df.copy()
    df_work = construct_features(df)
    
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
        
        # 1. Uniform weighting (baseline)
        temp_weights = np.full(N, 1.0 / N)
        
        # EXAMPLE WEIGHTING STRATEGIES (uncomment and modify as needed):
        # --------------------------------------------------------------
        
        # 2. Weight based on distance from moving average
        # for i in range(N):
        #     price = group['btc_close'].iloc[i]
        #     ma_value = group['ma_50'].iloc[i]
        #     if pd.notna(ma_value) and price < ma_value:
        #         # Increase weight when price is below MA
        #         temp_weights[i] *= 1.5
        
        # 3. Higher weights in bearish periods (below MA)
        # bearish_indices = group['btc_close'] < group['ma_200']
        # temp_weights[bearish_indices] *= 2.0
        
        # 4. Custom strategy logic - modify to implement your approach
        # ...
        
        # Ensure weights sum to 1.0 within the cycle
        if sum(temp_weights) > 0:
            temp_weights = temp_weights / sum(temp_weights)
        
        # Ensure minimum weight constraint is satisfied
        temp_weights = np.maximum(temp_weights, MIN_WEIGHT)
        if sum(temp_weights) > 1.0:
            temp_weights = temp_weights / sum(temp_weights)
        
        # Assign weights for this cycle
        weights.loc[group.index] = temp_weights
    
    return weights 