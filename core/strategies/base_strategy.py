# base_strategy.py
import pandas as pd
import numpy as np
from typing import Callable
from core.strategies import register_strategy

class StrategyTemplate:
    """Base class that all strategies should inherit from"""
    
    @staticmethod
    def construct_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Constructs additional features needed for the strategy.
        
        Args:
            df (pd.DataFrame): Input price data
            
        Returns:
            pd.DataFrame: DataFrame with additional features
        """
        raise NotImplementedError("Subclasses must implement construct_features")
    
    @staticmethod
    def compute_weights(df: pd.DataFrame) -> pd.Series:
        """
        Compute the weight allocation for each day in the dataframe.
        
        Args:
            df (pd.DataFrame): Input data with features
            
        Returns:
            pd.Series: Series of weights indexed by date
        """
        raise NotImplementedError("Subclasses must implement compute_weights")
    
    @classmethod
    def get_strategy_function(cls) -> Callable:
        """
        Returns a function that can be used as a strategy function.
        This function should be registered using the @register_strategy decorator.
        
        Returns:
            Callable: A function that takes a dataframe and returns weights
        """
        def strategy_function(df: pd.DataFrame) -> pd.Series:
            """
            Strategy function to be used by the backtester.
            
            Args:
                df (pd.DataFrame): Input price data
                
            Returns:
                pd.Series: Series of weights indexed by date
            """
            df_features = cls.construct_features(df)
            weights = cls.compute_weights(df_features)
            return weights
            
        # Set the docstring to the class docstring for better documentation
        strategy_function.__doc__ = cls.__doc__
        return strategy_function 