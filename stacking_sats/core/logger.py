"""
Logging configuration for stacking_sats.
"""
import os
import logging
import logging.handlers
from typing import Optional, Dict, Any

from stacking_sats.core.config.config_manager import ConfigManager


def setup_logger(
    name: str = "stacking_sats",
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    use_config: bool = True
) -> logging.Logger:
    """
    Set up and configure a logger.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file. If None, uses the default from config
        log_format: Format for log messages. If None, uses the default from config
        use_config: Whether to use config settings for logging
        
    Returns:
        Configured logger
    """
    # Get configuration if requested
    if use_config:
        config_manager = ConfigManager()
        log_config = config_manager.get("logging")
        
        level = level or log_config.get("level", "INFO")
        log_file = log_file or log_config.get("file")
        log_format = log_format or log_config.get("format")
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Default format if not specified
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(log_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if log file is specified
    if log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger
logger = setup_logger()


def get_strategy_logger(strategy_name: str) -> logging.Logger:
    """
    Get a logger for a specific strategy.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Logger for the strategy
    """
    return setup_logger(f"stacking_sats.strategies.{strategy_name}")


def get_backtest_logger(strategy_name: str) -> logging.Logger:
    """
    Get a logger for backtesting a specific strategy.
    
    Args:
        strategy_name: Name of the strategy
        
    Returns:
        Logger for the backtest
    """
    return setup_logger(f"stacking_sats.backtest.{strategy_name}") 