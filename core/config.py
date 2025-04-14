# config.py

# Define backtest date constants (keeping these as globals for simple access)
BACKTEST_START = '2013-01-01'
BACKTEST_END = '2024-12-31'
MIN_WEIGHT = 1e-4

class StrategyConfig:
    """Configuration parameters for strategy behavior."""
    
    def __init__(self):
        # Boost factor for z-score
        self.ALPHA = 1.25
        # Rebalance window in days (two years)
        self.REBALANCE_WINDOW = 365 * 2

# Create a default global instance for backward compatibility
strategy_config = StrategyConfig()

# For backward compatibility, making these accessible at the module level
ALPHA = strategy_config.ALPHA
REBALANCE_WINDOW = strategy_config.REBALANCE_WINDOW
