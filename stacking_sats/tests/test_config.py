"""
Tests for the configuration management system.
"""
import os
import pytest

from stacking_sats.core.config.config_manager import ConfigManager


def test_config_init(temp_config_dir):
    """Test ConfigManager initialization."""
    # Initialize with custom directory
    config = ConfigManager(config_dir=temp_config_dir)
    
    # Check that config file was created
    assert os.path.exists(os.path.join(temp_config_dir, "config.yaml"))
    
    # Check default config values
    assert config.get("backtest", "default_initial_capital") == 1000.0
    assert config.get("data", "source") == "local"


def test_config_set_get(temp_config_dir):
    """Test setting and getting config values."""
    config = ConfigManager(config_dir=temp_config_dir)
    
    # Set and get a value
    config.set("backtest", "default_initial_capital", 5000.0)
    assert config.get("backtest", "default_initial_capital") == 5000.0
    
    # Create a new section
    config.set("test_section", "test_key", "test_value")
    assert config.get("test_section", "test_key") == "test_value"
    
    # Test getting entire section
    backtest_config = config.get("backtest")
    assert isinstance(backtest_config, dict)
    assert backtest_config["default_initial_capital"] == 5000.0


def test_config_persistence(temp_config_dir):
    """Test that config changes persist."""
    # Create and modify config
    config1 = ConfigManager(config_dir=temp_config_dir)
    config1.set("data", "source", "remote")
    
    # Create a new instance and check that changes persisted
    config2 = ConfigManager(config_dir=temp_config_dir)
    assert config2.get("data", "source") == "remote"


def test_strategy_config(temp_config_dir):
    """Test strategy-specific configuration."""
    config = ConfigManager(config_dir=temp_config_dir)
    
    # Save strategy config
    strategy_params = {
        "alpha": 1.5,
        "min_weight": 0.0002,
        "max_weight": 0.05
    }
    config.save_strategy_config("TestStrategy", strategy_params)
    
    # Get strategy config
    retrieved_params = config.get_strategy_config("TestStrategy")
    assert retrieved_params == strategy_params
    
    # Non-existent strategy should return empty dict
    assert config.get_strategy_config("NonExistentStrategy") == {}


def test_reset_to_defaults(temp_config_dir):
    """Test resetting config to defaults."""
    # Create first config instance
    config1 = ConfigManager(config_dir=temp_config_dir)
    
    # Modify config
    config1.set("backtest", "default_initial_capital", 5000.0)
    assert config1.get("backtest", "default_initial_capital") == 5000.0
    
    # Reset to defaults
    config1.reset_to_defaults()
    
    # Create a new instance to ensure changes were saved
    config2 = ConfigManager(config_dir=temp_config_dir)
    assert config2.get("backtest", "default_initial_capital") == 1000.0 