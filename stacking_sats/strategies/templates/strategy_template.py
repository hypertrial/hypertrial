"""
Strategy template for creating custom investment strategies.

Copy this template to create your own strategy by implementing
the prepare_data and generate_weights methods.
"""
import pandas as pd
import numpy as np
from stacking_sats.strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    """
    Template for a custom investment strategy.
    
    Rename this class and implement your own strategy logic.
    """
    
    def __init__(self, 
                 # Add your strategy parameters here
                 param1: float = 0.5,
                 param2: int = 200):
        """
        Initialize your strategy with parameters.
        
        Parameters:
            param1 (float): Example parameter 1
            param2 (int): Example parameter 2
        """
        # Call the parent class constructor with all parameters
        super().__init__(param1=param1, param2=param2)
        
        # Store parameters for easy access (optional)
        self.param1 = param1
        self.param2 = param2
    
    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data by adding strategy-specific features.
        
        Parameters:
            data (pd.DataFrame): Raw price data with at least a price column
            
        Returns:
            pd.DataFrame: Data with added features
        """
        # Create a copy to avoid modifying the original data
        df = data.copy()
        
        # Assume 'btc_close' is the price column
        price_col = 'btc_close'
        if price_col not in df.columns:
            raise ValueError(f"Price column '{price_col}' not found in data")
        
        # IMPLEMENT YOUR FEATURE CALCULATIONS HERE
        # Example: Calculate moving averages
        df['ma_short'] = df[price_col].rolling(window=50, min_periods=1).mean()
        df['ma_long'] = df[price_col].rolling(window=self.param2, min_periods=1).mean()
        
        # Example: Calculate volatility
        df['volatility'] = df[price_col].rolling(window=30, min_periods=1).std()
        
        return df
    
    def generate_weights(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate allocation weights for each time period.
        
        Parameters:
            data (pd.DataFrame): Prepared data with features
            
        Returns:
            pd.Series: Series of weights indexed by date
        """
        # Initialize weights with zeros
        weights = pd.Series(0.0, index=data.index)
        
        # IMPLEMENT YOUR WEIGHT CALCULATION LOGIC HERE
        # Example: Allocate more when price is below long-term moving average
        signal = (data['ma_short'] > data['ma_long']).astype(float)
        
        # Simple example: Equal weights adjusted by signal
        n_days = len(data)
        base_weight = 1.0 / n_days
        
        # Adjust weights based on signal and param1
        weights = pd.Series(base_weight, index=data.index)
        weights = weights * (1 + signal * self.param1)
        
        # Normalize to ensure weights sum to 1
        weights = weights / weights.sum()
        
        # Validate weights
        if not self.validate_weights(weights):
            raise ValueError("Generated weights are invalid. Check your implementation.")
        
        return weights 