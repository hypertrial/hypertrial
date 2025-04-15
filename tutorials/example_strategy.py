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
    # Calculate 200-day moving average
    df['ma200'] = past_close.rolling(window=200, min_periods=1).mean()
    # Calculate 200-day standard deviation
    df['std200'] = past_close.rolling(window=200, min_periods=1).std()
    return df

# Example Ethereum wallet address - replace with real one for actual submissions
ETH_WALLET_ADDRESS = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"

@register_strategy(ETH_WALLET_ADDRESS)
def compute_weights(df: pd.DataFrame) -> pd.Series:
    """
    Computes daily DCA weights with a 200-day moving average strategy.
    Increases weight on days when price is below MA, redistributing from future days.
    
    Strategy logic:
    1. Start with uniform weights across each market cycle
    2. For days when price < 200MA, boost weight proportional to distance below MA
    3. Redistribute the excess weight from future days within a rebalance window
    4. Maintain minimum weight constraints for all days
    
    Args:
        df: DataFrame with BTC price data
        
    Returns:
        Series of daily investment weights, summing to 1.0 per market cycle
    """
    # Strategy parameters
    REBALANCE_WINDOW = 365 * 2  # Redistribute weight from up to 2 years ahead
    ALPHA = 1.25  # Multiplier for how much to boost weight based on z-score
    
    df_work = df.copy()
    df_work = construct_features(df)
    
    # Filter to backtest period only
    df_backtest = df_work.loc[BACKTEST_START:BACKTEST_END]
    weights = pd.Series(index=df_backtest.index, dtype=float)
    
    # Group by 4-year market cycles
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    
    # Process each market cycle separately to maintain weight sum = 1.0 per cycle
    for cycle, group in df_backtest.groupby(cycle_labels):
        N = len(group)
        base_weight = 1.0 / N  # Start with uniform weight distribution
        temp_weights = np.full(N, base_weight)
        strategy_active = True  # Flag to stop adjustments if constraints can't be met
        
        # Process each day in the cycle
        for i in range(N):
            if not strategy_active:
                break
            
            price = group['btc_close'].iloc[i]
            ma200 = group['ma200'].iloc[i]
            std200 = group['std200'].iloc[i]
            
            # Skip days with insufficient history
            if pd.isna(ma200) or pd.isna(std200) or std200 <= 0:
                continue
            
            # Apply weight boost when price is below MA
            if price < ma200:
                # Calculate z-score (standard deviations below MA)
                z = (ma200 - price) / std200
                boost_multiplier = 1 + ALPHA * z
                current_weight = temp_weights[i]
                boosted_weight = current_weight * boost_multiplier
                excess = boosted_weight - current_weight
                
                # Determine which future days to redistribute from
                start_redistribution = max(N - REBALANCE_WINDOW, i + 1)
                if start_redistribution >= N:
                    continue  # No future days to redistribute from
                
                redistribution_idx = np.arange(start_redistribution, N)
                if len(redistribution_idx) == 0:
                    continue
                    
                # Calculate reduction per future day
                reduction = excess / len(redistribution_idx)
                projected = temp_weights[redistribution_idx] - reduction
                
                # Only apply changes if minimum weight constraint is satisfied
                if np.all(projected >= MIN_WEIGHT):
                    temp_weights[i] = boosted_weight
                    temp_weights[redistribution_idx] -= reduction
                else:
                    # Stop strategy adjustments if constraints can't be met
                    strategy_active = False
        
        # Assign weights back to the original index
        weights.loc[group.index] = temp_weights
    
    return weights
