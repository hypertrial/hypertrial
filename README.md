# Hypertrial: Bitcoin Dollar-Cost Averaging (DCA) Backtest

A Python-based backtesting framework for evaluating Bitcoin DCA strategy performance across multiple market cycles.

## Overview

Hypertrial implements and tests a threshold-based dynamic DCA strategy that outperforms traditional uniform DCA by strategically adjusting purchase weights based on price deviations from the 200-day moving average.

The framework measures performance using Sats Per Dollar (SPD) across 4-year Bitcoin market cycles, allowing for objective comparison between different strategies.

## Features

- **Data Collection**: Automatically retrieves historical Bitcoin price data using CoinMetrics API
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

Run the main backtest:

```bash
python core/main.py
```

## Project Structure

- `core/main.py`: Entry point that orchestrates the backtest process
- `core/data.py`: Handles data loading from CoinMetrics API
- `core/user_strategy.py`: Implements the dynamic DCA weight allocation strategy
- `core/spd.py`: Contains SPD (Sats Per Dollar) calculation logic
- `core/plots.py`: Visualization functions for strategy performance
- `core/config.py`: Configuration parameters for the backtest

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
