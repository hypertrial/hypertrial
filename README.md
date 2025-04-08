# Hypertrial: Bitcoin Dollar-Cost Averaging (DCA) Tournament

A Bitcoin DCA strategy competition platform for evaluating and comparing participant-submitted algorithms.

## Tournament Overview

Hypertrial hosts a Bitcoin DCA strategy tournament where participants submit their custom strategies to compete for the highest performance. Your strategy will be evaluated using Sats Per Dollar (SPD) metrics across multiple Bitcoin market cycles, allowing for objective comparison against other participants.

As a tournament participant, your task is to develop and submit a custom DCA strategy that outperforms traditional approaches by strategically adjusting purchase weights based on market conditions.

## How to Participate

1. **Clone this repository** to your local machine
2. **Create your strategy** in the `submit_strategies` directory
3. **Test your strategy** against our test suite
4. **Submit your strategy** for official tournament evaluation

## Features

- **External Strategy Submissions**: Add your strategy to the `submit_strategies` directory
- **Automated Testing**: Verify your strategy works with our test suite
- **Performance Metrics**: Compare your strategy against others using SPD metrics
- **Cross-Cycle Analysis**: See how your strategy performs across different Bitcoin market cycles
- **Equal Evaluation**: All strategies tested against the same historical data

## Getting Started

### Prerequisites

- Python 3.6+
- Required packages (automatically installed when you install Hypertrial):
  - pandas
  - numpy
  - matplotlib
  - coinmetrics-api-client (2024.2.6.16+)
  - pytest (for running tests)

### Installation

```bash
git clone https://github.com/mattfaltyn/hypertrial.git
cd hypertrial
pip install -e .  # Install in development mode
```

### Tournament Submission Process

1. Look at the example strategy in `submit_strategies/dynamic_dca_50ma.py`
2. Create a new Python file in the `submit_strategies` directory
3. Copy the template from `submit_strategies/strategy_template.py`
4. Implement your strategy following the provided structure
5. Test your strategy using the commands below

For detailed submission instructions, see [submit_strategies/STRATEGIES.md](submit_strategies/STRATEGIES.md).

### Verifying Your Submission

1. Ensure your data is set up correctly:

```bash
python -m core.data.extract_data
```

2. Test your strategy specifically:

```bash
python -m core.main --strategy your_strategy_name
```

3. Run automated tests to verify your strategy meets all requirements:

```bash
pytest tests/test_submit_strategies.py
```

4. Compare your strategy against baseline strategies:

```bash
python -m core.main --backtest-all --output-dir results
```

## Complete Submission Workflow

### 1. Clone the Repository

```bash
git clone https://github.com/mattfaltyn/hypertrial.git
cd hypertrial
pip install -e .  # Install in development mode
```

### 2. Prepare the Data

Extract and prepare the Bitcoin price data:

```bash
python -m core.data.extract_data
```

### 3. Create Your Strategy

Create a new file in the `submit_strategies` directory:

```bash
cp submit_strategies/strategy_template.py submit_strategies/my__strategy.py
```

Edit your strategy file following the template structure. Be sure to:

- Implement the `construct_features` and `compute_weights` methods
- Register your strategy with a unique name using `@register_strategy`
- Document your strategy approach in the class docstring

### 4. Verify Your Strategy

Run the test suite to ensure your strategy meets all tournament requirements:

```bash
pytest tests/test_submit_strategies.py
```

### 5. Test Your Strategy's Performance

Evaluate how your strategy performs:

```bash
python -m core.main --strategy my_strategy
```

### 6. Compare Against Other Strategies

See how your strategy ranks against baseline strategies:

```bash
python -m core.main --backtest-all --output-dir results
```

### 7. Submit Your Strategy

For the tournament:

1. Fork the repository
2. Add your strategy to the `submit_strategies` directory
3. Run tests to verify it works correctly
4. Submit a pull request with ONLY your strategy file in the `submit_strategies` directory

## Project Structure

- `core/`: Core framework code (not to be modified by participants)
  - `main.py`: Evaluation system that runs the backtests
  - `data.py`: Data loading system
  - `strategies/`: Built-in baseline strategies for comparison
  - `spd.py`: Contains SPD (Sats Per Dollar) calculation logic
  - `plots.py`: Visualization functions for strategy performance
  - `config.py`: Configuration parameters for the backtest
- `submit_strategies/`: **Directory for tournament submissions**
  - `strategy_template.py`: Template to use for your submission
  - `STRATEGIES.md`: Detailed tournament submission instructions
- `tests/`: Test suite
  - `test_submit_strategies.py`: Tests to verify your submission
- `results/`: Directory where strategy comparison results are stored

## Tournament Rules and Guidelines

1. Your strategy must be implemented in a single Python file within `submit_strategies/`
2. You may not modify any code in the `core/` directory
3. Your strategy must pass all tests in `tests/test_submit_strategies.py`
4. Your strategy should be appropriately documented
5. External data sources are allowed, but your strategy must fit the structure in `strategy_template.py`
6. Strategies will be ranked by their mean excess SPD percentile compared to uniform DCA

## Configuration

Key parameters in `config.py` (DO NOT MODIFY):

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
