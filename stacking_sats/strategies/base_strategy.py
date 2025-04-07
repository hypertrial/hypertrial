"""
Base strategy class that defines the interface for all strategies.
"""
import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseStrategy(ABC):
    """
    Abstract base class for all investment strategies.
    
    This class defines the interface that all strategy implementations must follow.
    Users creating custom strategies should inherit from this class and implement
    the required methods.
    """
    
    def __init__(self, **params):
        """
        Initialize the strategy with parameters.
        
        Parameters:
            **params: Strategy-specific parameters
        """
        self.params = params
        
    @abstractmethod
    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data by adding strategy-specific features.
        
        This method should add any required indicators or features to the input data.
        
        Parameters:
            data (pd.DataFrame): Raw price data
            
        Returns:
            pd.DataFrame: Data with added features
        """
        pass
    
    @abstractmethod
    def generate_weights(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate allocation weights for each time period.
        
        This is the core method of the strategy, which determines how much capital
        to allocate at each time step.
        
        Parameters:
            data (pd.DataFrame): Prepared data with features
            
        Returns:
            pd.Series: Series of weights indexed by date
        """
        pass
    
    def validate_weights(self, weights: pd.Series) -> bool:
        """
        Validate that the weights are properly formatted.
        
        Parameters:
            weights (pd.Series): Series of weights
            
        Returns:
            bool: True if weights are valid, False otherwise
        """
        # Weights should sum to approximately 1.0
        weight_sum = weights.sum()
        if not 0.99 <= weight_sum <= 1.01:
            return False
        
        # Weights should be non-negative
        if (weights < 0).any():
            return False
            
        return True
    
    def get_params(self) -> Dict[str, Any]:
        """
        Get all strategy parameters.
        
        Returns:
            Dict[str, Any]: Dictionary of parameters
        """
        return self.params
    
    def set_params(self, **params):
        """
        Set strategy parameters.
        
        Parameters:
            **params: Parameters to set
        """
        self.params.update(params)
        
    def __str__(self) -> str:
        """
        Return string representation of the strategy.
        
        Returns:
            str: Strategy name and parameters
        """
        return f"{self.__class__.__name__}(params={self.params})" 