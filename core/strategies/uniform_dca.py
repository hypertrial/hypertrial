# uniform_dca.py
import pandas as pd
import numpy as np
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class UniformDCAStrategy(StrategyTemplate):
    """
    A simple uniform DCA strategy that allocates equal weight to each day in the backtest period.
    This is the baseline strategy for comparison.
    """
    
    @staticmethod
    def construct_features(df):
        """
        No additional features needed for uniform DCA.
        """
        return df.copy()
    
    @staticmethod
    def compute_weights(df):
        """
        Computes uniform weights across the backtest period.
        """
        df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
        weights = pd.Series(index=df_backtest.index, dtype=float)
        
        # Group by 4-year cycles
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        # Calculate weights for each cycle separately to ensure each cycle sums to 1.0
        for cycle, group in df_backtest.groupby(cycle_labels):
            N = len(group)
            weights.loc[group.index] = 1.0 / N
            
        return weights

# Create a function wrapper that will be registered
@register_strategy("uniform_dca")
def uniform_dca(df):
    """
    A simple uniform DCA strategy that allocates equal weight to each day.
    """
    return UniformDCAStrategy.get_strategy_function()(df) 