# Hypertrial: Stacking Sats Challenge

A Bitcoin Dollar-Cost Averaging (DCA) tournament platform for evaluating and comparing participant-submitted algorithms.

[![PyPI version](https://img.shields.io/pypi/v/hypertrial.svg)](https://pypi.org/project/hypertrial/)
[![PyPI status](https://img.shields.io/pypi/status/hypertrial.svg)](https://pypi.org/project/hypertrial/)
[![Python versions](https://img.shields.io/pypi/pyversions/hypertrial.svg)](https://pypi.org/project/hypertrial/)

## Tournament Overview

Hypertrial's Stacking Sats challenge hosts a Bitcoin DCA strategy tournament where participants submit their custom strategies to compete for the highest performance. Your strategy will be evaluated using Sats Per Dollar (SPD) metrics across multiple Bitcoin market cycles, allowing for objective comparison against other participants.

As a tournament participant, your task is to develop and submit a custom DCA strategy that outperforms traditional approaches by strategically adjusting purchase weights based on market conditions.

**IMPORTANT:** External data sources are strictly prohibited in the tournament. Strategies must only use the provided Bitcoin price data. Any attempts to access external APIs or data sources will result in immediate rejection of your strategy.

## How to Participate

1. **Start with Tutorial 1**: Review [`tutorials/1. Intro.ipynb`](tutorials/1.%20Intro.ipynb) to understand the basics
2. **Learn the Challenge**: Read through [`tutorials/2. Challenge Overview.ipynb`](tutorials/2.%20Challenge%20Overview.ipynb) to understand the competition
3. **Create Your Strategy**: Follow [`tutorials/3. Submission_Template.ipynb`](tutorials/3.%20Submission_Template.ipynb) to develop and test your strategy
4. **Submit Your Strategy**: Follow the submission instructions at the end of Tutorial 3

## Features

- **External Strategy Submissions**: Add your strategy to the `submit_strategies` directory
- **Standalone Strategy Testing**: Run individual strategy files directly without installation
- **Automated Testing**: Verify your strategy works with our test suite
- **Performance Metrics**: Compare your strategy against others using SPD metrics
- **Cross-Cycle Analysis**: See how your strategy performs across different Bitcoin market cycles
- **Equal Evaluation**: All strategies tested against the same historical data
- **Security Scanning**: All submissions undergo thorough security analysis with Bandit
- **Validation Checks**: All strategies are validated by default to ensure they meet submission criteria

## Security Verification

All submitted strategies undergo comprehensive security checks:

1. **Static Analysis**: Code is scanned with Bandit, a security linter for Python
2. **Resource Monitoring**: Memory and CPU usage are restricted and monitored
3. **Dangerous Pattern Detection**: Prohibited functions and code patterns are blocked
4. **Module Restrictions**: Only approved modules can be imported
5. **External Data Validation**: All forms of external data access are blocked

Strategies with high or medium severity security issues will be automatically blocked from execution. For detailed security requirements, see `tests/TESTS.md` and `core/SECURITY.md`.

### Test Mode Security Behavior

The system detects when running in test mode and applies more relaxed resource limits:

- Execution time limit is extended from 30 seconds to 60 seconds in test mode
- CPU time limit is extended from 10 seconds to 30 seconds in test mode
- Certain DataFrame operations (like `to_csv`, `to_datetime`, `to_numpy`, `to_dict`, `to_records`, `to_series`) are permitted in test mode but restricted in production
- Security tests dynamically adjust validation requirements based on test context

## Getting Started

### Prerequisites

- Python 3.6 - 3.13
- Required packages (automatically installed when you install Hypertrial):
  - pandas
  - numpy
  - matplotlib
  - coinmetrics-api-client (2024.2.6.16+)
  - pytest (for running tests)

### Installation

**Option 1: Install from PyPI (Recommended)**

```bash
# Create a virtual environment
python -m venv hypertrial_venv
source hypertrial_venv/bin/activate  # On Windows: hypertrial_venv\Scripts\activate

# Install from PyPI
pip install hypertrial
```

**Option 2: Install from Source**

```bash
# Create a virtual environment
python -m venv hypertrial_venv

# Activate the virtual environment
# On Windows:
hypertrial_venv\Scripts\activate
# On macOS/Linux:
source hypertrial_venv/bin/activate

# Clone and install
git clone https://github.com/mattfaltyn/hypertrial.git
cd hypertrial
pip install -e .  # Install in development mode
```

### Command Line Interface

You can interact with Hypertrial directly from the command line. Here's a comprehensive list of all available commands and flags:

#### Basic Usage

```bash
# List all available strategies
python -m core.main --list

# Run backtest with a specific strategy
python -m core.main --strategy dynamic_dca

# Run a standalone strategy file (without loading other strategies)
python -m core.main --strategy-file path/to/my_strategy.py --standalone

# Test a strategy file while still loading registered strategies
python -m core.main --strategy-file path/to/my_strategy.py
```

#### Running Example Strategy from Tutorials

```bash
# Run example_strategy.py in standalone mode (with validation enabled by default)
python -m core.main --strategy-file tutorials/example_strategy.py --standalone

# Run example_strategy.py without validation checks
python -m core.main --strategy-file tutorials/example_strategy.py --standalone --no-validate

# Run example_strategy.py with custom data file
python -m core.main --strategy-file tutorials/example_strategy.py --standalone --data-file custom_data.csv

# Run example_strategy.py (dynamic_dca_10ma) as a registered strategy if it's been registered
python -m core.main --strategy dynamic_dca_10ma

# Save plots from example_strategy.py to the results directory
python -m core.main --strategy-file tutorials/example_strategy.py --standalone --save-plots --output-dir results
```

#### Batch Processing

```bash
# Run backtest for all registered strategies
python -m core.main --backtest-all --output-dir results

# Backtest multiple strategy files from custom paths
python -m core.main --strategy-files path/to/strategy1.py path/to/strategy2.py --output-dir results

# Backtest all Python files in a directory
python -m core.main --strategy-dir path/to/strategies/dir --output-dir results

# Backtest files matching a glob pattern
python -m core.main --glob-pattern "strategies/batch_*.py" --output-dir results

# Process many strategies in parallel (4 processes)
python -m core.main --strategy-dir strategies/ --processes 4 --output-dir results

# Process large sets of strategies in batches of 10 to manage memory
python -m core.main --glob-pattern "*.py" --batch-size 10 --output-dir results
```

#### Display and Output Options

```bash
# Disable plots during backtest
python -m core.main --strategy my_strategy --no-plots

# Save plots to files instead of displaying them
python -m core.main --strategy dynamic_dca --save-plots --output-dir plots_dir

# Process strategies with a custom timeout (in seconds)
python -m core.main --strategy-dir strategies/ --file-timeout 120
```

#### Data Management

```bash
# Force download fresh Bitcoin price data
python -m core.main --strategy dynamic_dca --download-data

# Use a custom data file
python -m core.main --strategy dynamic_dca --data-file path/to/custom_data.csv
```

#### Directory and File Filtering

```bash
# Recursively search directories
python -m core.main --strategy-dir strategies/ --recursive

# Exclude specific directories
python -m core.main --strategy-dir strategies/ --exclude-dirs tests __pycache__

# Exclude files matching specific patterns
python -m core.main --strategy-dir strategies/ --exclude-patterns test_*.py *_draft.py

# Include only files matching specific patterns
python -m core.main --strategy-dir strategies/ --include-patterns *_final.py *_v2.py

# Limit the number of files to process
python -m core.main --strategy-dir strategies/ --max-files 50
```

#### Validation Control

```bash
# Disable validation checks (validation is enabled by default)
python -m core.main --strategy dynamic_dca --no-validate

# Run with validation explicitly enabled (default behavior)
python -m core.main --strategy dynamic_dca
```

### All Available Command-Line Options

| Flag                 | Shorthand | Description                                                    |
| -------------------- | --------- | -------------------------------------------------------------- |
| `--strategy`         | `-s`      | Strategy to use for backtesting (default: dynamic_dca)         |
| `--strategy-file`    | `-f`      | Path to a standalone Python strategy file for backtesting      |
| `--strategy-files`   | `-fs`     | List of paths to Python strategy files for batch backtesting   |
| `--strategy-dir`     | `-sd`     | Directory containing Python strategy files to backtest         |
| `--glob-pattern`     | `-gp`     | Glob pattern for finding strategy files                        |
| `--processes`        | `-p`      | Number of parallel processes to use (0=auto, 1=sequential)     |
| `--batch-size`       | `-bs`     | Process strategies in batches to manage memory (0=no batching) |
| `--file-timeout`     | `-ft`     | Maximum seconds allowed per strategy file (0=no timeout)       |
| `--exclude-dirs`     | `-ed`     | Directories to exclude when searching for files                |
| `--exclude-patterns` | `-ep`     | File patterns to exclude when searching                        |
| `--recursive`        | `-r`      | Recursively search for Python files in subdirectories          |
| `--include-patterns` | `-ip`     | File patterns to include when searching                        |
| `--max-files`        | `-mf`     | Maximum number of files to process (default: 100)              |
| `--standalone`       | `-st`     | Run only the specified strategy file without loading others    |
| `--save-plots`       | `-sp`     | Save plots to files in the output directory                    |
| `--list`             | `-l`      | List all available strategies                                  |
| `--no-plots`         | `-n`      | Disable plotting (only show numeric results)                   |
| `--backtest-all`     | `-a`      | Backtest all available strategies and output results           |
| `--output-dir`       | `-o`      | Directory to store results (default: results)                  |
| `--download-data`    | `-d`      | Force download of fresh BTC price data                         |
| `--data-file`        | `-df`     | Path to the price data CSV file                                |
| `--no-validate`      | `-nv`     | Disable strategy validation (validation is ON by default)      |

### Standalone Strategy Testing

The standalone mode is useful for directly testing strategy files without adding them to the project structure:

```bash
python -m core.main --strategy-file path/to/my_strategy.py --standalone
```

Key features of standalone mode:

- Runs a single strategy file in isolation
- Does not load other registered strategies
- Uses the same Bitcoin price data as the main framework
- Performs security validation of the strategy code
- Shows performance metrics and visualizations
- Useful for iterative development before final submission

The Bitcoin price data is loaded from:

1. The default local CSV file (`core/data/btc_price_data.csv`)
2. If the file doesn't exist, data is automatically downloaded from the CoinMetrics API

**Note:** While the framework downloads data from CoinMetrics during initialization, your strategy is not allowed to access external data sources directly.

You can specify a custom data file with:

```bash
python -m core.main --strategy-file path/to/my_strategy.py --standalone --data-file path/to/custom_data.csv
```

### Tournament Submission Process

1. Open and follow the instructions in the `tutorials/3. Submission_Template.ipynb` notebook. This notebook serves as the template and guide for creating your strategy.
2. Implement your strategy logic within the notebook environment.
3. Test your strategy using the code provided within the notebook.
4. Follow the instructions in the notebook to extract your final strategy code into a Python file for submission.

For detailed submission instructions, see the final sections of the `tutorials/3. Submission_Template.ipynb` notebook.

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

5. Submit a pull request with ONLY your strategy file in the `submit_strategies` directory

## Project Structure

- `core/`: Core framework code (not to be modified by participants)
  - `main.py`: Evaluation system that runs the backtests
  - `data.py`: Data loading system
  - `strategies/`: Built-in baseline strategies for comparison
  - `spd.py`: Contains SPD (Sats Per Dollar) calculation logic
  - `plots.py`: Visualization functions for strategy performance
  - `config.py`: Configuration parameters for the backtest
  - `security/`: Security verification and resource monitoring system
  - `spd_checks.py`: Strategy validation system for submission criteria
- `tutorials/`: Jupyter notebooks providing guidance and the submission template.
  - `1. Intro.ipynb`: Introduction to the platform.
  - `2. Challenge Overview.ipynb`: Details about the competition.
  - `3. Submission_Template.ipynb`: **Notebook for creating and testing your strategy.**
  - `example_strategy.py`: Example strategy implementation (dynamic_dca_10ma)
- `submit_strategies/`: **Directory for final tournament submissions (exported .py files)**
  - `STRATEGIES.md`: Detailed tournament submission instructions (supplements the notebook).
- `tests/`: Test suite
  - `test_submit_strategies.py`: Tests to verify your final submission file.
  - `test_strategy_file.py`: Tests for the standalone strategy file feature.
  - `test_security.py`: Tests for the security system
  - `TESTS.md`: Detailed testing information
- `results/`: Directory where strategy comparison results are stored

## Tournament Rules and Guidelines

1. Your strategy must be developed using the `tutorials/3. Submission_Template.ipynb` notebook and submitted as a single Python file within `submit_strategies/` after extraction.
2. You may not modify any code in the `core/` directory.
3. Your final submitted strategy file must pass all tests in `tests/test_submit_strategies.py`.
4. Your strategy should be appropriately documented within the notebook and the extracted file.
5. **External data sources are not allowed.** Strategies can only use the provided Bitcoin price data that is passed to the strategy function. Any attempts to access external APIs or data sources will result in immediate rejection.
6. Strategies will be ranked by their mean excess SPD percentile compared to uniform DCA

## Configuration

Key parameters in `config.py` (DO NOT MODIFY):

- `BACKTEST_START`: Start date for backtest (default: '2013-01-01')
- `BACKTEST_END`: End date for backtest (default: '2024-12-31')
- `ALPHA`: Boost factor for z-score (default: 1.25)
- `REBALANCE_WINDOW`: Days to distribute excess weight (default: 730, two years)
- `MIN_WEIGHT`: Minimum weight threshold (default: 1e-4)

### Security Configuration

The framework implements stringent security controls:

- **Bandit Security Analysis**: All code is scanned with Bandit for security issues
- **Severity Blocking**: Strategies with high or medium severity issues are blocked
- **Comprehensive Test Coverage**: Over 100 security tests covering various attack vectors
- **Restricted Environment**: Limited access to system resources and external services
- **Test Mode Detection**: Automatically identifies test execution for adjusted limits

Security configuration is defined in `core/security/config.py` and is not customizable by participants.

## Resources

- **GitHub Repository**: https://github.com/mattfaltyn/hypertrial
- **PyPI Package**: https://pypi.org/project/hypertrial/
- **Documentation**: Available in the repository's tutorials directory
- **Issue Tracker**: Submit issues on GitHub
- **Contact**: For questions about external data restrictions or other tournament rules, see the documentation or submit an issue on GitHub.

## License

This project is available under the MIT License.

## Acknowledgments

- [CoinMetrics](https://coinmetrics.io/) for their comprehensive Bitcoin price data
- Inspired by various Bitcoin DCA strategy research

### SPD Validation Tests

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

> **Note**: The forward-looking check (which previously verified that strategies don't use future data) has been removed from the validation process. Strategies are now evaluated only on the criteria listed above.
