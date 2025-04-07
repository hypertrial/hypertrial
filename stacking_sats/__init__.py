"""
Stacking Sats - A BTC investment strategy backtest library.
"""

__version__ = '0.1.0'

# Import core functionality for easy access
from stacking_sats.core.backtest import backtest, BacktestEngine
from stacking_sats.strategies.base_strategy import BaseStrategy 