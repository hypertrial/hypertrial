# submit_strategies/__init__.py
"""
This directory contains user-contributed strategies.
Core strategies are located in core/strategies.
"""

# Import from core.strategies to expose registration functions
from core.strategies import register_strategy, get_strategy, list_strategies, available_strategies

__version__ = "0.1.10"
