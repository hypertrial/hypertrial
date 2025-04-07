# Stacking Sats

A flexible Bitcoin investment strategy backtesting library. Easily create, test, and analyze custom Bitcoin investment strategies.

## Features

- Clean, modular architecture for strategy development
- Template-based approach for creating custom strategies
- Simple API for running backtests
- Visualization tools for performance analysis
- Data loading utilities for multiple formats
- Example strategies included
- Command-line interface (CLI) for quick backtesting
- Configuration management system

## Installation

### Recommended: Install using Virtual Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/stacking_sats.git
cd stacking_sats

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies directly (recommended)
pip install pandas numpy matplotlib pyarrow pyyaml pytest pytest-asyncio pytest-xprocess pytest-cov

# Install the package in development mode
pip install -e .

# If you need data utilities
pip install cryptocompare yfinance
```

### Troubleshooting Installation Issues

If you encounter errors during installation, especially with Python 3.12:

1. Make sure your pip is up to date:

   ```bash
   pip install --upgrade pip
   ```

2. Install binary wheels when possible:

   ```bash
   pip install --only-binary=:all: pandas numpy matplotlib
   ```

3. If you encounter `distutils` related errors (common in Python 3.12):
   - Try installing packages one at a time
   - Use pre-built binary wheels when possible
   - Avoid using `-e .[dev]` directly

### Alternative: Quick Install (not for development)

```bash
# Simple installation
pip install git+https://github.com/yourusername/stacking_sats.git
```

## Quick Start

### Single-Line Backtest Command

```bash
# Run a backtest with a single command
stacksats DynamicAllocationStrategy --param alpha=1.5 --start-date 2018-01-01 --end-date 2023-12-31 --capital 10000
```

### Python API

```python
from stacking_sats.core.data_loader import load_btc_data
from stacking_sats.strategies.examples.dynamic_allocation_strategy import DynamicAllocationStrategy
from stacking_sats.core.backtest import backtest

# Load data
data = load_btc_data()

# Create strategy
strategy = DynamicAllocationStrategy(alpha=1.5)

# Run backtest
results = backtest(
    data=data,
    strategy=strategy,
    start_date='2018-01-01',
    end_date='2023-12-31',
    initial_capital=10000.0,
    plot=True
)

# Print SPD metrics
print(results['spd_metrics'])
```

### Command-Line Interface

The package provides a command-line tool for quick backtesting:

```bash
# List available strategies
stacksats --list-strategies

# Run a backtest with parameters
stacksats DynamicAllocationStrategy --param alpha=1.5 --param min_weight=0.0002 --start-date 2018-01-01 --end-date 2023-12-31 --capital 10000

# Control plotting
stacksats DynamicAllocationStrategy --no-plot  # Disable all plots
stacksats DynamicAllocationStrategy --show-portfolio  # Show portfolio performance plot
stacksats DynamicAllocationStrategy --no-weights  # Hide allocation weights plot
stacksats DynamicAllocationStrategy --no-spd  # Hide SPD metrics plots

# Run a backtest and save results
stacksats DynamicAllocationStrategy --save-dir ./results

# Save strategy configuration for future use
stacksats DynamicAllocationStrategy --param alpha=1.5 --save-config
```

## Creating Custom Strategies

To create your own strategy:

1. Create a new Python file for your strategy
2. Inherit from `BaseStrategy` class
3. Implement the `prepare_data` and `generate_weights` methods

```python
from stacking_sats.strategies.base_strategy import BaseStrategy
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    def __init__(self, param1=0.5, param2=200):
        super().__init__(param1=param1, param2=param2)
        self.param1 = param1
        self.param2 = param2

    def prepare_data(self, data):
        # Add your indicators and features here
        df = data.copy()
        df['indicator1'] = ...
        return df

    def generate_weights(self, data):
        # Implement your weight calculation logic
        weights = pd.Series(...)
        return weights
```

See the `stacking_sats/strategies/templates/strategy_template.py` file for a more detailed example.

## Project Structure

```
stacking_sats/
├── cli/                # Command-line interface
│   ├── main.py         # CLI entry point
│   ├── utils.py        # CLI utilities
│   └── strategy_loader.py # Strategy loading utilities
├── core/               # Core functionality
│   ├── backtest.py     # Backtesting engine
│   ├── data_loader.py  # Data loading utilities
│   ├── logger.py       # Logging system
│   └── config/         # Configuration management
├── strategies/         # Strategy implementations
│   ├── base_strategy.py
│   ├── templates/      # Strategy templates
│   └── examples/       # Example strategies
├── data/               # Data storage and utilities
├── examples/           # Usage examples
├── tests/              # Test suite
└── README.md           # This file
```

## Configuration Management

Stacking Sats now includes a configuration management system that allows you to:

- Save and load strategy parameters
- Set default values for backtests
- Configure logging
- Customize visualization settings

Configuration is stored in `~/.stacking_sats/config.yaml` by default. You can use the `--save-config` flag in the CLI to save your current settings for future use.

```python
# Using the configuration system in your code
from stacking_sats.core.config.config_manager import ConfigManager

# Load configuration
config = ConfigManager()

# Get configuration values
backtest_settings = config.get("backtest")
initial_capital = config.get("backtest", "default_initial_capital")

# Set configuration values
config.set("backtest", "default_initial_capital", 5000.0)

# Save strategy parameters
config.save_strategy_config("MyStrategy", {"param1": 0.5, "param2": 200})
```

## Logging

Stacking Sats includes a flexible logging system:

```python
from stacking_sats.core.logger import setup_logger, get_strategy_logger

# Create a logger for a specific component
logger = setup_logger("my_component")

# Or get a logger for a strategy
strategy_logger = get_strategy_logger("MyStrategy")

# Log messages
logger.info("Starting backtest")
logger.debug("Processing data")
logger.warning("Missing data point")
logger.error("Failed to load strategy")
```

Logs are stored in `~/.stacking_sats/stacking_sats.log` by default.

## Recent Updates

The package has been cleaned up and restructured for better organization and maintainability:

1. **Improved Package Structure**:

   - Moved CLI to its own module
   - Added proper logging system
   - Created a configuration management system
   - Organized tests in a standard structure

2. **Enhanced Code Quality**:

   - Added type hints
   - Improved error handling
   - Better docstrings
   - Better parameter validation

3. **New Features**:
   - Configuration persistence
   - User-defined strategy support
   - Better CLI experience
4. **Development Tools**:
   - Added pyproject.toml with modern Python packaging
   - Added configuration for code formatting and linting
   - Set up GitHub Actions for CI/CD
   - Automated dependency updates

## Development

### Setting Up the Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/stacking_sats.git
cd stacking_sats

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies first
pip install pandas numpy matplotlib pyarrow pyyaml

# Install development dependencies
pip install pytest pytest-asyncio pytest-xprocess pytest-cov
pip install black isort flake8 mypy

# Install data utilities if needed
pip install cryptocompare yfinance

# Install the package in development mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=stacking_sats

# Run specific test file
pytest tests/test_strategy.py

# Run tests verbosely
pytest -v
```

### Code Formatting and Linting

The codebase uses:

- [Black](https://github.com/psf/black) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [Flake8](https://flake8.pycqa.org/) for code linting
- [mypy](https://mypy.readthedocs.io/) for type checking

Run the tools:

```bash
# Format code
black stacking_sats

# Sort imports
isort stacking_sats

# Lint code
flake8 stacking_sats

# Check types
mypy stacking_sats
```

### Continuous Integration

The repository uses GitHub Actions for CI/CD:

- Runs tests on multiple Python versions
- Performs linting and type checking
- Generates coverage reports
- Checks package building

## Data Requirements

Your data should have the following:

- DatetimeIndex as the index
- A 'btc_close' column with price data

You can use the data loading utilities to help format your data correctly.

## Running a Backtest

The simple `backtest` function provides an easy way to run backtests:

```python
from stacking_sats.core.backtest import backtest

results = backtest(
    data=your_data,              # DataFrame with price data
    strategy=your_strategy,      # Instance of a strategy
    start_date='2018-01-01',     # Start date (optional)
    end_date='2023-12-31',       # End date (optional)
    initial_capital=10000.0,     # Starting capital (default: 1000.0)
    fee_pct=0.001,               # Trading fee percentage (default: 0.0)
    plot=True,                   # Whether to enable any plotting (default: True)
    plot_portfolio=False,        # Whether to plot portfolio performance (default: False)
    plot_weights=True,           # Whether to plot allocation weights (default: True)
    plot_spd=True,               # Whether to plot SPD metrics (default: True)
    benchmark=benchmark_data,    # Benchmark for comparison (optional)
    save_dir='results/'          # Directory to save results (optional)
)
```

## Visualization Options

Stacking Sats provides various visualization options for analyzing backtest results:

- **Allocation Weights**: Shows how the strategy allocates capital over time
- **SPD Metrics**: Shows SPD (Sats-Per-Dollar) performance with cycle breakdowns
- **Portfolio Performance**: Shows the normalized portfolio value over time (disabled by default)

By default, only the allocation weights and SPD metrics plots are shown. You can control which plots are displayed using the CLI options or function parameters.

## Performance Metrics

Stacking Sats uses SPD (Sats-Per-Dollar) metrics for performance evaluation instead of traditional financial metrics. This Bitcoin-specific approach better captures the effectiveness of a Bitcoin accumulation strategy.

### SPD Metrics

The backtest results include the following SPD metrics:

- **Strategy SPD**: Satoshis acquired per dollar using the strategy's weights
- **Uniform SPD**: Satoshis acquired per dollar using uniform dollar-cost averaging (DCA)
- **Min SPD**: Worst-case scenario (buying at highest price)
- **Max SPD**: Best-case scenario (buying at lowest price)
- **Strategy Percentile**: Where the strategy falls between worst and best case (0-100%)
- **Uniform Percentile**: Where uniform DCA falls between worst and best case (0-100%)
- **Excess Percentile**: How much the strategy outperforms uniform DCA

Results are also broken down by 4-year Bitcoin cycles to show performance in different market conditions.

### Why SPD Metrics?

SPD metrics directly measure what matters in Bitcoin accumulation: how many satoshis you acquire per dollar invested. This approach:

1. Focuses on accumulation rather than price speculation
2. Provides a clear benchmark against uniform DCA
3. Shows how close your strategy comes to theoretical best/worst cases
4. Evaluates performance across market cycles
5. Quantifies exactly how much better (or worse) your strategy performs compared to simple DCA

Traditional metrics like returns and Sharpe ratio are still available in the results but are secondary to the SPD analysis.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
