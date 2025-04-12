# Hypertrial: Stacking Sats Challenge - Strategy Verification Tests

This directory contains tests for verifying that your Stacking Sats Challenge submission meets all requirements.

## Package Installation

Hypertrial is available on PyPI and can be installed with pip:

```bash
pip install hypertrial
```

For development and testing purposes, it's recommended to install from source in development mode:

```bash
git clone https://github.com/mattfaltyn/hypertrial.git
cd hypertrial
pip install -e .
```

The PyPI package can be found at: https://pypi.org/project/hypertrial/

## Complete Test Suite

The test suite includes the following test files:

### Tournament Submission Tests

- `test_submit_strategies.py`: Tests strategies submitted to the `submit_strategies` directory
- `test_strategy_file.py`: Tests loading and executing standalone strategy files
- `test_strategy_files.py`: Tests batch loading of multiple strategy files

### Tutorial and Example Strategy Tests

- `test_tutorial_commands.py`: Tests all CLI commands against files in the tutorials directory
- `test_example_strategy.py`: Tests the functionality of the example strategy in the tutorials directory

### Security Tests

- `test_security.py`: Main security tests for strategy validation and sandboxing
- `test_bandit_security.py`: Tests for Bandit security analysis on submitted strategies

### Data Tests

- `test_data_basic.py`: Tests for basic data loading and validation
- `test_data_download.py`: Tests for data downloading functionality
- `test_data_download_integration.py`: Tests data integration with real-world sources

### Package Tests

- `test_installation.py`: Tests for proper package installation
- `test_setup.py`: Tests for proper package setup
- `test_package_deployment.py`: Tests for package deployment
- `test_installed_package.py`: Tests for installed package functionality
- `test_dist_files.py`: Tests for distribution files

### Requirements and Version Tests

- `test_requirements_compatibility.py`: Tests compatibility between packages in requirements.txt
- `test_version_constraints.py`: Tests version constraints in requirements.txt
- `test_validation_default.py`: Tests default validation configurations
- `test_spd_checks.py`: Tests software package data integrity checks

### CLI Tests

- `test_cli.py`: Tests command-line interface functionality

## Tournament Test Focus

As a tournament participant, you should focus on the `test_submit_strategies.py` file, which specifically tests strategies submitted to the `submit_strategies` directory.

## Verifying Your Tournament Submission

Your submitted strategy must pass all tests in `test_submit_strategies.py` to be considered valid for the tournament. These tests ensure your strategy follows the required format and can be executed successfully within the tournament framework.

### Running the Tournament Verification Tests

To verify your tournament submission:

```bash
pytest tests/test_submit_strategies.py -v
```

The `-v` flag provides verbose output so you can see exactly which tests pass or fail.

### Testing a Standalone Strategy File

You can test a standalone strategy file without placing it in the `submit_strategies` directory by using the `--strategy-file` command line option:

```bash
# Regular mode - loads the strategy file alongside other strategies
python -m core.main --strategy-file path/to/my_strategy.py

# Standalone mode - only loads the specified strategy file
python -m core.main --strategy-file path/to/my_strategy.py --standalone
```

The standalone mode provides several advantages during development:

1. **Isolation**: Tests your strategy in isolation without interference from other strategies.
2. **No Installation Required**: You don't need to add the strategy to the project structure.
3. **Rapid Testing**: Quickly iterate on your strategy without modifying the project.
4. **Direct Feedback**: Performance metrics are displayed immediately for your strategy only.

#### Testing Tutorial Example Strategy

The framework includes specific tests for validating the example strategy found in the tutorials directory:

```bash
# Test the example strategy functionality
pytest tests/test_example_strategy.py -v

# Test CLI commands with the tutorials directory
pytest tests/test_tutorial_commands.py -v
```

The `test_example_strategy.py` file tests:

1. The core functionality of the example strategy class
2. Feature construction and weight calculations
3. Registration and module imports
4. Output validation against cycle-based normalization requirements

The `test_tutorial_commands.py` file tests:

1. All commands from `commands.py` and `main.py` with the example strategy
2. Different CLI flags like `--standalone`, `--save-plots`, `--no-validate`
3. Batch processing and parallelization options
4. Directory filtering with `--include-patterns` and `--exclude-patterns`
5. Multiple strategy loading methods like `--strategy-dir` and `--glob-pattern`

These tests ensure that all command-line functionality works correctly with tutorial files. They use a non-interactive Matplotlib backend to prevent plots from being displayed during testing.

### Data Sources in Standalone Mode

When running in standalone mode, the system loads Bitcoin price data from:

1. The default local CSV file at `core/data/btc_price_data.csv`
2. If the file doesn't exist, data is automatically downloaded from the CoinMetrics API
3. You can specify a custom data file using the `--data-file` option:

```bash
python -m core.main --strategy-file path/to/my_strategy.py --standalone --data-file path/to/custom_data.csv
```

### Strategy File Requirements

The standalone strategy file must still follow the same format requirements as strategies in the `submit_strategies` directory:

1. It must include a class that extends `StrategyTemplate` with the required methods:

   - `construct_features`: For creating additional features from price data
   - `compute_weights`: For calculating weight allocations

2. It must register the strategy using the `@register_strategy` decorator
3. It must pass all the security checks that are applied to submitted strategies

### Standalone vs. Regular Mode

The difference between regular and standalone modes:

| Feature               | Regular Mode                 | Standalone Mode                       |
| --------------------- | ---------------------------- | ------------------------------------- |
| Command               | `--strategy-file` only       | `--strategy-file` with `--standalone` |
| Strategy Registration | Required                     | Required                              |
| Other Strategies      | Loaded                       | Not loaded                            |
| Data Source           | Same                         | Same                                  |
| Security Checks       | Applied                      | Applied                               |
| Performance Metrics   | Compared to other strategies | Standalone only                       |

The tests in `test_strategy_file.py` verify that both modes work correctly and safely.

### What the Verification Tests Check

The tests in `test_submit_strategies.py` check your strategy for:

1. **Discovery and Loading**: Your strategy is properly registered and can be loaded
2. **Execution Correctness**: Your strategy executes without errors
3. **Backtest Compatibility**: Your strategy works with the tournament backtesting engine
4. **Output Generation**: Your strategy produces valid output for evaluation
5. **Performance Comparison**: Your strategy can be compared against baseline strategies
6. **Security Compliance**: Your strategy passes security validation checks

## Requirements and Version Compatibility Tests

The framework includes comprehensive tests to ensure that all required packages are compatible with each other and meet the specified version constraints.

### Requirements Compatibility Tests

The `test_requirements_compatibility.py` file contains tests that:

1. Parse `requirements.txt` to extract package and version constraints
2. Verify that all packages can be imported successfully
3. Test compatibility between key packages:
   - NumPy and Pandas integration
   - Matplotlib visualization with NumPy/Pandas data
   - SciPy numerical functions with NumPy arrays
   - CoinMetrics API client functionality
   - Code quality tools like pytest, bandit, safety, and pylint
   - System monitoring with psutil

To run the requirements compatibility tests:

```bash
pytest tests/test_requirements_compatibility.py -v
```

### Version Constraints Tests

The `test_version_constraints.py` file contains tests that:

1. Verify that installed package versions satisfy constraints in `requirements.txt`
2. Test compatibility between specific version ranges:
   - Pandas 2.0+ with NumPy 2.0+
   - Latest matplotlib with Pandas/NumPy
   - Latest SciPy with NumPy

To run the version constraints tests:

```bash
pytest tests/test_version_constraints.py -v
```

These tests are especially important when upgrading dependencies to ensure that newer versions continue to work correctly with the codebase.

## Security Checks

The framework implements comprehensive security checks to ensure that submitted strategies do not contain potentially harmful code. Your strategy must pass all security checks to be considered valid.

### Security Testing

Security tests verify that your strategy:

1. **Respects Resource Limits**: Doesn't exceed memory or CPU usage thresholds
2. **Uses Allowed Modules Only**: Imports only from the approved list of modules
3. **Avoids Dangerous Patterns**: Doesn't use prohibited functions or code patterns
4. **Handles External Data Safely**: Validates external data sources and uses them securely
5. **Maintains Reasonable Complexity**: Doesn't have excessively complex code structure
6. **Passes Bandit Analysis**: No high or medium severity security issues detected by Bandit

### Security Blocking Rules

The framework will block execution of strategies that:

- Exceed memory or CPU limits
- Use prohibited modules or imports
- Contain dangerous code patterns (e.g., `eval`, `exec`, shell commands)
- Have high severity security issues detected by Bandit
- Have medium severity security issues detected by Bandit
- Use banned functions or methods

Low severity issues will generate warnings but will not block execution.

### Test Mode Detection

The security system automatically detects when it's running in a test environment by checking for 'pytest' or 'unittest' in the loaded modules. In test mode:

- Resource limits are relaxed
- Certain DataFrame operations are allowed that would be blocked in production
- Security tests may adjust requirements based on specific test context
- Memory leak and high CPU warnings are issued instead of blocking errors

### Security Limits

The framework enforces the following resource limits:

| Resource              | Production Limit | Test Mode Limit               |
| --------------------- | ---------------- | ----------------------------- |
| Memory                | 512 MB           | 512 MB                        |
| CPU Time              | 10 seconds       | 30 seconds                    |
| Execution Time        | 30 seconds       | 60 seconds                    |
| Module Complexity     | 500 lines        | 500 lines                     |
| Function Complexity   | 120 statements   | 120 statements (warning only) |
| Cyclomatic Complexity | 25               | 25 (warning only)             |
| Nested Depth          | 6 levels         | 6 levels (warning only)       |

### Allowed Modules

Your strategy may only import from these modules:

- `pandas`, `numpy`, `matplotlib`, `scipy` (data science libraries)
- `coinmetrics` / `coinmetrics_api_client` (for data access)
- `datetime`, `time` (time handling)
- `typing` (type annotations)
- `core.config`, `core.strategies`, `core.strategies.base_strategy` (framework modules)
- `submit_strategies` (your strategy modules)

Limited access to the `os` module is permitted, but only for specific path operations.

### DataFrame Operations in Test Mode

The following DataFrame operations are allowed specifically in test mode but blocked in production:

- `to_csv` - Exporting to CSV files
- `to_datetime` - Converting to datetime format
- `to_numpy` - Converting to NumPy arrays
- `to_dict` - Converting to dictionaries
- `to_records` - Converting to records
- `to_series` - Converting to Series objects

All other DataFrame write operations remain blocked even in test mode.

### External Data Security

When using external data, your strategy must:

1. Use only approved data sources (see below)
2. Validate URL parameters and inputs
3. Handle external data failures gracefully
4. Avoid using external data in dangerous operations (e.g., eval())

#### Approved External Data Sources

- CoinMetrics API: `api.coinmetrics.io`
- Yahoo Finance: `query1.finance.yahoo.com`, `finance.yahoo.com`
- CoinGecko: `api.coingecko.com`
- Nasdaq Data: `data.nasdaq.com`

For more detailed information on security requirements, see `core/SECURITY.md`.

### Testing Strategies with External Data Sources

If your strategy uses external data sources, the tests will verify:

1. That your strategy can retrieve the external data successfully
2. That it handles API failures or connection issues gracefully
3. That the final output conforms to the required format
4. That the strategy completes within a reasonable time frame
5. That external data is accessed in a secure manner

To ensure your strategy with external data passes the tests:

1. Include all necessary API code and keys in your strategy file
2. Add error handling for API calls and provide fallback behavior
3. Consider adding a caching mechanism to avoid repeated API calls during testing
4. Make sure your API usage respects rate limits to avoid test failures
5. Only use approved data sources and validate URLs before use

Example of a robust external data retrieval function:

```python
def get_external_data(start_date, end_date):
    """
    Retrieves external data with proper error handling.

    Args:
        start_date: Start date for data retrieval
        end_date: End date for data retrieval

    Returns:
        DataFrame with external data or None if retrieval failed
    """
    # Create a cache directory if it doesn't exist
    cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
    os.makedirs(cache_dir, exist_ok=True)

    # Create a cache file path
    cache_file = os.path.join(cache_dir, f'external_data_{start_date}_{end_date}.csv')

    # Check if cache exists
    if os.path.exists(cache_file):
        try:
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        except Exception:
            # If cache is corrupted, proceed to fetch data
            pass

    # Try to fetch the data
    try:
        # Your API call logic here
        import pandas_datareader as pdr
        data = pdr.get_data_yahoo('GLD', start_date, end_date)

        # Save to cache
        data.to_csv(cache_file)

        return data
    except Exception as e:
        print(f"Warning: Could not retrieve external data: {e}")
        return None
```

### External Data Restriction

External data sources are not allowed in strategies. Strategies can only use the provided Bitcoin price data. Any attempts to access external APIs or data sources will result in immediate rejection of your strategy.

### Passing Tournament Requirements

For your strategy to qualify for the tournament, it must:

- Be located in the `submit_strategies` directory
- Use the `@register_strategy` decorator with a unique name
- Have non-negative weights
- Handle the backtest date range properly
- Not modify the input data in harmful ways
- Handle external data retrieval properly, if applicable
- Execute efficiently (complete within reasonable time)
- Pass all security validation checks

## Troubleshooting Your Tournament Submission

### Strategy Not Found

If your strategy isn't being discovered:

- Ensure your file is in the `submit_strategies` directory
- Verify your strategy name is unique and valid
- Make sure your strategy function returns the result of `YourClass.get_strategy_function()(df)`

### Execution Failures

If your strategy fails during execution:

- Check for errors in handling NaN or missing values in the data
- Ensure all features are calculated before being used
- Verify your date ranges match those in `core/config.py`
- Make sure you're not modifying the input DataFrame (use `.copy()`)
- For external data, add robust error handling for API calls

### Security Violations

- Note that test mode allows certain operations that would be blocked in production

### API and External Data Issues

If your strategy fails due to external data problems:

- Include fallback behavior when external data can't be retrieved
- Implement caching to avoid network failures during testing
- Add timeouts for API calls to prevent tests from hanging
- Consider mocking the API responses for more reliable testing
- Only use approved data sources (see the Security Checks section)
- Add URL validation to prevent security issues

### Weight Generation Issues

If your weights are causing problems:

- Ensure weights are non-negative
- Check that weights are normalized within each cycle
- Make sure your Series has the correct datetime indices
- Verify your weights are not all zeros or contain extreme values

### Performance Issues

If your strategy runs but performs poorly:

- Consider using vectorized operations instead of loops
- Avoid unnecessarily complex calculations
- Make sure your strategy logic is sound
- Verify your normalization logic works as expected
- Cache external data to avoid repeated API calls

## Running All Tests

To run the complete test suite:

```bash
pytest
```

To run specific categories of tests:

```bash
# Tournament submission tests
pytest tests/test_submit_strategies.py tests/test_strategy_file.py

# Security tests
pytest tests/test_security.py tests/test_bandit_security.py

# Requirements and version compatibility tests
pytest tests/test_requirements_compatibility.py tests/test_version_constraints.py

# Tutorial and example strategy tests
pytest tests/test_example_strategy.py tests/test_tutorial_commands.py
```

## Detailed Test Structure

The `test_submit_strategies.py` file contains two main test classes:

1. **`TestSubmitStrategies`**: Tests existing strategies in the `submit_strategies` directory

   - `test_submit_strategies_loaded`: Verifies strategies are properly loaded
   - `test_submit_strategies_execution`: Tests strategy execution
   - `test_submit_strategies_backtest`: Tests backtest compatibility
   - `test_submit_strategies_comparison`: Compares strategies against baseline
   - `test_results_output`: Verifies results output generation

2. **`TestDynamicSubmitStrategies`**: Tests creating and running strategies dynamically
   - Creates a temporary strategy file
   - Tests loading, execution, and backtesting

The `test_tutorial_commands.py` file contains the `TestTutorialCommandsExecution` class with tests for:

1. Set up with non-interactive matplotlib configuration
2. Command execution utilities with environment control
3. Tests for each major command-line flag and option
4. Tests for processing directories, glob patterns, and file lists
5. Handling of plot outputs with special environment variables

The `test_example_strategy.py` file contains the `TestExampleStrategy` class with tests for:

1. Core functionality of the example DynamicDCA10MAStrategy class
2. Feature construction with moving averages
3. Weight computation and cycle-based normalization
4. Strategy registration and proper function return values

## Generating Test Reports

If you want to generate a detailed report of your test results:

```bash
pytest tests/test_submit_strategies.py -v --html=report.html
```

This requires the pytest-html plugin:

```bash
pip install pytest-html
```

## Fixing Common Test Failures

### Strategy Not Recognized

If your strategy isn't recognized by the system:

```python
# Make sure your decorator is correct
@register_strategy("your_strategy_name")  # Use a unique name
def your_strategy_name(df):
    """Brief description of your tournament strategy"""
    return YourStrategyClass.get_strategy_function()(df)
```

### Invalid Weights

If your weights are invalid:

```python
# Ensure weights are normalized per cycle
start_year = pd.to_datetime(BACKTEST_START).year
cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)

for cycle, group in weights.groupby(cycle_labels):
    cycle_sum = group.sum()
    if cycle_sum > 0:
        weights.loc[group.index] = weights.loc[group.index] / cycle_sum
```

### Index Mismatch

If you have index mismatches:

```python
# Ensure you're using the correct date range
df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
weights = pd.Series(index=df_backtest.index, data=0.0)
# Fill in weights...
```
