import pytest
import os
import sys
import pandas as pd
import numpy as np
import importlib.util
from pathlib import Path

# Suppress matplotlib output for testing
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
plt.ioff()  # Turn off interactive mode

# Function to import a module from a file path
def import_module_from_path(file_path, module_name="dynamic_module"):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def example_strategy_path():
    """Get the path to the example strategy."""
    path = os.path.abspath("tutorials/example_strategy.py")
    if not os.path.exists(path):
        pytest.skip(f"Example strategy file not found at {path}")
    return path

@pytest.fixture
def strategy_module(example_strategy_path):
    """Import the strategy module."""
    return import_module_from_path(example_strategy_path, "example_strategy")

@pytest.fixture
def test_df():
    """Load real Bitcoin price data for testing instead of synthetic data.
    
    This test uses real Bitcoin price data to ensure that the example strategy,
    which has been updated to use a 200-day moving average, passes all SPD 
    validation checks including outperforming the uniform DCA strategy in 
    all market cycles.
    """
    # Path to real data file
    data_path = os.path.abspath("core/data/btc_price_data.csv")
    if not os.path.exists(data_path):
        pytest.skip(f"Bitcoin price data file not found at {data_path}")
    
    # Load real data
    try:
        df = pd.read_csv(data_path, index_col=0, parse_dates=True)
        
        # Ensure we have the right column
        if 'btc_close' not in df.columns:
            # Try to find a suitable price column
            price_cols = [col for col in df.columns if 'price' in col.lower() or 'close' in col.lower()]
            if price_cols:
                df = df.rename(columns={price_cols[0]: 'btc_close'})
            else:
                # Create btc_close from the first column if needed
                df = df.rename(columns={df.columns[0]: 'btc_close'})
        
        # Return data within the backtest range, making sure we include all of 2024
        backtest_range = df.loc['2013-01-01':'2024-12-31']
        
        # If 2024 data is incomplete, fill with the last available price
        # to ensure we have a complete cycle
        if '2024-12-31' not in backtest_range.index:
            last_date = backtest_range.index.max()
            missing_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), end='2024-12-31')
            missing_df = pd.DataFrame(index=missing_dates, columns=['btc_close'])
            missing_df['btc_close'] = backtest_range['btc_close'].iloc[-1]
            backtest_range = pd.concat([backtest_range, missing_df])
        
        return backtest_range
    except Exception as e:
        pytest.skip(f"Failed to load Bitcoin price data: {str(e)}")
        return None

def test_module_imports(strategy_module):
    """Test that the module can be imported successfully."""
    assert strategy_module is not None
    assert hasattr(strategy_module, 'DynamicDCA200MAStrategy')
    assert hasattr(strategy_module, 'dynamic_rule_causal_200ma')

def test_strategy_class(strategy_module):
    """Test the DynamicDCA200MAStrategy class."""
    strategy_class = strategy_module.DynamicDCA200MAStrategy
    
    # Test class methods
    assert hasattr(strategy_class, 'construct_features')
    assert hasattr(strategy_class, 'compute_weights')
    assert hasattr(strategy_class, 'get_strategy_function')

def test_construct_features(strategy_module, test_df):
    """Test the construct_features method."""
    strategy_class = strategy_module.DynamicDCA200MAStrategy
    
    # Call the method
    result_df = strategy_class.construct_features(test_df)
    
    # Check the result
    assert isinstance(result_df, pd.DataFrame)
    assert 'ma200' in result_df.columns
    assert 'std200' in result_df.columns
    
    # Check that the original DataFrame is not modified
    assert 'ma200' not in test_df.columns
    assert 'std200' not in test_df.columns

def test_compute_weights(strategy_module, test_df):
    """Test the compute_weights method."""
    strategy_class = strategy_module.DynamicDCA200MAStrategy
    
    # First construct features
    df_with_features = strategy_class.construct_features(test_df)
    
    # Call the method
    weights = strategy_class.compute_weights(df_with_features)
    
    # Check the result
    assert isinstance(weights, pd.Series)
    assert len(weights) == len(df_with_features.loc['2013-01-01':'2024-12-31'])
    
    # Check that weights sum to 1.0 for each cycle
    years = weights.index.year
    unique_years = years.unique()
    for start_year in range(2013, 2025, 4):
        if start_year in unique_years:
            cycle_years = [y for y in range(start_year, start_year + 4) if y in unique_years]
            cycle_mask = years.isin(cycle_years)
            cycle_sum = weights[cycle_mask].sum()
            assert abs(cycle_sum - 1.0) < 0.0001

def test_strategy_function(strategy_module, test_df):
    """Test the registered strategy function."""
    strategy_fn = strategy_module.dynamic_rule_causal_200ma
    
    # Call the function
    weights = strategy_fn(test_df)
    
    # Check the result
    assert isinstance(weights, pd.Series)
    assert len(weights) == len(test_df.loc['2013-01-01':'2024-12-31'])
    
    # Check that weights are all positive
    assert (weights >= 0).all()
    
    # Check that weights sum to 1.0 for each cycle
    years = weights.index.year
    unique_years = years.unique()
    for start_year in range(2013, 2025, 4):
        if start_year in unique_years:
            cycle_years = [y for y in range(start_year, start_year + 4) if y in unique_years]
            cycle_mask = years.isin(cycle_years)
            cycle_sum = weights[cycle_mask].sum()
            assert abs(cycle_sum - 1.0) < 0.0001

def test_strategy_registration(example_strategy_path):
    """Test that the strategy is properly registered."""
    # We can't directly import core.strategies without affecting the real registry,
    # so we'll just check if the registration decorator is applied correctly
    with open(example_strategy_path, 'r') as f:
        source_code = f.read()
    assert '@register_strategy("dynamic_dca_200ma")' in source_code

def test_spd_checks_pass(strategy_module, test_df):
    """Test that the strategy passes all security and SPD checks."""
    # Import the spd_checks module
    spd_checks_path = os.path.abspath("core/spd_checks.py")
    if not os.path.exists(spd_checks_path):
        pytest.skip(f"SPD checks file not found at {spd_checks_path}")
    
    spd_checks_module = import_module_from_path(spd_checks_path, "spd_checks")
    
    try:
        # First test if the strategy function can be called without errors
        strategy_fn = strategy_module.dynamic_rule_causal_200ma
        weights = strategy_fn(test_df)
        assert isinstance(weights, pd.Series)
        
        # Make sure core.strategies is imported in the test environment
        strategies_path = os.path.abspath("core/strategies/__init__.py")
        if not os.path.exists(strategies_path):
            pytest.skip(f"Strategies module not found at {strategies_path}")
        
        strategies_module = import_module_from_path(strategies_path, "strategies")
        
        # Register the strategy for testing if needed
        if "dynamic_dca_200ma" not in strategies_module.list_strategies():
            strategies_module.register_strategy("dynamic_dca_200ma")(strategy_module.dynamic_rule_causal_200ma)
        
        # Run the checks
        check_result = spd_checks_module.check_strategy_submission_ready(
            test_df, 
            "dynamic_dca_200ma", 
            return_details=True
        )
        
        # Print detailed results for debugging
        for key, value in check_result.items():
            if key != 'cycle_issues':
                print(f"{key}: {value}")
        
        if 'cycle_issues' in check_result and check_result['cycle_issues']:
            print("Cycle issues detected:")
            for cycle, issues in check_result['cycle_issues'].items():
                print(f"  Cycle {cycle}:")
                for issue_key, issue_val in issues.items():
                    print(f"    {issue_key}: {issue_val}")
        
        # Verify all checks pass
        assert check_result['validation_passed'], f"Strategy failed validation: {check_result}"
        assert not check_result['has_negative_weights'], "Strategy has negative weights"
        assert not check_result['has_below_min_weights'], "Strategy has weights below minimum threshold"
        assert not check_result['weights_not_sum_to_one'], "Strategy weights don't sum to one"
        assert not check_result['underperforms_uniform'], "Strategy underperforms uniform DCA"
        
        # Also verify that the SPD is actually improved over uniform
        spd_results = spd_checks_module.compute_cycle_spd(test_df, "dynamic_dca_200ma")
        for cycle, row in spd_results.iterrows():
            assert row['dynamic_pct'] >= row['uniform_pct'], \
                f"Cycle {cycle}: Dynamic SPD ({row['dynamic_pct']:.2f}%) should be >= uniform ({row['uniform_pct']:.2f}%)"
                
    except Exception as e:
        pytest.fail(f"SPD checks test failed with error: {str(e)}") 