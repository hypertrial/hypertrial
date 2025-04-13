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

- `strategies/test_submit_strategies.py`: Tests strategies submitted to the `submit_strategies` directory
- `strategies/test_strategy_file.py`: Tests loading and executing standalone strategy files
- `strategies/test_strategy_files.py`: Tests batch loading of multiple strategy files
- `strategies/test_strategies_utils.py`: Tests utility functions for strategy handling and manipulation
- `strategies/test_strategy_loader.py`: Tests dynamic loading of strategy files with timeout handling
- `strategies/test_strategy_processor.py`: Tests strategy processing with validation and backtest integration

### Tutorial and Example Strategy Tests

- `cli/test_tutorial_commands.py`: Tests all CLI commands against files in the tutorials directory
- `strategies/test_example_strategy.py`: Tests the functionality of the example strategy in the tutorials directory

### Security Tests

- `security/test_security.py`: Main security tests for strategy validation and sandboxing
- `security/test_bandit_security.py`: Tests for Bandit security analysis on submitted strategies
- `security/test_security_module.py`: Tests for the security module components and functionality
- `security/test_ast_operations.py`: Tests for the abstract syntax tree (AST) parsing and analysis operations
- `security/test_backward_compatibility.py`: Tests for ensuring backward compatibility with previous security measures
- `security/test_data_flow.py`: Tests for data flow validation and protection against data leakage
- `security/test_data_flow_more_coverage.py`: Additional tests for data flow security features
- `security/test_import_hook.py`: Tests for the custom import hook used for security sandboxing
- `security/test_resource_monitor.py`: Tests for the resource monitoring and limitation components
- `security/test_strategy_security.py`: Tests for specific security checks on strategy files
- `security/test_validate_external_data.py`: Tests for validating and securing external data sources

### Data Tests

- `data/test_data_basic.py`: Tests for basic data loading and validation
- `data/test_data_download.py`: Tests for data downloading functionality
- `data/test_data_download_integration.py`: Tests data integration with real-world sources
- `data/test_data_init.py`: Tests for data module initialization and setup
- `data/test_extract_data_more_coverage.py`: Additional tests for data extraction and processing
- `core_modules/data/test_data_formats.py`: Tests data format validation and conversion
- `core_modules/data/test_data_validation.py`: Tests data validation rules and constraints

### Package Tests

- `package/test_installation.py`: Tests for proper package installation
- `package/test_setup.py`: Tests for proper package setup
- `package/test_package_deployment.py`: Tests for package deployment
- `package/test_installed_package.py`: Tests for installed package functionality
- `package/test_dist_files.py`: Tests for distribution files

### Core Module Coverage Tests

The following tests ensure comprehensive coverage of core functionality:

- `core_modules/test_file_utils.py`: Tests file utility functions for strategy discovery and path management
- `core_modules/test_plots.py`: Tests visualization functions with a non-interactive Matplotlib backend
- `core_modules/test_config.py`: Tests configuration constants and their constraints
- `batch/test_batch.py`: Tests batch processing of strategies and parallel execution
- `batch/test_batch_advanced.py`: Tests advanced batch processing capabilities and edge cases
- `batch/test_batch_more_coverage.py`: Tests additional batch processing scenarios and edge cases
- `core_modules/error/test_error_handling.py`: Tests error handling and graceful failure modes

### Strategy Tests

- `strategies/core/test_strategy_registration.py`: Tests strategy registration system
- `strategies/core/test_dynamic_strategy.py`: Tests dynamic strategy generation
- `strategies/core/test_uniform_strategy.py`: Tests uniform strategy allocation
- `performance/test_strategy_performance.py`: Tests strategy performance metrics and calculations

### Requirements and Version Tests

- `requirements/test_requirements_compatibility.py`: Tests compatibility between packages in requirements.txt
- `requirements/test_version_constraints.py`: Tests version constraints in requirements.txt
- `requirements/test_validation_default.py`: Tests default validation configurations
- `spd/test_spd_checks.py`: Tests software package data integrity checks
- `spd/core/test_spd_calculation.py`: Tests SPD calculation algorithms
- `spd/core/test_spd_integration.py`: Tests SPD integration with other system components
- `spd/core/test_spd_advanced.py`: Tests advanced SPD features and edge cases
- `performance/test_performance_benchmarks.py`: Tests strategy performance benchmarks

### CLI Tests

- `cli/test_cli.py`: Tests command-line interface functionality
- `cli/test_tutorial_commands.py`: Tests tutorial command execution

### Integration Tests

The `integration/` directory is prepared for integration tests that verify different components working together. Currently, this directory is empty and reserved for future end-to-end tests.

## Tournament Test Focus

As a tournament participant, you should focus on the `test_submit_strategies.py` file, which specifically tests strategies submitted to the `submit_strategies` directory.

## Verifying Your Tournament Submission

Your submitted strategy must pass all tests in `test_submit_strategies.py` to be considered valid for the tournament. These tests ensure your strategy follows the required format and can be executed successfully within the tournament framework.

### Running the Tournament Verification Tests

To verify your tournament submission:

```bash
pytest tests/strategies/test_submit_strategies.py -v
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
pytest tests/strategies/test_example_strategy.py -v

# Test CLI commands with the tutorials directory
pytest tests/cli/test_tutorial_commands.py -v
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
7. **Strategy Validation**: Your strategy passes all validation criteria:
   - Contains only positive weights
   - All weights are above the minimum threshold
   - Weights sum to 1.0 within each cycle
   - SPD performance is better than or equal to uniform DCA

> **Note**: The forward-looking check (which previously verified that strategies don't use future data) has been removed from the validation process.

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
pytest tests/requirements/test_requirements_compatibility.py -v
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
pytest tests/requirements/test_version_constraints.py -v
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

**IMPORTANT:** External data sources are strictly prohibited in the tournament. The information below about external data validation is retained for educational purposes only and does not apply to tournament submissions.

For more detailed information on security requirements, see `core/SECURITY.md`.

### Testing Strategies with External Data Sources

~~If your strategy uses external data sources, the tests will verify:~~

~~1. That your strategy can retrieve the external data successfully~~
~~2. That it handles API failures or connection issues gracefully~~
~~3. That the final output conforms to the required format~~
~~4. That the strategy completes within a reasonable time frame~~
~~5. That external data is accessed in a secure manner~~

~~To ensure your strategy with external data passes the tests:~~

~~1. Include all necessary API code and keys in your strategy file~~
~~2. Add error handling for API calls and provide fallback behavior~~
~~3. Consider adding a caching mechanism to avoid repeated API calls during testing~~
~~4. Make sure your API usage respects rate limits to avoid test failures~~
~~5. Only use approved data sources and validate URLs before use~~

~~Example of a robust external data retrieval function:~~

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

**IMPORTANT:** External data sources are not allowed in strategies. Strategies can only use the provided Bitcoin price data. Any attempts to access external APIs or data sources will result in immediate rejection of your strategy.

The security system enforces this restriction by:

1. Blocking imports of data access libraries (pandas_datareader, requests, urllib, etc.)
2. Preventing network connections
3. Monitoring for attempts to access external resources
4. Analyzing data flow for patterns that might indicate external data usage

### Passing Tournament Requirements

For your strategy to qualify for the tournament, it must:

- Be located in the `submit_strategies` directory
- Use the `@register_strategy` decorator with a unique name
- Have non-negative weights
- Handle the backtest date range properly
- Not modify the input data in harmful ways
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

### Security Violations

- Note that test mode allows certain operations that would be blocked in production

### API and External Data Issues

~~If your strategy fails due to external data problems:~~

~~- Include fallback behavior when external data can't be retrieved~~
~~- Implement caching to avoid network failures during testing~~
~~- Add timeouts for API calls to prevent tests from hanging~~
~~- Consider mocking the API responses for more reliable testing~~
~~- Only use approved data sources (see the Security Checks section)~~
~~- Add URL validation to prevent security issues~~

**IMPORTANT:** Remember that external data sources are not allowed in tournament submissions. This section is retained for educational purposes only.

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
pytest tests/strategies/test_submit_strategies.py tests/strategies/test_strategy_file.py tests/strategies/test_strategy_files.py tests/strategies/test_strategies_utils.py

# Security tests
pytest tests/security/

# Requirements and version compatibility tests
pytest tests/requirements/

# Tutorial and example strategy tests
pytest tests/strategies/test_example_strategy.py tests/cli/test_tutorial_commands.py

# Core module tests
pytest tests/core_modules/

# Strategy module tests
pytest tests/strategies/core/

# Data validation and format tests
pytest tests/data/ tests/core_modules/data/

# SPD (Software Package Data) tests
pytest tests/spd/

# Batch processing tests
pytest tests/batch/

# Package installation and deployment tests
pytest tests/package/

# File utilities and configuration tests
pytest tests/core_modules/test_file_utils.py tests/core_modules/test_config.py

# Strategy processing and loading tests
pytest tests/strategies/test_strategy_processor.py tests/strategies/test_strategy_loader.py

# Performance tests
pytest tests/performance/
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
pytest tests/strategies/test_submit_strategies.py -v --html=report.html
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

## Test Coverage Goals

The test suite aims to provide comprehensive coverage of all core functionality to ensure:

1. **Robustness**: Every core module is tested for expected behavior and error handling
2. **Edge Cases**: Unusual inputs and error conditions are tested systematically
3. **Integration**: Modules work correctly together when combined
4. **Security**: Security validation functions perform as expected
5. **Configuration**: System constants are properly defined and constrained

The new test files provide dedicated coverage for previously under-tested components:

- `test_file_utils.py` tests the strategy file discovery and filtering system
- `test_plots.py` verifies visualization functions work correctly using a non-interactive backend
- `test_config.py` ensures configuration constants are properly defined
- `test_batch.py` tests the parallel processing and batching capabilities
- `test_strategy_processor.py` tests the strategy execution pipeline
- `test_strategy_loader.py` tests dynamic module loading with timeout protection

## Running Tests with Coverage

To run tests with coverage reporting:

```bash
# Install pytest-cov
pip install pytest-cov

# Run tests with coverage for core modules
pytest tests/ --cov=core --cov-report=term-missing
```

This will show which lines in the core modules are covered by tests and identify any gaps in coverage.

## Test Directory Organization

The test suite is organized into the following directory structure:

- `tests/`: Root directory containing main configuration and common fixtures
  - `security/`: Security-related tests
    - `test_security.py`: Main security tests
    - `test_bandit_security.py`: Bandit security analysis tests
    - `test_security_module.py`: Security module component tests
    - `test_ast_operations.py`: AST operations tests
    - `test_backward_compatibility.py`: Security backward compatibility tests
    - `test_data_flow.py`: Data flow validation tests
    - `test_data_flow_more_coverage.py`: Extended data flow security tests
    - `test_import_hook.py`: Import hook security tests
    - `test_resource_monitor.py`: Resource monitoring tests
    - `test_strategy_security.py`: Strategy security tests
    - `test_validate_external_data.py`: External data validation tests
  - `strategies/`: Strategy-related tests
    - `test_strategy_file.py`: Standalone strategy file tests
    - `test_strategy_files.py`: Multiple strategy files loading tests
    - `test_strategies_utils.py`: Strategy utility function tests
    - `test_strategy_loader.py`: Dynamic strategy loading tests
    - `test_strategy_processor.py`: Strategy processing tests
    - `test_submit_strategies.py`: Submission tests
    - `test_example_strategy.py`: Example strategy tests
    - `core/`: Core strategy implementation tests
      - `test_strategy_registration.py`: Strategy registration tests
      - `test_dynamic_strategy.py`: Dynamic strategy tests
      - `test_uniform_strategy.py`: Uniform strategy tests
  - `batch/`: Batch processing tests
    - `test_batch.py`: Basic batch processing tests
    - `test_batch_advanced.py`: Advanced batch processing tests
    - `test_batch_more_coverage.py`: Additional batch processing coverage tests
  - `data/`: Data handling tests
    - `test_data_basic.py`: Basic data loading tests
    - `test_data_download.py`: Data downloading tests
    - `test_data_download_integration.py`: Data integration tests
    - `test_data_init.py`: Data initialization tests
    - `test_extract_data_more_coverage.py`: Extended data extraction tests
  - `package/`: Package management tests
    - `test_installation.py`: Installation tests
    - `test_setup.py`: Setup tests
    - `test_package_deployment.py`: Deployment tests
    - `test_installed_package.py`: Installed package tests
    - `test_dist_files.py`: Distribution files tests
  - `cli/`: Command-line interface tests
    - `test_cli.py`: CLI functionality tests
    - `test_tutorial_commands.py`: Tutorial command tests
  - `spd/`: Software Package Data tests
    - `test_spd_checks.py`: SPD integrity checks
    - `core/`: Core SPD implementation tests
      - `test_spd_advanced.py`: Advanced SPD features tests
      - `test_spd_integration.py`: SPD integration tests
      - `test_spd_calculation.py`: SPD calculation tests
  - `requirements/`: Requirements and version tests
    - `test_requirements_compatibility.py`: Package compatibility tests
    - `test_version_constraints.py`: Version constraint tests
    - `test_validation_default.py`: Default validation tests
  - `core_modules/`: Core module tests
    - `test_config.py`: Configuration tests
    - `test_file_utils.py`: File utility tests
    - `test_plots.py`: Visualization tests
    - `data/`: Core data module tests
      - `test_data_formats.py`: Data format tests
      - `test_data_validation.py`: Data validation tests
    - `error/`: Error handling tests
      - `test_error_handling.py`: Error handling tests
  - `performance/`: Performance tests
    - `test_strategy_performance.py`: Strategy performance tests
    - `test_performance_benchmarks.py`: Performance benchmark tests
  - `integration/`: Integration and end-to-end tests
    - Currently empty, reserved for future end-to-end tests

This organization allows for:

1. **Modular Testing**: Each component has dedicated test files focused on its functionality
2. **Hierarchical Structure**: Tests are grouped by module and submodule
3. **Isolation**: Tests can be run separately by category for focused debugging
4. **Maintainability**: New tests can be added to the appropriate directory as the system evolves

When running tests, you can target specific categories by using the directory path:

```bash
# Run all security tests
pytest tests/security/

# Run only strategy performance tests
pytest tests/performance/

# Run all core module tests
pytest tests/core_modules/
```

For development, you can focus on a specific test category when working on a related component of the system.

## SPD Validation Tests

The framework provides comprehensive validation for submitted strategies through the SPD (Sats Per Dollar) checks. These tests ensure that strategies meet all tournament requirements and follow best practices.

### SPD Check Validation Output

The validation system has been enhanced to provide detailed validation results that are included in the output CSV files:

1. **Strategy Validation Results**: Running `backtest_all_strategies` or `backtest_multiple_strategy_files` now includes validation results in the output CSV
2. **Detailed Validation Flags**: The output includes specific flags for each type of validation check:
   - `validation_passed`: Overall pass/fail status
   - `has_negative_weights`: Whether the strategy has any negative weights
   - `has_below_min_weights`: Whether any weights are below the minimum threshold
   - `weights_not_sum_to_one`: Whether weights sum to 1 within each cycle
   - `underperforms_uniform`: Whether the strategy performs worse than uniform DCA

### Testing Validation Output

Three new test categories have been added to verify this functionality:

1. **Detailed Validation Results Test**: `test_check_strategy_submission_ready_with_return_details` in `tests/spd/test_spd_checks.py` tests that the `check_strategy_submission_ready` function correctly returns structured validation results when `return_details=True` is specified.

2. **Backtest Function Integration Test**: `test_backtest_dynamic_dca_with_validation_results` in `tests/spd/test_spd_checks.py` verifies that the `backtest_dynamic_dca` function correctly integrates validation results into its output DataFrame.

3. **CSV Output Validation Test**: `test_backtest_all_strategies_with_validation_results` in `tests/batch/test_batch.py` verifies that the validation results are correctly included in the output CSV files generated by the batch processing system.

To run the specific validation output tests:

```bash
# Test detailed validation results
pytest tests/spd/test_spd_checks.py::test_check_strategy_submission_ready_with_return_details -v

# Test backtest function integration with validation results
pytest tests/spd/test_spd_checks.py::test_backtest_dynamic_dca_with_validation_results -v

# Test CSV output with validation results
pytest tests/batch/test_batch.py::test_backtest_all_strategies_with_validation_results -v
```

These enhancements make it easier to identify and diagnose issues with strategies, providing specific feedback on why a strategy may not meet the tournament requirements.
