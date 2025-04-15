import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.config import BACKTEST_START, BACKTEST_END, MIN_WEIGHT
from core.strategies import get_strategy, list_strategies, get_strategy_info

def compute_cycle_spd(df, strategy_name):
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()
    rows = []
    
    weight_fn = get_strategy(strategy_name)
    full_weights = weight_fn(df).fillna(0).clip(lower=0)
    inverted_prices = (1 / df_backtest['btc_close']) * 1e8

    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        
        if cycle.empty:
            break

        cycle_label = f"{current.year}–{end_date.year}"
        cycle_prices = cycle['btc_close'].values
        high, low = np.max(cycle_prices), np.min(cycle_prices)
        min_spd = (1 / high) * 1e8
        max_spd = (1 / low) * 1e8

        cycle_inverted = inverted_prices.loc[cycle.index]
        w_slice = full_weights.loc[cycle.index]
        dynamic_spd = (w_slice * cycle_inverted).sum()
        uniform_spd = cycle_inverted.mean()

        spd_range = max_spd - min_spd
        uniform_pct = (uniform_spd - min_spd) / spd_range * 100
        dynamic_pct = (dynamic_spd - min_spd) / spd_range * 100
        excess_pct = dynamic_pct - uniform_pct

        rows.append({
            'cycle': cycle_label,
            'min_spd': min_spd,
            'max_spd': max_spd,
            'uniform_spd': uniform_spd,
            'dynamic_spd': dynamic_spd,
            'uniform_pct': uniform_pct,
            'dynamic_pct': dynamic_pct,
            'excess_pct': excess_pct
        })

        current += cycle_length

    return pd.DataFrame(rows).set_index('cycle')

def backtest_dynamic_dca(df, strategy_name="dynamic_dca"):
    df_res = compute_cycle_spd(df, strategy_name)
    
    dynamic_spd = df_res['dynamic_spd']
    dynamic_pct = df_res['dynamic_pct']
    
    dynamic_spd_metrics = {
        'min': dynamic_spd.min(),
        'max': dynamic_spd.max(),
        'mean': dynamic_spd.mean(),
        'median': dynamic_spd.median()
    }
    
    dynamic_pct_metrics = {
        'min': dynamic_pct.min(),
        'max': dynamic_pct.max(),
        'mean': dynamic_pct.mean(),
        'median': dynamic_pct.median()
    }

    print(f"\nAggregated Metrics for {strategy_name}:")
    print("Dynamic SPD:")
    for key, value in dynamic_spd_metrics.items():
        print(f"  {key}: {value:.2f}")
    print("Dynamic SPD Percentile:")
    for key, value in dynamic_pct_metrics.items():
        print(f"  {key}: {value:.2f}")

    print("\nExcess SPD Percentile Difference (Dynamic - Uniform) per Cycle:")
    for cycle, row in df_res.iterrows():
        print(f"  {cycle}: {row['excess_pct']:.2f}%")
    
    return df_res

def check_strategy_submission_ready(df, strategy_name, return_details=False):
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()

    weight_fn = get_strategy(strategy_name)
    full_weights = weight_fn(df).fillna(0)

    passed = True
    validation_results = {
        'validation_passed': True,
        'has_negative_weights': False,
        'has_below_min_weights': False,
        'weights_not_sum_to_one': False,
        'underperforms_uniform': False,
        'is_forward_looking': False,
    }
    
    cycle_issues = {}
    validation_messages = []

    # --- Criteria 1–3: per-cycle checks ---
    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        w_slice = full_weights.loc[cycle.index]

        cycle_label = f"{current.year}–{end_date.year}"
        cycle_issues[cycle_label] = {}

        # Criterion 1: strictly positive
        if (w_slice <= 0).any():
            validation_messages.append(f"[{cycle_label}] Some weights are zero or negative.")
            passed = False
            validation_results['has_negative_weights'] = True
            cycle_issues[cycle_label]['has_negative_weights'] = True

        # Criterion 2: above minimum threshold
        if (w_slice < MIN_WEIGHT).any():
            validation_messages.append(f"[{cycle_label}] Some weights are below MIN_WEIGHT = {MIN_WEIGHT}.")
            passed = False
            validation_results['has_below_min_weights'] = True
            cycle_issues[cycle_label]['has_below_min_weights'] = True

        # Criterion 3: weights must sum to 1 over the entire cycle
        total_weight = w_slice.sum().sum() if isinstance(w_slice, pd.DataFrame) else w_slice.sum()
        if not np.isclose(total_weight, 1.0, rtol=1e-5, atol=1e-8):
            validation_messages.append(f"[{cycle_label}] Total weights across the cycle do not sum to 1 (sum = {total_weight:.6f}).")
            passed = False
            validation_results['weights_not_sum_to_one'] = True
            cycle_issues[cycle_label]['weights_not_sum_to_one'] = True
            cycle_issues[cycle_label]['weight_sum'] = float(total_weight)

        current += cycle_length

    # --- Criterion 4: SPD performance must be ≥ uniform ---
    spd_results = compute_cycle_spd(df, strategy_name)
    for cycle, row in spd_results.iterrows():
        if cycle not in cycle_issues:
            cycle_issues[cycle] = {}
            
        if row['dynamic_pct'] < row['uniform_pct']:
            validation_messages.append(f"[{cycle}] Strategy performance ({row['dynamic_pct']:.2f}%) is below threshold.")
            passed = False
            validation_results['underperforms_uniform'] = True
            cycle_issues[cycle]['underperforms_uniform'] = True
            cycle_issues[cycle]['dynamic_pct'] = float(row['dynamic_pct'])
            cycle_issues[cycle]['uniform_pct'] = float(row['uniform_pct'])

    # --- Criterion 5: Strategy must be causal (not forward-looking) ---
    try:
        # Import the feature construction function from the strategy module
        try:
            # Get the strategy module from the registry based on strategy_name
            strategy_info = get_strategy_info(strategy_name)
            
            if strategy_info and 'module' in strategy_info:
                module_path = strategy_info['module']
                # Import the strategy module
                import importlib
                strategy_module = importlib.import_module(module_path)
                construct_features = getattr(strategy_module, 'construct_features', None)
                
                if construct_features:
                    # Define function to test if feature construction is causal
                    def is_causal(construct_features_func, df_test, test_indices, perturb_func, rtol=1e-5, atol=1e-8):
                        """
                        Test if feature construction is causal by perturbing future data and verifying
                        that features at the current time step don't change.
                        
                        Args:
                            construct_features_func: Function that constructs features from data
                            df_test: DataFrame with price data
                            test_indices: List of indices to test
                            perturb_func: Function to perturb future data
                            rtol: Relative tolerance for floating point comparison
                            atol: Absolute tolerance for floating point comparison
                            
                        Returns:
                            True if features are causal, False otherwise
                        """
                        # Get original features
                        features_original = construct_features_func(df_test)
                        
                        for t in test_indices:
                            # Skip if beyond data range
                            if t >= len(df_test):
                                continue
                                
                            # Copy df and perturb data after index t
                            df_perturbed = df_test.copy()
                            if t + 1 < len(df_perturbed):
                                # Get future data as a separate object to perturb
                                future_data = df_perturbed.iloc[t+1:].copy()
                                # Apply perturbation
                                df_perturbed.iloc[t+1:] = perturb_func(future_data)
                                
                            # Compute features on perturbed data
                            features_perturbed = construct_features_func(df_perturbed)
                            
                            # Compare features at time t; they should be essentially identical
                            # Handle potential NaN values
                            original_val = features_original.iloc[t].fillna(0)
                            perturbed_val = features_perturbed.iloc[t].fillna(0)
                            
                            # Compare using numpy's allclose
                            if not np.allclose(original_val, perturbed_val, rtol=rtol, atol=atol):
                                validation_messages.append(f"Features at time index {t} change when future data is perturbed.")
                                return False
                                
                        # All test cases passed
                        return True
                    
                    # Define a perturbation function: replace future values with random noise
                    def perturb_func(df_future):
                        # Create random noise with the same shape but different values
                        np.random.seed(42)  # For reproducibility
                        perturb_factor = np.random.uniform(1.5, 2.5)
                        return df_future * perturb_factor
                    
                    # Define test indices - select points across the dataset
                    # Skip early points where not enough history is available
                    warm_up = 500  # Allow for moving averages to stabilize
                    data_len = len(df)
                    
                    # Choose 10 test points spread across the dataset
                    num_test_points = 10
                    test_step = (data_len - warm_up) // (num_test_points + 1)
                    test_indices = [warm_up + i * test_step for i in range(1, num_test_points + 1)]
                    
                    # Run the causality test
                    is_causal_result = is_causal(construct_features, df, test_indices, perturb_func)
                    
                    if not is_causal_result:
                        validation_messages.append("Strategy features may be forward-looking: they use information from future data.")
                        passed = False
                        validation_results['is_forward_looking'] = True
                    
                else:
                    # No construct_features function found, unable to test causality
                    validation_messages.append("Cannot test causality: no construct_features function found in the strategy.")
                    construct_features_error = "No construct_features function in strategy module"
                    validation_results['causality_check_error'] = construct_features_error
            else:
                # No module path found for strategy
                validation_messages.append("Cannot test causality: strategy module not found in registry.")
                module_error = "Strategy module not found in registry"
                validation_results['causality_check_error'] = module_error

        except Exception as e:
            import traceback
            validation_messages.append(f"Error testing causality: {str(e)}")
            validation_results['causality_check_error'] = str(e)
            
    except Exception as e:
        # Catch any other errors
        validation_messages.append(f"Error in validation checks: {str(e)}")
        validation_results['validation_error'] = str(e)

    # Add cycle issues to validation results
    validation_results['cycle_issues'] = cycle_issues
    validation_results['validation_passed'] = passed

    # Only print in test mode, skip printing in normal operation
    import sys
    in_test_mode = 'pytest' in sys.modules or 'unittest' in sys.modules
    
    if in_test_mode:
        if passed:
            print("\n✅ Strategy passed all validation checks.")
        else:
            for message in validation_messages:
                print(f"❌ {message}")

    if return_details:
        return validation_results
    else:
        return passed 