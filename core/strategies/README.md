# Hypertrial Strategy Framework

This directory contains all strategies that can be used with the Hypertrial backtesting framework.

## Available Strategies

- `dynamic_dca.py`: The original threshold-based DCA strategy with constrained early bias rebalancing.
- `uniform_dca.py`: A simple uniform DCA strategy for baseline comparison.

## Creating Your Own Strategy

To create a new strategy:

1. Copy `strategy_template.py` to a new file with a descriptive name (e.g., `my_strategy.py`)
2. Rename the `NewStrategy` class and update its docstring
3. Implement the `construct_features` and `compute_weights` methods
4. Register your strategy by uncommenting and modifying the registration line at the bottom of the file:
   ```python
   my_strategy = register_strategy("my_strategy_name")(MyStrategy.get_strategy_function())
   ```

## Strategy Interface

Each strategy must implement:

1. `construct_features(df)`: Add any features needed for your strategy (technical indicators, etc.)
2. `compute_weights(df)`: Calculate daily weight allocations for the DCA strategy

The `StrategyTemplate` base class handles the rest of the implementation details.

## Running Your Strategy

To run the backtester with your strategy, use:

```
python -m core.main --strategy my_strategy_name
```

To list all available strategies:

```
python -m core.main --list
```

## Required Imports

Your strategy file should include these imports:

```python
import pandas as pd
import numpy as np
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate
```
