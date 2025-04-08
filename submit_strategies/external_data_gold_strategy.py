"""
Strategy that uses external gold price data alongside Bitcoin price data.

This strategy follows the tournament submission format and demonstrates how to:
1. Retrieve external data from Yahoo Finance
2. Implement data caching for efficient backtesting
3. Create features combining Bitcoin and gold prices
4. Handle API failures gracefully
"""
import pandas as pd
import numpy as np
import os
import time
from typing import Dict, Any
from datetime import datetime, timedelta
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class ExternalDataGoldStrategy(StrategyTemplate):
    """
    Tournament strategy that incorporates gold price data from Yahoo Finance to inform
    Bitcoin investment decisions. The strategy is based on the principle that Bitcoin
    and gold share properties as alternative stores of value.
    
    External data sources:
    - Yahoo Finance API: Gold price data (GLD ETF)
    
    The strategy computes the Bitcoin-to-Gold ratio and adjusts investment weights
    based on whether Bitcoin appears undervalued or overvalued relative to gold.
    It also considers the trend and momentum of this relationship.
    
    Features:
    - Bitcoin-to-Gold ratio
    - Moving averages of the ratio (7, 30, and 90 days)
    - Z-score of the ratio to detect extreme valuations
    - Trend slope to identify directional movements
    """
    
    def __init__(self):
        """Initialize strategy parameters."""
        self.name = "external_data_gold_strategy"
        self.window_short = 7     # 1-week moving average
        self.window_medium = 30   # 1-month moving average
        self.window_long = 90     # 3-month moving average
        self.data_cache = {}      # Cache for external data
    
    @staticmethod
    def get_strategy_function():
        """Return a function that can be called with a dataframe to run the strategy."""
        def strategy_function(df):
            strategy = ExternalDataGoldStrategy()
            df_with_features = strategy.construct_features(df)
            return strategy.compute_weights(df_with_features)
        return strategy_function
    
    def get_gold_data(self, start_date, end_date):
        """
        Retrieve gold price data from Yahoo Finance with caching.
        
        Args:
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            DataFrame with gold price data or None if retrieval failed
        """
        # Create a deterministic cache key
        start_str = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_str = pd.to_datetime(end_date).strftime('%Y-%m-%d')
        cache_key = f"gold_{start_str}_{end_str}"
        
        # Check if data is already in cache
        if cache_key in self.data_cache:
            return self.data_cache[cache_key]
        
        # Define cache directory and file
        cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, f"{cache_key}.csv")
        
        # Try to load from file cache first
        try:
            if os.path.exists(cache_file):
                gold_data = pd.read_csv(cache_file, index_col=0, parse_dates=True)
                self.data_cache[cache_key] = gold_data
                return gold_data
        except Exception as e:
            print(f"Error reading cache file: {e}")
        
        # If not in cache, retrieve from API
        try:
            # Add buffer days to ensure we have enough data for calculations
            buffer_days = 30
            extended_start = pd.to_datetime(start_date) - pd.Timedelta(days=buffer_days)
            extended_end = pd.to_datetime(end_date) + pd.Timedelta(days=5)
            
            # Get data from Yahoo Finance
            import pandas_datareader as pdr
            gold_data = pdr.get_data_yahoo('GLD', 
                                          extended_start.strftime('%Y-%m-%d'), 
                                          extended_end.strftime('%Y-%m-%d'))
            
            # Save to cache
            self.data_cache[cache_key] = gold_data
            try:
                gold_data.to_csv(cache_file)
            except Exception as e:
                print(f"Error saving to cache file: {e}")
                
            return gold_data
            
        except Exception as e:
            print(f"Error retrieving gold data: {e}")
            return None
    
    def construct_features(self, df):
        """
        Constructs additional features needed for the strategy.
        
        Args:
            df (pd.DataFrame): Input price data with at least 'btc_close' column
            
        Returns:
            pd.DataFrame: DataFrame with additional features
        """
        df = df.copy()
        
        try:
            # Get gold price data
            gold_data = self.get_gold_data(df.index.min(), df.index.max())
            
            if gold_data is not None and not gold_data.empty:
                # Merge gold data with Bitcoin data (reindex to match Bitcoin dates)
                gold_price = gold_data['Close'].reindex(df.index, method='ffill')
                
                # Calculate Bitcoin-to-gold ratio
                df['btc_gold_ratio'] = df['btc_close'] / gold_price
                
                # Calculate moving averages of the ratio
                df[f'ratio_ma_{self.window_short}'] = df['btc_gold_ratio'].rolling(window=self.window_short, min_periods=1).mean()
                df[f'ratio_ma_{self.window_medium}'] = df['btc_gold_ratio'].rolling(window=self.window_medium, min_periods=1).mean()
                df[f'ratio_ma_{self.window_long}'] = df['btc_gold_ratio'].rolling(window=self.window_long, min_periods=1).mean()
                
                # Calculate rate of change in the ratio
                df['ratio_roc'] = df['btc_gold_ratio'].pct_change(periods=self.window_short)
                
                # Calculate z-score of the ratio compared to historical values
                # This helps identify when BTC is relatively cheap or expensive compared to gold
                ratio_rolling = df['btc_gold_ratio'].rolling(window=365, min_periods=90)
                df['ratio_zscore'] = (df['btc_gold_ratio'] - ratio_rolling.mean()) / ratio_rolling.std()
                
                # Calculate the trend strength using the slope of the medium-term moving average
                from scipy import stats
                df['trend_slope'] = df[f'ratio_ma_{self.window_medium}'].rolling(window=self.window_medium, min_periods=5).apply(
                    lambda x: stats.linregress(np.arange(len(x)), x)[0] if len(x) > 2 else 0, raw=True
                )
                
            else:
                # If gold data retrieval failed, use fallback features
                print("Using fallback features due to missing gold data")
                df['btc_gold_ratio'] = 1.0
                df[f'ratio_ma_{self.window_short}'] = 1.0
                df[f'ratio_ma_{self.window_medium}'] = 1.0 
                df[f'ratio_ma_{self.window_long}'] = 1.0
                df['ratio_roc'] = 0.0
                df['ratio_zscore'] = 0.0
                df['trend_slope'] = 0.0
                
        except Exception as e:
            print(f"Error in construct_features: {e}")
            # Set default values if feature construction fails
            df['btc_gold_ratio'] = 1.0
            df[f'ratio_ma_{self.window_short}'] = 1.0
            df[f'ratio_ma_{self.window_medium}'] = 1.0 
            df[f'ratio_ma_{self.window_long}'] = 1.0
            df['ratio_roc'] = 0.0
            df['ratio_zscore'] = 0.0
            df['trend_slope'] = 0.0
            
        return df
    
    def compute_weights(self, df):
        """
        Compute the weight allocation for each day in the dataframe.
        
        Args:
            df (pd.DataFrame): Input data with features
            
        Returns:
            pd.Series: Series of weights indexed by date
        """
        # Use only the backtest period for weight calculation
        df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
        
        try:
            # Base weights on the z-score of the Bitcoin-to-gold ratio
            # Lower z-score means Bitcoin is relatively cheap compared to gold
            weights = pd.Series(index=df_backtest.index, data=0.0)
            
            # Only compute weights if the required columns exist
            if 'ratio_zscore' in df_backtest.columns:
                # More weight when BTC is undervalued relative to gold
                weights = 1.0 - (0.2 * df_backtest['ratio_zscore'])
                
                # Adjust weights based on trend direction and strength
                if 'trend_slope' in df_backtest.columns:
                    trend_factor = np.clip(df_backtest['trend_slope'] * 5.0, -0.5, 0.5)
                    weights = weights + trend_factor
                
                # Apply moving average crossover signals
                # Increase weight when short MA crosses above medium MA (bullish)
                if all(col in df_backtest.columns for col in [f'ratio_ma_{self.window_short}', f'ratio_ma_{self.window_medium}', f'ratio_ma_{self.window_long}']):
                    crossover_signal = ((df_backtest[f'ratio_ma_{self.window_short}'] > df_backtest[f'ratio_ma_{self.window_medium}']) & 
                                      (df_backtest[f'ratio_ma_{self.window_medium}'] > df_backtest[f'ratio_ma_{self.window_long}']))
                    weights = weights + (0.2 * crossover_signal)
            else:
                # Fallback to uniform weighting
                weights = pd.Series(index=df_backtest.index, data=1.0)
            
            # Ensure weights are positive
            weights = weights.clip(lower=0.1)
        
        except Exception as e:
            print(f"Error computing weights with external data: {e}")
            # Fallback to uniform weighting if weight computation fails
            weights = pd.Series(index=df_backtest.index, data=1.0)
        
        # Make sure the weights are valid (non-negative)
        weights = weights.clip(lower=0)
        
        # Normalize weights by investment cycle (4-year periods)
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        for cycle, group in weights.groupby(cycle_labels):
            cycle_sum = group.sum()
            if cycle_sum > 0:
                weights.loc[group.index] = weights.loc[group.index] / cycle_sum
                
        return weights
    
    def backtest(self, df):
        """
        Run backtest for the strategy.
        
        Args:
            df: DataFrame with Bitcoin price data
            
        Returns:
            Series with weights for each date in the backtest period
        """
        # Add features
        df_with_features = self.construct_features(df)
        
        # Compute weights
        weights = self.compute_weights(df_with_features)
        
        return weights

# Register the tournament entry
@register_strategy("external_data_gold_strategy")
def external_data_gold_strategy(df):
    """Tournament strategy using gold price data to identify Bitcoin investment opportunities."""
    return ExternalDataGoldStrategy.get_strategy_function()(df) 