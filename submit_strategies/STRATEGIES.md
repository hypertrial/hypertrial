# External Strategies

This directory contains user-contributed strategies for the Hypertrial backtesting system.

## Contributing a Strategy

To create a new strategy:

1. Create a new Python file in this directory
2. Import the necessary modules:
   ```python
   from core.strategies import register_strategy
   from core.strategies.base_strategy import StrategyTemplate
   ```
3. Create a class that inherits from `StrategyTemplate`
4. Implement at minimum the following methods:
   - `construct_features(df)` - Creates any additional features needed for your strategy
   - `compute_weights(df)` - Computes the weight allocations for each day
5. Create a function that uses your strategy class and decorate it with `@register_strategy`

## Quick Example

Here's a minimal example of a valid strategy:

```python
# submit_strategies/my_awesome_strategy.py
import pandas as pd
import numpy as np
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import register_strategy
from core.strategies.base_strategy import StrategyTemplate

class MyAwesomeStrategy(StrategyTemplate):
    """
    A strategy that allocates more weight to days when price is below the 50-day MA.
    """

    @staticmethod
    def construct_features(df):
        df = df.copy()
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

        # Normalize weights so they sum to 1.0 in each 4-year cycle
        start_year = pd.to_datetime(BACKTEST_START).year
        cycle_labels = df_backtest.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)

        for cycle, group in weights.groupby(cycle_labels):
            # Normalize to sum to 1.0
            cycle_sum = group.sum()
            if cycle_sum > 0:
                weights.loc[group.index] = weights.loc[group.index] / cycle_sum

        return weights

# Register the strategy
@register_strategy("my_awesome_strategy")
def my_awesome_strategy(df):
    """
    A strategy that allocates more weight when price is below the 50-day MA.
    """
    return MyAwesomeStrategy.get_strategy_function()(df)
```

## Testing Your Strategy

To test your strategy:

1. Make sure your file is in the `submit_strategies` directory
2. Run the following command to see if your strategy is loaded:
   ```
   py -m core.main --list
   ```
3. Test your strategy specifically:
   ```
   py -m core.main --strategy my_strategy_name
   ```
4. Run it with all strategies for comparison:
   ```
   py -m core.main --backtest-all
   ```

## Advanced Features

- **Strategy parameters**: You can customize constants in `core/config.py` or create your own parameters
- **Performance optimization**: Consider using vectorized operations (numpy/pandas) instead of loops
- **Input validation**: Add validation in your strategy to handle edge cases

## Troubleshooting

- **Strategy not showing up**: Ensure your file is correctly registered with `@register_strategy`
- **Import errors**: Check that all imports are correctly specified
- **Runtime errors**: Common issues include missing data handling and division by zero

## Core vs External Strategies

- Core strategies are located in `core/strategies/`
- External (user-contributed) strategies are located in this directory

Both types of strategies use the same registration mechanism and will be available to the backtesting system.
