# Hypertrial Tests

This directory contains tests for the Hypertrial Bitcoin DCA Backtesting Framework.

## Test Structure

The tests are organized according to the module structure of the codebase:

- `conftest.py`: Common test fixtures including sample price data
- `core/strategies/`: Tests for strategy-related functionality
  - `test_strategy_registration.py`: Tests for strategy registration functions
  - `test_uniform_strategy.py`: Tests for the Uniform DCA strategy
  - `test_dynamic_strategy.py`: Tests for the Dynamic DCA strategy
- `core/`: Tests for core modules
  - `test_spd_calculation.py`: Tests for SPD calculation functions
  - `test_spd_integration.py`: Tests for strategy integration with SPD calculations
  - `test_spd_advanced.py`: Tests for advanced SPD functionality and edge cases
  - `test_performance_benchmarks.py`: Tests for backtest performance benchmarking
  - `test_strategy_performance.py`: Tests for measuring strategy implementation performance

### SPD Integration Tests

The `test_spd_integration.py` file contains tests that focus on how different strategy implementations integrate with the SPD calculation module. These tests ensure that strategies with various weight generation logic can work with the SPD calculation pipeline:

- **Strategy Output Format Tests**:

  - Test strategies that return Series weights
  - Test strategies that return weights in other formats
  - Test strategies with partial date coverage

- **Weight Normalization Tests**:

  - Test unnormalized weights (sum ≠ 1.0)
  - Test negative weights and clipping behavior
  - Test weights greater than 1.0
  - Test NaN and missing values handling

- **Performance Metrics Consistency Tests**:
  - Test min/max SPD calculations
  - Test uniform SPD calculation
  - Test dynamic SPD calculation
  - Test percentile calculations
  - Test different weight distributions

### SPD Advanced Tests

The `test_spd_advanced.py` file contains advanced tests that focus on more complex interactions and edge cases:

- **Strategy Substitution Tests**:

  - Test that different strategies yield different SPD results
  - Verify that strategy name is properly propagated to results and plots

- **Error Handling Tests**:

  - Test handling of malformed data returned by strategies
  - Test behavior when strategies raise exceptions

- **Performance Comparison Tests**:
  - Test with strategies that have predictable performance patterns
  - Verify comparative metrics calculations

### Performance Benchmarking Tests

The `test_performance_benchmarks.py` file contains tests that measure the performance characteristics of the backtest process:

- **Execution Time Tests**:

  - Measure execution time for different data sizes
  - Test performance with different strategies
  - Evaluate performance impact of adding data fields

- **Memory Usage Tests**:

  - Measure memory consumption during backtest execution
  - Track peak memory usage with different workloads
  - Test memory scaling with increasing data size

- **Plotting Overhead Tests**:

  - Measure the performance impact of generating plots
  - Compare execution time with and without plotting

- **CPU Profiling Tests**:
  - Profile CPU usage during backtest execution
  - Identify performance bottlenecks

### Strategy Performance Tests

The `test_strategy_performance.py` file contains tests that specifically focus on the performance of different strategy implementations:

- **Strategy Execution Time Comparison**:

  - Measure execution time of strategies with varying complexity
  - Calculate the percentage of backtest time spent on strategy calculation
  - Compare strategies with different computational requirements

- **Strategy Memory Footprint Tests**:

  - Measure memory usage of different strategy implementations
  - Compare memory-efficient vs memory-intensive strategies

- **Vectorized vs Iterative Implementation Tests**:

  - Compare performance between vectorized and iterative implementations
  - Measure speedup factors for different implementation approaches

- **Strategy Caching Benefits Tests**:
  - Measure performance benefits of caching intermediate results
  - Compare execution times with and without caching
  - Evaluate the impact of caching on strategy performance

## Running Tests

To run all tests:

```bash
pytest
```

To run a specific test module:

```bash
pytest tests/core/test_spd_calculation.py
```

To run a specific test function:

```bash
pytest tests/core/test_spd_calculation.py::test_spd_calculation_with_uniform_weights
```

## Test Coverage

To run tests with coverage reporting:

```bash
pip install pytest-cov
pytest --cov=core
```

## Adding New Tests

When adding new tests:

1. Follow the existing structure, putting tests in the directory matching the module being tested
2. Use the `pytest` fixtures from `conftest.py` for common test data
3. Use clear, descriptive test names that indicate what is being tested
4. Include docstrings for each test function explaining what is being tested
