# Bitcoin DCA Strategy Tournament - Submission Guide

This directory is where you'll submit your strategy for the Bitcoin DCA Tournament. Follow these instructions carefully to ensure your strategy qualifies for evaluation.

## Tournament Submission Quick Start

1. Copy `strategy_template.py` to a new file with your unique strategy name (e.g., `your_name_strategy.py`)
2. Implement the required methods in your strategy class
3. Register your strategy with a unique name using the `@register_strategy` decorator
4. Verify your strategy passes all tests:
   ```bash
   pytest tests/test_submit_strategies.py -v
   ```
5. Evaluate your strategy's performance:
   ```bash
   python -m core.main --strategy your_strategy_name
   ```

## Tournament Submission Process

### Step 1: Create Your Strategy File

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

## External Data Sources

You may use external data sources in your strategy, but:

1. Your submission must include all code needed to retrieve and process the external data
2. Any required API keys must be included in your submission file
3. Your strategy must handle cases where the external data is unavailable
4. The final output must still follow the `strategy_template.py` structure
5. Your strategy must pass all tests in the test suite
6. Clearly document any external data sources in your strategy's docstring

Example of documenting external data usage:

```python
class ExternalDataStrategy(StrategyTemplate):
    """
    Tournament strategy that uses external gold price data alongside BTC price.

    External data sources:
    - Yahoo Finance API: Gold price data (GLD)

    The strategy compares the BTC/Gold ratio to identify periods of BTC
    undervaluation relative to gold, allocating more weight during these periods.
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
- Include error handling for external API calls
- Consider caching external data to avoid redundant API calls

### Strategy Ideas for the Tournament

Consider these approaches for your tournament strategy:

- Moving average crossovers
- Relative Strength Index (RSI) thresholds
- Bollinger Band breakouts
- Volume-based indicators
- Drawdown-based allocation
- Volatility-adjusted weighting
- Seasonality patterns
- External market correlations (stocks, gold, etc.)
- On-chain metrics (if available via API)

## Tournament Rules

1. Your strategy must be self-contained in a single Python file
2. Your strategy must follow the structure defined in `strategy_template.py`
3. External data sources are allowed, but you must include all API code and keys in your submission
4. Your strategy must complete execution in a reasonable time
5. You must not modify or depend on changes to the core framework
6. All entries must pass the test suite to qualify
7. Only one strategy submission per participant
8. Your strategy must not have any high or medium severity security issues

## Security Requirements

The tournament framework enforces strict security checks to ensure all submissions are safe. Strategies with any high or medium severity security issues will be automatically blocked from execution.

### Security Constraints

- No dangerous functions like `eval()`, `exec()`, or `os.system()`
- No subprocess invocations or shell commands
- No hardcoded credentials or sensitive information
- No unsafe use of cryptographic functions
- No unsafe deserialization (e.g., `yaml.load` without safe mode)
- No dangerous exception handling patterns (e.g., bare try-except blocks)

### Security Verification

Your submission is analyzed using Bandit, a security linter for Python code. To check if your strategy passes security verification:

```bash
pytest tests/test_security.py -v
```

If you receive errors about security issues, you'll need to fix them before your strategy can be accepted. The error messages include details about the specific issues found, including the severity level, issue ID, and line number.

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
2. Review the example strategies
3. Contact the tournament organizers at [contact information]

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

5. **Unsafe External API Calls**
   - Not validating URLs before requests
   - Missing timeout parameters
   - No error handling for API failures

When your strategy is rejected due to security issues, check the error message which will contain:

- The security issue type (e.g., "B102: exec used")
- The exact line number where the issue was found
- A description of why this is considered a security concern
