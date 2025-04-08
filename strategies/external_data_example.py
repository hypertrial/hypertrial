import pandas as pd
import numpy as np
import pandas_datareader as pdr
from scipy import stats
import time
import os

# Configuration values
from core.config import BACKTEST_START, BACKTEST_END

class ExternalDataStrategy:
    """
    Example strategy demonstrating how to incorporate external data sources.
    
    This strategy uses gold prices from Yahoo Finance as an external data source
    and combines it with Bitcoin price data to make trading decisions. The approach
    is based on the relationship between Bitcoin and gold as alternative stores of value.
    
    External data sources:
    - Gold prices (GLD ETF) from Yahoo Finance
    - Optional: Treasury yields from Federal Reserve Economic Data (FRED)
    
    Features:
    - Bitcoin-to-gold ratio
    - Rate of change in the Bitcoin-to-gold ratio
    - Optional: Risk-adjusted Bitcoin-to-gold ratio using Treasury yields
    
    Weighting approach:
    - Allocate more weight when Bitcoin is undervalued relative to gold
    - Reduce weight when Bitcoin is overvalued relative to gold
    - Use moving averages to identify trend changes in the ratio
    """
    
    def __init__(self):
        """Initialize strategy parameters."""
        self.name = "external_data_example"
        self.window_short = 7     # 1-week moving average
        self.window_medium = 30   # 1-month moving average
        self.window_long = 90     # 3-month moving average
        self.data_cache = {}      # Cache for external data
        
    def get_gold_data(self, start_date, end_date):
        """
        Retrieve gold price data from Yahoo Finance with caching.
        
        Args:
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            
        Returns:
            DataFrame with gold price data
        """
        cache_key = f"gold_{start_date}_{end_date}"
        
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
            # Add some buffer days to ensure we have enough data for calculations
            buffer_days = 30
            extended_start = pd.to_datetime(start_date) - pd.Timedelta(days=buffer_days)
            extended_end = pd.to_datetime(end_date) + pd.Timedelta(days=5)
            
            # Get data from Yahoo Finance
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
            # Return empty DataFrame with expected columns if API call fails
            return pd.DataFrame(columns=['Close', 'High', 'Low', 'Open', 'Volume'])
    
    def construct_features(self, df):
        """
        Construct features using Bitcoin price data and external data.
        
        Args:
            df: DataFrame with Bitcoin price data
            
        Returns:
            DataFrame with additional features
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        try:
            # Get gold price data
            gold_data = self.get_gold_data(df.index.min(), df.index.max())
            
            if not gold_data.empty:
                # Merge gold data with Bitcoin data
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
                df['trend_slope'] = df[f'ratio_ma_{self.window_medium}'].rolling(window=self.window_medium, min_periods=5).apply(
                    lambda x: stats.linregress(np.arange(len(x)), x)[0], raw=True
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
        Compute portfolio weights based on features.
        
        Args:
            df: DataFrame with Bitcoin price data and features
            
        Returns:
            Series with weights for each date in the backtest period
        """
        # Use only the backtest period for weight calculation
        df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
        
        try:
            # Base weights on the z-score of the Bitcoin-to-gold ratio
            # Lower z-score means Bitcoin is relatively cheap compared to gold
            weights = 1.0 - (0.1 * df_backtest['ratio_zscore'])
            
            # Adjust weights based on trend direction and strength
            trend_factor = np.clip(df_backtest['trend_slope'] * 5.0, -0.5, 0.5)
            weights = weights + trend_factor
            
            # Apply moving average crossover signals
            # Increase weight when short MA crosses above medium MA (bullish)
            crossover_signal = ((df_backtest[f'ratio_ma_{self.window_short}'] > df_backtest[f'ratio_ma_{self.window_medium}']) & 
                               (df_backtest[f'ratio_ma_{self.window_medium}'] > df_backtest[f'ratio_ma_{self.window_long}']))
            weights = weights + (0.2 * crossover_signal)
            
            # Ensure weights are positive
            weights = weights.clip(lower=0.1, upper=2.0)
        
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