# Hypertrial: Bitcoin Dollar-Cost Averaging (DCA) Backtest

A Python-based backtesting framework for evaluating Bitcoin DCA strategy performance across multiple market cycles.

## Overview

Hypertrial implements and tests various Bitcoin DCA strategies including a threshold-based dynamic approach that outperforms traditional uniform DCA by strategically adjusting purchase weights based on price deviations from the 200-day moving average.

The framework measures performance using Sats Per Dollar (SPD) across 4-year Bitcoin market cycles, allowing for objective comparison between different strategies.

## Features

- **Pluggable Strategy System**: Easily create and test custom DCA strategies
- **Data Collection**: Automatically retrieves and stores historical Bitcoin price data
- **Dynamic DCA Strategy**: Implements a 200-day MA threshold strategy with customizable parameters
- **Performance Metrics**: Calculates and compares SPD for both uniform DCA and dynamic strategies
- **Visualization**: Generates detailed plots showing strategy performance over time
- **Cycle Analysis**: Groups results by Bitcoin's characteristic 4-year cycles
- **Batch Processing**: Run all strategies at once and compare results in CSV format

## Getting Started

### Prerequisites

- Python 3.6+
- Required packages (automatically installed when you install Hypertrial):
  - pandas
  - numpy
  - matplotlib
  - coinmetrics-api-client (2024.2.6.16+)

### Installation

Option 1: Install from PyPI (recommended)

```bash
pip install hypertrial
```

Option 2: Install from source

```bash
git clone https://github.com/mattfaltyn/hypertrial.git
cd hypertrial
pip install .
```

Option 3: Install in development mode (changes to code are immediately reflected)

```bash
git clone https://github.com/mattfaltyn/hypertrial.git
cd hypertrial
pip install -e .
```

Option 4: Install dependencies only (without installing the package)

```bash
git clone https://github.com/mattfaltyn/hypertrial.git
cd hypertrial
pip install -r requirements.txt
```

### Usage

1. Extract the Bitcoin price data (one-time setup):

```bash
python -m core.data.extract_data
```

2. Run the default strategy backtest:

```bash
python -m core.main
```

After installation, you can also use the command-line interface:

```bash
hypertrial  # Run with default options
```

3. Run with a specific strategy:

```bash
python -m core.main --strategy uniform_dca
# OR
hypertrial --strategy uniform_dca
```

4. List all available strategies:

```bash
python -m core.main --list
# OR
hypertrial --list
```

5. Run without generating plots (numeric results only):

```bash
python -m core.main --no-plots
# OR
hypertrial --no-plots
```

6. Backtest all strategies at once and save results to CSV:

```bash
python -m core.main --backtest-all
# OR
hypertrial --backtest-all
```

7. Customize the output directory:

```bash
python -m core.main --backtest-all --output-dir my_results
# OR
hypertrial --backtest-all --output-dir my_results
```

8. Command-line options can be combined:

```bash
python -m core.main --strategy uniform_dca --no-plots
# OR
hypertrial --strategy uniform_dca --no-plots
```

## Complete Workflow

Here's the complete workflow from creating a custom strategy to running a backtest:

### 1. Data Extraction

First, extract and prepare the Bitcoin price data:

```bash
python -m core.data.extract_data
```

This will:

- Fetch Bitcoin price data from CoinMetrics API
- Clean and validate the data
- Save it as a CSV file in the `core/data/` directory

### 2. Strategy Creation

Create a new strategy file in the `core/strategies/` directory:

```bash
touch core/strategies/my_custom_strategy.py
```

Implement your strategy following this template:

```python
# my_custom_strategy.py
import pandas as pd
from core.strategies import register_strategy

@register_strategy("my_custom_strategy")
def my_custom_strategy(df):
    """
    My custom DCA strategy.

    This strategy implements [brief description of your strategy logic].

    Args:
        df (pandas.DataFrame): Price data with datetime index

    Returns:
        pandas.Series: Weight for each date, indexed by date
    """
    # Your strategy logic here
    # Example: Create weights based on some calculation
    weights = pd.Series(1.0, index=df.index)  # Default uniform weight

    # Apply your custom logic to modify weights
    # Example: Increase weights when price is below a threshold

    return weights
```

### 3. Backtesting

Run a backtest with your custom strategy:

```bash
python -m core.main --strategy my_custom_strategy
```

This will:

- Load the Bitcoin price data
- Apply your strategy to generate purchase weights
- Calculate the SPD (Sats Per Dollar) performance
- Generate performance plots
- Show summary statistics for your strategy

### 4. Compare Strategies

To compare your strategy against other strategies:

```bash
python -m core.main --backtest-all --output-dir results
```

This creates:

- A CSV file with performance metrics for all strategies
- Performance plots for each strategy
- A summary report that ranks the strategies

### 5. Refine Strategy

Based on the backtest results:

1. Analyze the performance metrics
2. Identify areas for improvement
3. Modify your strategy code
4. Run the backtest again to see if performance improves

### 6. Implement in Production

Once satisfied with your strategy's performance:

1. Export the strategy parameters
2. Implement the strategy in your Bitcoin purchasing system
3. Schedule regular purchases according to the strategy's recommendations

## Project Structure

- `core/main.py`: Entry point that orchestrates the backtest process
- `core/data.py`: Handles data loading from local CSV (with fallback to CoinMetrics API)
- `core/data/extract_data.py`: Script to fetch and cache Bitcoin price data
- `core/strategies/`: Directory containing all available DCA strategies
- `core/spd.py`: Contains SPD (Sats Per Dollar) calculation logic
- `core/plots.py`: Visualization functions for strategy performance
- `core/config.py`: Configuration parameters for the backtest
- `results/`: Directory where strategy comparison results are stored

## Creating Your Own Strategies

1. Copy `core/strategies/strategy_template.py` to a new file with a descriptive name
2. Implement your strategy by extending the StrategyTemplate class
3. Register your strategy with a unique name using the decorator
4. Run your strategy with `python -m core.main --strategy your_strategy_name`

See `core/strategies/README.md` for detailed instructions.

## Configuration

Key parameters in `config.py`:

- `BACKTEST_START`: Start date for backtest (default: '2013-01-01')
- `BACKTEST_END`: End date for backtest (default: '2024-12-31')
- `ALPHA`: Boost factor for z-score (default: 1.25)
- `REBALANCE_WINDOW`: Days to distribute excess weight (default: 730, two years)
- `MIN_WEIGHT`: Minimum weight threshold (default: 1e-4)

## License

This project is available under the MIT License.

## Acknowledgments

- [CoinMetrics](https://coinmetrics.io/) for their comprehensive Bitcoin price data
- Inspired by various Bitcoin DCA strategy research
