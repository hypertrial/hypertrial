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

## Getting Started

### Prerequisites

- Python 3.6+
- Required packages:
  - pandas
  - numpy
  - matplotlib
  - coinmetrics-api-client (2024.2.6.16+)

### Installation

1. Clone this repository

```bash
git clone https://github.com/yourusername/hypertrial.git
cd hypertrial
```

2. Install required dependencies

```bash
pip install pandas numpy matplotlib coinmetrics-api-client
```

### Usage

1. Extract the Bitcoin price data (one-time setup):

```bash
python -m core.extract_data
```

2. Run the default strategy backtest:

```bash
python -m core.main
```

3. Run with a specific strategy:

```bash
python -m core.main --strategy uniform_dca
```

4. List all available strategies:

```bash
python -m core.main --list
```

5. Run without generating plots (numeric results only):

```bash
python -m core.main --no-plots
```

6. Command-line options can be combined:

```bash
python -m core.main --strategy uniform_dca --no-plots
```

## Project Structure

- `core/main.py`: Entry point that orchestrates the backtest process
- `core/data.py`: Handles data loading from local CSV (with fallback to CoinMetrics API)
- `core/extract_data.py`: Script to fetch and cache Bitcoin price data
- `core/strategies/`: Directory containing all available DCA strategies
- `core/spd.py`: Contains SPD (Sats Per Dollar) calculation logic
- `core/plots.py`: Visualization functions for strategy performance
- `core/config.py`: Configuration parameters for the backtest

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
