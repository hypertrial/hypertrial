# SPD Validation Checks

The Hypertrial framework includes a comprehensive set of validation checks to ensure that all strategies submitted to the tournament meet the required criteria. These checks are implemented in `core/spd_checks.py` and are automatically run when strategies are evaluated.

## Overview

The validation system verifies that a strategy:

1. Produces strictly positive weights
2. Maintains weights above the minimum threshold
3. Produces weights that sum to 1.0 for each market cycle
4. Outperforms uniform DCA in terms of SPD percentile
5. Is causal (not forward-looking, i.e., does not use future data)

The validation results are returned as a dictionary with flags for each criterion, along with cycle-specific issues where applicable.

## Validation Criteria in Detail

### Criterion 1: Strictly Positive Weights

```python
if (w_slice <= 0).any():
    print(f"[{cycle_label}] ❌ Some weights are zero or negative.")
    passed = False
    validation_results['has_negative_weights'] = True
    cycle_issues[cycle_label]['has_negative_weights'] = True
```

This check ensures that all weights produced by a strategy are strictly positive. Negative weights would imply selling Bitcoin rather than buying it, which is not allowed in the DCA tournament. Zero weights would imply skipping certain days entirely, which is also not allowed.

Strategies must produce a positive weight for every day in the backtest period to pass this criterion.

### Criterion 2: Weights Above Minimum Threshold

```python
if (w_slice < MIN_WEIGHT).any():
    print(f"[{cycle_label}] ❌ Some weights are below MIN_WEIGHT = {MIN_WEIGHT}.")
    passed = False
    validation_results['has_below_min_weights'] = True
    cycle_issues[cycle_label]['has_below_min_weights'] = True
```

All weights must be above a minimum threshold defined by `MIN_WEIGHT` (typically set to a small value like 1e-4). This ensures that no day is completely skipped in the investment strategy. While extremely small weights are allowed, they must not fall below this threshold.

### Criterion 3: Weights Sum to 1.0 per Cycle

```python
total_weight = w_slice.sum().sum() if isinstance(w_slice, pd.DataFrame) else w_slice.sum()
if not np.isclose(total_weight, 1.0, rtol=1e-5, atol=1e-8):
    print(f"[{cycle_label}] ❌ Total weights across the cycle do not sum to 1 (sum = {total_weight:.6f}).")
    passed = False
    validation_results['weights_not_sum_to_one'] = True
    cycle_issues[cycle_label]['weights_not_sum_to_one'] = True
    cycle_issues[cycle_label]['weight_sum'] = float(total_weight)
```

The sum of all weights within each market cycle must equal 1.0. This ensures that strategies allocate exactly 100% of the investment budget across each cycle, allowing for fair comparison between strategies.

A small tolerance is allowed for floating-point precision issues, but the sum should be very close to exactly 1.0.

### Criterion 4: SPD Performance ≥ Uniform DCA

```python
if row['dynamic_pct'] < row['uniform_pct']:
    print(f"[{cycle}] ❌ Dynamic SPD percentile ({row['dynamic_pct']:.2f}%) is less than uniform ({row['uniform_pct']:.2f}%).")
    passed = False
    validation_results['underperforms_uniform'] = True
    cycle_issues[cycle]['underperforms_uniform'] = True
    cycle_issues[cycle]['dynamic_pct'] = float(row['dynamic_pct'])
    cycle_issues[cycle]['uniform_pct'] = float(row['uniform_pct'])
```

Strategies must outperform uniform DCA (investing the same amount every day) in terms of SPD percentile for each market cycle. The SPD percentile represents where the strategy's Satoshis Per Dollar falls within the range from minimum to maximum possible for the cycle.

A strategy that performs worse than simple uniform DCA in any market cycle fails this criterion. This ensures that all strategies in the tournament provide at least some improvement over the baseline approach.

### Criterion 5: Strategy Must Be Causal (Not Forward-Looking)

```python
def is_causal(construct_features_func, df_test, test_indices, perturb_func, rtol=1e-5, atol=1e-8):
    # Implementation details...

# Run the causality test
is_causal_result = is_causal(construct_features, df, test_indices, perturb_func)

if not is_causal_result:
    print("❌ Strategy features may be forward-looking: they use information from future data.")
    passed = False
    validation_results['is_forward_looking'] = True
else:
    print("✅ Strategy features appear to be causal (not forward-looking).")
```

This check ensures that strategies do not use future information that wouldn't be available at the time of investment. A strategy is causal if its features at time t depend only on data available up to time t.

The test works by:

1. Selecting specific test points throughout the dataset
2. Perturbing (changing) future data after each test point
3. Checking if features at the test point change due to future data perturbation
4. If features change, the strategy is using future information

The implementation uses a sophisticated approach to avoid false positives:

- Test points are selected after a warm-up period to allow moving averages to stabilize
- Multiple test points are checked across the dataset
- Small numerical differences are allowed through tolerance parameters
- NaN values are properly handled
- Future data is significantly perturbed to detect any dependence

For a strategy to pass this test, its feature computation must only depend on past and present data, never on future data.

## Using Validation Results

The validation system returns detailed results that can be used to identify and fix issues in strategies:

```python
validation_results = {
    'validation_passed': True/False,
    'has_negative_weights': True/False,
    'has_below_min_weights': True/False,
    'weights_not_sum_to_one': True/False,
    'underperforms_uniform': True/False,
    'is_forward_looking': True/False,
    'cycle_issues': {
        '2013–2016': { ... cycle-specific issues ... },
        '2017–2020': { ... cycle-specific issues ... },
        '2021–2024': { ... cycle-specific issues ... }
    }
}
```

The cycle-specific issues provide details about which market cycles fail which criteria, allowing for targeted improvements to strategies.

## Calling the Validation System

The validation system can be called directly using:

```python
from core.spd_checks import check_strategy_submission_ready

# Simple validation (returns True/False)
is_valid = check_strategy_submission_ready(df, strategy_name)

# Detailed validation results
results = check_strategy_submission_ready(df, strategy_name, return_details=True)
```

The validation system is also automatically called when strategies are tested using the Hypertrial framework's command-line interface, unless the `--no-validate` flag is specified.

## Tips for Passing All Validations

1. **Positive Weights**: Ensure your strategy always outputs positive weights, typically by taking absolute values or clipping any negative values.

2. **Minimum Weight**: Apply a minimum threshold to all weights (e.g., `np.maximum(weights, MIN_WEIGHT)`).

3. **Sum to One**: Normalize your weights to sum to 1.0 for each cycle (e.g., `weights / weights.sum()`).

4. **Performance**: Test against uniform DCA and adjust your strategy if it underperforms in any cycle.

5. **Causality**: Implement feature construction that only uses past data:
   - Always use `.shift(1)` or greater to access previous days' data
   - For moving averages, use `rolling()` on shifted data
   - Avoid any operations that might peek into the future
   - Keep your feature code simple and auditable
