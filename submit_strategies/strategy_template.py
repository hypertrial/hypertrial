# strategy_template.py
"""
Template for creating a new strategy.

To create a new strategy:
1. Copy this file to a new file in the 'submit_strategies' directory (e.g., my_strategy.py)
2. Rename the class and update the docstring
3. Implement the construct_features and compute_weights methods
4. Register the strategy with a unique name by uncommenting and modifying the decorator at the bottom
"""
import pandas as pd
import numpy as np
from typing import Dict, Any
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class NewStrategy(StrategyTemplate):
    """
    Description of your strategy goes here.
    
    This should explain:
    - The key idea behind your strategy
    - What market conditions it works best in
    - Any theoretical basis for the approach
    - Expected performance characteristics
    """
    
    @staticmethod
    def construct_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Constructs additional features needed for the strategy.
        
        Args:
            df (pd.DataFrame): Input price data with at least 'btc_close' column
            
        Returns:
            pd.DataFrame: DataFrame with additional features
            
        Example:
            # Calculate moving averages
            df['ma_20'] = df['btc_close'].rolling(window=20).mean()
            df['ma_50'] = df['btc_close'].rolling(window=50).mean()
            
            # Calculate relative price position
            df['price_to_ma_ratio'] = df['btc_close'] / df['ma_50']
            
            # Calculate volatility
            df['volatility'] = df['btc_close'].pct_change().rolling(window=20).std()
        """
        df = df.copy()
        
        # EXAMPLE FEATURE CALCULATIONS (uncomment and modify as needed):
        # --------------------------------------------------------------
        # 1. Moving averages
        # df['ma_20'] = df['btc_close'].rolling(window=20).mean()
        # df['ma_50'] = df['btc_close'].rolling(window=50).mean()
        # df['ma_200'] = df['btc_close'].rolling(window=200).mean()
        
        # 2. Price relative to moving average
        # df['price_to_ma_ratio'] = df['btc_close'] / df['ma_50']
        # df['pct_from_ma'] = (df['btc_close'] / df['ma_50'] - 1) * 100
        
        # 3. Volatility measures
        # df['volatility'] = df['btc_close'].pct_change().rolling(window=20).std()
        
        # 4. Momentum indicators
        # df['momentum'] = df['btc_close'].pct_change(periods=14)
        
        # 5. Binary indicators
        # df['below_ma'] = (df['btc_close'] < df['ma_50']).astype(int)
        
        return df
    
    @staticmethod
    def compute_weights(df: pd.DataFrame) -> pd.Series:
        """
        Compute the weight allocation for each day in the dataframe.
        
        Args:
            df (pd.DataFrame): Input data with features
            
        Returns:
            pd.Series: Series of weights indexed by date, ideally normalized
            to sum to 1.0 within each 4-year cycle
            
        Notes:
            - Weights should be positive (zero is allowed)
            - The backtester will clip very small weights to zero
            - The backtester will normalize to sum to 1.0 within cycles
        """
        df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
        weights = pd.Series(index=df_backtest.index, data=0.0)
        
        # EXAMPLE WEIGHTING STRATEGIES (uncomment and modify as needed):
        # --------------------------------------------------------------
        # 1. Uniform weighting (baseline)
        # weights = pd.Series(index=df_backtest.index, data=1.0)
        
        # 2. Weight based on distance from moving average
        # weights = 1.0 + 2.0 * (df_backtest['ma_50'] - df_backtest['btc_close']) / df_backtest['ma_50']
        # weights = weights.clip(lower=0.1)  # Ensure minimum weight
        
        # 3. Higher weights in bearish periods (below MA)
        # weights[df_backtest['btc_close'] < df_backtest['ma_50']] = 2.0
        # weights[df_backtest['btc_close'] >= df_backtest['ma_50']] = 0.5
        
        # 4. Volatility-based weighting (more weight during low volatility)
        # weights = 1.0 / df_backtest['volatility']
        # weights = weights.fillna(0).replace([np.inf, -np.inf], 0)
        
        # 5. Seasonal weighting
        # weights = pd.Series(index=df_backtest.index, data=1.0)
        # Q4_months = [10, 11, 12]
        # weights[df_backtest.index.month.isin(Q4_months)] = 2.0  # Higher weight in Q4
        
        # NORMALIZE WEIGHTS BY CYCLE - THIS IS REQUIRED
        # ----------------------------------------------
        # Group by 4-year cycles and normalize weights within each cycle
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        # Normalize weights so each cycle sums to 1.0
        for cycle, group in weights.groupby(cycle_labels):
            cycle_sum = group.sum()
            if cycle_sum > 0:
                weights.loc[group.index] = weights.loc[group.index] / cycle_sum
        
        return weights

# UNCOMMENT AND MODIFY TO REGISTER YOUR STRATEGY
# ---------------------------------------------
# @register_strategy("my_strategy_name")
# def my_strategy(df: pd.DataFrame) -> pd.Series:
#     """
#     Brief description of your strategy that will appear in --list output.
#     """
#     return NewStrategy.get_strategy_function()(df) 