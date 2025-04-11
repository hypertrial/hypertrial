# Hypertrial: Bitcoin DCA Strategy Framework

A Bitcoin Dollar-Cost Averaging (DCA) framework for evaluating and comparing algorithmic trading strategies across multiple market cycles.

## Installation

```bash
pip install hypertrial
```

## Quick Start

```python
import pandas as pd
from hypertrial import backtest_dynamic_dca, load_data, register_strategy

# Load Bitcoin data (included with the package)
btc_df = load_data()

# Create a simple custom strategy
@register_strategy("my_custom_strategy")
def custom_dca_strategy(df):
    """A simple custom strategy that allocates more weight when price is below the 50-day MA."""
    # Add features
    df = df.copy()
    df['ma_50'] = df['btc_close'].rolling(window=50).mean()
    df['below_ma'] = (df['btc_close'] < df['ma_50']).astype(int)

    # Create weights
    weights = pd.Series(index=df.index, data=0.0)
    weights[df['below_ma'] == 1] = 2.0  # Double weight when below MA
    weights[df['below_ma'] == 0] = 0.5  # Half weight when above MA

    # Normalize weights (required)
    total_weight = weights.sum()
    if total_weight > 0:
        weights = weights / total_weight

    return weights

# Run backtest with your strategy
results = backtest_dynamic_dca(btc_df, strategy_name="my_custom_strategy")
```

## Key Features

- **Strategy Development**: Create and test custom DCA strategies with a flexible API
- **Performance Metrics**: Analyze strategies using Sats Per Dollar (SPD) across market cycles
- **Cross-Cycle Analysis**: Test strategies under different market conditions
- **Visualization Tools**: Built-in plotting for strategy weights and performance metrics
- **Security Verification**: Comprehensive security system for submitted strategies
- **Tournament Platform**: Submit and compare your strategies against others

## Command Line Interface

Hypertrial comes with a built-in CLI:

```bash
# List available strategies
hypertrial --list

# Run backtest with a specific strategy
hypertrial --strategy dynamic_dca

# Run backtest for all strategies
hypertrial --backtest-all --output-dir results

# Backtest multiple strategy files from custom paths
hypertrial --strategy-files path/to/strategy1.py path/to/strategy2.py --output-dir results

# Backtest all Python files in a directory
hypertrial --strategy-dir path/to/strategies/dir --output-dir results

# Backtest files matching a glob pattern
hypertrial --glob-pattern "strategies/batch_*.py" --output-dir results

# Process many strategies in parallel
hypertrial --strategy-dir strategies/ --processes 4 --output-dir results

# Process large sets of strategies in batches to manage memory
hypertrial --glob-pattern "*.py" --batch-size 10 --output-dir results

# Disable plots during backtest
hypertrial --strategy my_strategy --no-plots
```

## What is DCA?

Dollar-Cost Averaging (DCA) is an investment strategy where you invest a fixed amount at regular intervals, regardless of price. With Bitcoin, DCA helps mitigate volatility while accumulating BTC over time.

Hypertrial extends this concept by allowing for "dynamic" DCA - varying the purchase amounts strategically while maintaining the same total investment.

## Resources

- **GitHub Repository**: [github.com/mattfaltyn/hypertrial](https://github.com/mattfaltyn/hypertrial)
- **PyPI Package**: [pypi.org/project/hypertrial](https://pypi.org/project/hypertrial/)
- **Documentation**: Available in the repository's tutorials directory
- **Issue Tracker**: Submit issues on GitHub

## License

This project is available under the MIT License.
