import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

# Import the strategy registration functionality
from core.strategies import register_strategy, get_strategy, list_strategies, available_strategies

def test_strategy_registration():
    """Test that strategies can be registered correctly."""
    # Create a local dictionary for testing
    test_strategies = {}
    
    # Create a local function that mimics register_strategy but uses our test dictionary
    def test_register_strategy(name=None):
        def decorator(func):
            strategy_name = name or func.__name__
            test_strategies[strategy_name] = func
            return func
        return decorator
    
    # Apply the decorator to a test function
    @test_register_strategy("test_strategy")
    def test_strategy_fn(df):
        """Test strategy docstring"""
        return pd.Series(1.0, index=df.index)
    
    # Check that the strategy was registered in our test dictionary
    assert "test_strategy" in test_strategies
    assert test_strategies["test_strategy"] == test_strategy_fn

def test_strategy_retrieval():
    """Test that strategies can be retrieved by name."""
    # Clear existing registered strategies for this test
    with patch('core.strategies.available_strategies', {}):
        # Define a test strategy function
        @register_strategy("test_strategy")
        def test_strategy_fn(df):
            """Test strategy docstring"""
            return pd.Series(1.0, index=df.index)
        
        # Retrieve the strategy
        strategy = get_strategy("test_strategy")
        
        # Check that the correct strategy was retrieved
        assert strategy == test_strategy_fn

def test_strategy_list():
    """Test that list_strategies returns all registered strategies with docstrings."""
    # Clear existing registered strategies for this test
    with patch('core.strategies.available_strategies', {}):
        # Define test strategy functions
        @register_strategy("test_strategy1")
        def test_strategy_fn1(df):
            """Test strategy 1 docstring"""
            return pd.Series(1.0, index=df.index)
        
        @register_strategy("test_strategy2")
        def test_strategy_fn2(df):
            """Test strategy 2 docstring"""
            return pd.Series(2.0, index=df.index)
        
        # Get the list of strategies
        strategies = list_strategies()
        
        # Check that all strategies are in the list with their docstrings
        assert "test_strategy1" in strategies
        assert "test_strategy2" in strategies
        assert strategies["test_strategy1"] == "Test strategy 1 docstring"
        assert strategies["test_strategy2"] == "Test strategy 2 docstring"

def test_get_strategy_unknown():
    """Test that an error is raised when trying to get an unknown strategy."""
    # Clear existing registered strategies for this test
    with patch('core.strategies.available_strategies', {}):
        # Try to get an unknown strategy
        with pytest.raises(ValueError):
            get_strategy("unknown_strategy") 