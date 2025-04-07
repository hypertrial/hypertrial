"""
Tests for strategy implementations.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from stacking_sats.strategies.base_strategy import BaseStrategy


class SimpleTestStrategy(BaseStrategy):
    """A simple strategy for testing."""
    
    def __init__(self, alpha=0.5, beta=0.5):
        super().__init__(alpha=alpha, beta=beta)
        self.alpha = alpha
        self.beta = beta
    
    def prepare_data(self, data):
        """Add a simple moving average."""
        df = data.copy()
        df['sma'] = df['btc_close'].rolling(window=20).mean()
        return df
    
    def generate_weights(self, data):
        """Generate weights based on alpha and beta."""
        # Simple weight calculation based on parameters
        n = len(data)
        weights = pd.Series(self.alpha * np.ones(n), index=data.index)
        
        # Scale weights to sum to 1
        weights = weights / weights.sum()
        return weights


def test_base_strategy_init():
    """Test BaseStrategy initialization."""
    params = {"alpha": 0.5, "beta": 0.5}
    strategy = SimpleTestStrategy(**params)
    
    assert strategy.params == params
    assert strategy.alpha == 0.5
    assert strategy.beta == 0.5


def test_prepare_data_method(sample_price_data):
    """Test that prepare_data method adds features."""
    strategy = SimpleTestStrategy()
    prepared_data = strategy.prepare_data(sample_price_data)
    
    # Check that the SMA column was added
    assert "sma" in prepared_data.columns
    
    # Original data should be unchanged
    assert "sma" not in sample_price_data.columns


def test_generate_weights_method(sample_price_data):
    """Test that generate_weights produces valid weights."""
    strategy = SimpleTestStrategy(alpha=0.8, beta=0.2)
    prepared_data = strategy.prepare_data(sample_price_data)
    weights = strategy.generate_weights(prepared_data)
    
    # Check that weights are a pandas Series
    assert isinstance(weights, pd.Series)
    
    # Check that weights have the same index as the data
    assert weights.index.equals(prepared_data.index)
    
    # Check that weights sum to approximately 1
    assert 0.999 <= weights.sum() <= 1.001
    
    # Check that weights are non-negative
    assert (weights >= 0).all()


def test_validate_weights_method():
    """Test the validate_weights method."""
    strategy = SimpleTestStrategy()
    
    # Valid weights: sum to 1, all non-negative
    index = pd.date_range("2020-01-01", periods=5, freq="D")
    valid_weights = pd.Series([0.2, 0.2, 0.2, 0.2, 0.2], index=index)
    assert strategy.validate_weights(valid_weights) is True
    
    # Invalid weights: sum greater than 1
    invalid_weights1 = pd.Series([0.3, 0.3, 0.3, 0.3, 0.3], index=index)
    assert strategy.validate_weights(invalid_weights1) is False
    
    # Invalid weights: contains negative values
    invalid_weights2 = pd.Series([0.3, 0.3, 0.3, 0.3, -0.2], index=index)
    assert strategy.validate_weights(invalid_weights2) is False 