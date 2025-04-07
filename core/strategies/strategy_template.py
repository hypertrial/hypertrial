# strategy_template.py
"""
Template for creating a new strategy.
To create a new strategy:
1. Copy this file to a new file in the 'strategies' directory
2. Rename the class and update the docstring
3. Implement the construct_features and compute_weights methods
4. Register the strategy with a unique name
"""
import pandas as pd
import numpy as np
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class NewStrategy(StrategyTemplate):
    """
    Description of your strategy goes here.
    """
    
    @staticmethod
    def construct_features(df):
        """
        Constructs additional features needed for the strategy.
        
        Args:
            df (pd.DataFrame): Input price data with at least 'btc_close' column
            
        Returns:
            pd.DataFrame: DataFrame with additional features
        """
        df = df.copy()
        # Add your feature calculations here
        # For example:
        # df['my_feature'] = ...
        return df
    
    @staticmethod
    def compute_weights(df):
        """
        Compute the weight allocation for each day in the dataframe.
        
        Args:
            df (pd.DataFrame): Input data with features
            
        Returns:
            pd.Series: Series of weights indexed by date
        """
        df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
        # Implementation of your weighting strategy
        weights = pd.Series(index=df_backtest.index)
        
        # Example of uniform weights (replace with your algorithm)
        N = len(df_backtest)
        weights = pd.Series(index=df_backtest.index, data=1.0/N)
        
        return weights

# Uncomment and modify to register your strategy
# my_strategy = register_strategy("my_strategy_name")(NewStrategy.get_strategy_function()) 