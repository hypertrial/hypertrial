# Hypertrial: Stacking Sats Challenge - Submission Guide

This directory is where you'll submit your strategy for the Stacking Sats Challenge. Follow these instructions carefully to ensure your strategy qualifies for evaluation.

## Getting Started

Before submitting your strategy, follow these steps:

1. **Install the Package**: You can install hypertrial from PyPI:

   ```bash
   pip install hypertrial
   ```

   Alternatively, you can install from source:

   ```bash
   git clone https://github.com/mattfaltyn/hypertrial.git
   cd hypertrial
   pip install -e .
   ```

2. **Start with Tutorial 1**: Review [`tutorials/1. Intro.ipynb`](../tutorials/1.%20Intro.ipynb) to understand the basics
3. **Learn the Challenge**: Read through [`tutorials/2. Challenge Overview.ipynb`](../tutorials/2.%20Challenge%20Overview.ipynb) to understand the competition
4. **Create Your Strategy**: Follow [`tutorials/3. Submission_Template.ipynb`](../tutorials/3.%20Submission_Template.ipynb) to develop and test your strategy
5. **Submit Your Strategy**: Follow the submission instructions below

## Submission Process

### Step 1: Create Your Strategy File

After completing the tutorials, especially Tutorial 3:

```bash
cp strategy_template.py your_name_strategy.py
```

Use a descriptive filename that includes your name or unique identifier to avoid conflicts with other participants.

### Step 2: Implement Your Tournament Strategy

Open your new file and:

1. Rename the class to something descriptive (e.g., `YourNameStrategy`)
2. Add a detailed docstring explaining your strategy logic and approach
3. Implement the `construct_features` and `compute_weights` methods
4. Register your strategy by uncommenting and editing the decorator at the bottom

### Step 3: Verify Your Tournament Entry

Run specific tests designed to validate tournament submissions:

```bash
pytest tests/test_submit_strategies.py -v
```

All tests must pass for your strategy to be considered a valid tournament entry.

### Step 4: Evaluate Your Strategy's Performance

Run a backtest to see how your strategy ranks:

```bash
python -m core.main --strategy your_strategy_name
```

Compare against baseline strategies:

```bash
python -m core.main --backtest-all --output-dir results
```

### Step 5: Submit Your Tournament Entry

1. Fork the repository on GitHub
2. Add ONLY your strategy file to the `submit_strategies` directory
3. Submit a pull request with a clear title including your name and strategy
4. Include a brief description of your strategy approach in the PR description

## Tournament Strategy Requirements

### Required Methods

Your tournament strategy class must implement:

1. **`construct_features(df)`**: Add indicators or signals for your strategy

   - Input: Price dataframe with 'btc_close' column
   - Output: Enhanced dataframe with features your strategy needs
   - Must not modify the input dataframe (use `df.copy()`)

2. **`compute_weights(df)`**: Determine investment weight for each day
   - Input: Dataframe with features from `construct_features`
   - Output: Series of weights indexed by date (must be positive values)
   - Weights should be normalized to sum to 1.0 within each 4-year cycle

### Tournament Registration

Register your tournament entry with a unique name using the decorator:

```python
@register_strategy("your_name_strategy")
def your_name_strategy(df):
    """Brief description of your tournament strategy"""
    return YourNameStrategy.get_strategy_function()(df)
```

## External Data Access

**IMPORTANT:** External data sources are NOT allowed for tournament submissions. Strategies must only use the provided Bitcoin price data that is passed to the strategy function. Any attempts to access external APIs or data sources will result in immediate rejection of your strategy.

The following information about external data access is retained for educational purposes only and does not apply to tournament submissions:

~~Strategies are allowed to access external data only through `pandas_datareader`. Direct network requests using libraries like `requests` or `urllib` are strictly prohibited for security reasons.~~

### Prohibited Network Access Methods

The following methods of network access are strictly forbidden:

1. **Direct HTTP requests**

   - requests library (`import requests`)
   - urllib module (`import urllib`)
   - http.client (`import http`)
   - socket module (`import socket`)

2. **Custom network implementations**

   - Creating custom socket connections
   - Using any third-party HTTP clients not listed in allowed modules

3. **Data access libraries**
   - pandas_datareader
   - Any other libraries that access external data

Attempts to use these libraries will result in immediate rejection of your strategy.

## External Data Sources

~~You may use external data sources in your strategy, but:~~

**IMPORTANT:** External data sources are NOT allowed for tournament submissions. Your strategy must only use the Bitcoin price data provided in the input dataframe parameter. The security system will immediately reject any strategy that attempts to access external data.

For educational purposes only, here is an example of how a strategy might be structured if external data were allowed (which it is not for this tournament):

```python
class ExampleStrategy(StrategyTemplate):
    """
    Example strategy that only uses the provided BTC price data.

    The strategy calculates a simple moving average and allocates more
    weight when the price is below this average.
    """
```

## Tournament Strategy Example

Here's a minimal example of a valid tournament entry:

```python
# submit_strategies/example_tournament_strategy.py
import pandas as pd
import numpy as np
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class ExampleTournamentStrategy(StrategyTemplate):
    """
    Tournament strategy that allocates more weight to days when price is below the 50-day MA.

    Strategy approach:
    1. Calculate the 50-day moving average of Bitcoin price
    2. Identify days when price is below this average
    3. Allocate more weight on those days (2x)
    4. Allocate less weight when price is above MA (0.5x)
    5. Normalize weights within each 4-year market cycle
    """

    @staticmethod
    def construct_features(df):
        df = df.copy()  # Important: don't modify the input dataframe
        # Calculate 50-day moving average
        df['ma_50'] = df['btc_close'].rolling(window=50).mean()
        df['below_ma'] = (df['btc_close'] < df['ma_50']).astype(int)
        return df

    @staticmethod
    def compute_weights(df):
        df_backtest = df.loc[BACKTEST_START:BACKTEST_END]

        # Allocate more weight when price is below MA
        weights = pd.Series(index=df_backtest.index, data=0.0)
        weights[df_backtest['below_ma'] == 1] = 2.0  # Double weight when below MA
        weights[df_backtest['below_ma'] == 0] = 0.5  # Half weight when above MA

        # Normalize weights within each 4-year cycle (REQUIRED)
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)

        for cycle, group in weights.groupby(cycle_labels):
            # Normalize to sum to 1.0
            cycle_sum = group.sum()
            if cycle_sum > 0:
                weights.loc[group.index] = weights.loc[group.index] / cycle_sum

        return weights

# Register the tournament entry
@register_strategy("example_tournament_strategy")
def example_tournament_strategy(df):
    """Tournament strategy allocating more weight when price is below the 50-day MA."""
    return ExampleTournamentStrategy.get_strategy_function()(df)
```

## Tournament Strategy Design Tips

### Weight Normalization (Required)

All weights must be properly normalized within 4-year market cycles:

```python
# Normalize weights within each cycle - THIS IS REQUIRED
start_year = pd.to_datetime(BACKTEST_START).year
cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)

for cycle, group in weights.groupby(cycle_labels):
    cycle_sum = group.sum()
    if cycle_sum > 0:
        weights.loc[group.index] = weights.loc[group.index] / cycle_sum
```

### Performance Optimization Tips

For better tournament performance:

- Use vectorized operations (pandas/numpy) instead of loops
- Avoid iterating over rows when possible
- Pre-calculate values that are used multiple times

### Strategy Ideas for the Tournament

Consider these approaches for your tournament strategy:

- Moving average crossovers
- Relative Strength Index (RSI) thresholds
- Bollinger Band breakouts
- Volume-based indicators
- Drawdown-based allocation
- Volatility-adjusted weighting
- Seasonality patterns

## Tournament Rules

1. Your strategy must be self-contained in a single Python file
2. Your strategy must follow the structure defined in `strategy_template.py`
3. **External data sources are not allowed** (strategies can only use the provided BTC price data)
4. Your strategy must complete execution in a reasonable time
5. You must not modify or depend on changes to the core framework
6. All entries must pass the validation checks to qualify:
   - Strictly positive weights
   - Weights above minimum threshold
   - Weights sum to 1.0 per cycle
   - SPD performance >= uniform DCA

> **Note**: The forward-looking check (which previously verified that strategies don't use future data) has been removed from the validation process.

7. Only one strategy submission per participant
8. Your strategy must not have any high or medium severity security issues

## Security Requirements

The tournament framework enforces strict security checks to ensure all submissions are safe. Strategies with any high or medium severity security issues will be automatically blocked from execution.

## Security Restrictions

To maintain a secure and fair environment, the following restrictions apply to all strategies:

### Test vs. Production Environment

The system detects when it's running in test mode vs. production mode:

- During testing (`pytest`), certain restrictions are relaxed to facilitate development
- In production (tournament evaluation), stricter security measures are applied
- Test mode provides more generous resource limits (execution time, CPU time)
- Certain DataFrame operations are allowed in test mode only

### Filesystem Restrictions

- **No file writing operations** - Strategies cannot write to the filesystem
- **No file reading operations** except through pandas functions
- **No temporary file operations** - The `tempfile` module is blocked
- **Limited OS operations** - Only `os.path.join` and `os.path.exists` are allowed

### Network Restrictions

- **No external data access** - No external APIs or data sources are allowed. Strategies can only use the provided Bitcoin price data
- **No direct HTTP requests** - The `requests` library is blocked
- **No socket operations** - The `socket` module is blocked
- **No pandas_datareader** - The pandas_datareader package is blocked as it provides external data access

### Pandas Operations

- **DataFrame output methods** - The following methods are blocked in production but allowed in test mode:

  - `to_csv()`
  - `to_datetime()`
  - `to_numpy()`
  - `to_dict()`
  - `to_records()`
  - `to_series()`

- **Always blocked methods** - These methods are blocked even in test mode:

  - `to_pickle()`
  - `to_json()`
  - `to_excel()`
  - `to_feather()`
  - Any other `to_*()` methods not explicitly allowed

- **Allowed pandas_datareader functions** - Only these functions are permitted:
  - `DataReader`
  - `get_data_yahoo`
  - `get_data_fred`
  - `get_data_stooq`
  - `get_data_alpha_vantage`
  - `get_data_naver`
  - `get_nasdaq_symbols`
  - `get_iex_symbols`
  - `get_tiingo_symbols`

### Serialization Restrictions

- **No serialization** - The following operations are blocked:
  - `pickle.dump` / `pickle.dumps`
  - `json.dump` / `json.dumps` (when writing to files)
  - `marshal.dump` / `marshal.dumps`
  - `shelve.open`

### Code Generation Restrictions

- **No code generation or evaluation** - These operations are blocked:
  - `eval()` / `exec()`
  - `ast.parse` / `ast.unparse`
  - `compile()`
  - `importlib` functions

### System Operations

- **No system access** - The following are blocked:
  - `subprocess` module and all subprocesses
  - `os.system()` and similar commands
  - `sys` module access

### Resource Limits

The framework enforces these resource limits:

| Resource       | Production Limit | Test Mode Limit |
| -------------- | ---------------- | --------------- |
| Memory         | 512 MB           | 512 MB          |
| CPU Time       | 10 seconds       | 30 seconds      |
| Execution Time | 30 seconds       | 60 seconds      |

These restrictions ensure that strategies operate in a fair, secure, and deterministic environment. Any attempt to circumvent these restrictions will result in immediate rejection of your strategy.

## Tournament Judging Criteria

Strategies will be evaluated based on:

1. **SPD Performance**: Mean excess SPD percentile compared to uniform DCA
2. **Consistency**: Performance across different market cycles
3. **Originality**: Uniqueness of approach compared to other entries
4. **Code Quality**: Clear, well-documented, and efficient implementation

## Common Tournament Submission Issues

### Strategy Not Found

- Make sure your file is in the `submit_strategies` directory
- Check that your function is properly decorated with `@register_strategy`
- Verify your function name matches the string in the decorator

### Runtime Errors

- Always handle NaN values after rolling calculations
- Check for division by zero in your calculations
- Make sure all features are calculated before being used
- Add error handling for external API calls

### Weight Issues

- Ensure all weights are non-negative
- Make sure to handle the case where all weights in a cycle are zero
- Verify your normalization gives reasonable weight distributions

## Tournament Schedule

1. **Submission Deadline**: [Date]
2. **Initial Evaluation**: [Date]
3. **Final Results Announcement**: [Date]

## Questions and Support

If you have questions about the tournament or need help troubleshooting your strategy, please:

1. Check the documentation in this repository
   - `README.md`: For general tournament information
   - `core/SECURITY.md`: For detailed security requirements
   - `tests/TESTS.md`: For testing procedures and requirements
2. Review the example strategies in the `tutorials` directory
3. **External Data Restriction**: For questions about the external data prohibition, refer to the prominent warnings in all documentation files
4. Submit issues on GitHub: https://github.com/mattfaltyn/hypertrial/issues

### Common Security Issues

The following issues frequently cause strategies to be rejected:

1. **Code Execution**

   - Using `eval()` or `exec()` to execute dynamic code
   - Using `os.system()` or subprocess functions
   - Implementing custom imports or code loaders

2. **Credential Handling**

   - Hardcoded API keys or passwords
   - Saving credentials to disk insecurely
   - Logging sensitive information

3. **Unsafe Deserialization**

   - Using `yaml.load()` without `Loader=yaml.SafeLoader`
   - Unpickling data from untrusted sources
   - Using `eval()` to parse JSON or other data formats

4. **Poor Exception Handling**

   - Empty `try-except` blocks that hide errors
   - Catching all exceptions without specific handling
   - Suppressing security-relevant errors

When your strategy is rejected due to security issues, check the error message which will contain:

- The security issue type (e.g., "B102: exec used")
- The exact line number where the issue was found
- A description of why this is considered a security concern
