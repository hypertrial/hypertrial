"""
Tests for the command-line interface.
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from stacking_sats.cli.main import main
from stacking_sats.cli.utils import parse_strategy_params


def test_parse_strategy_params():
    """Test parsing strategy parameters from command line arguments."""
    # Test integer parameters
    params = parse_strategy_params(["alpha=5", "beta=10"])
    assert params == {"alpha": 5, "beta": 10}
    
    # Test float parameters
    params = parse_strategy_params(["alpha=0.5", "beta=1.5"])
    assert params == {"alpha": 0.5, "beta": 1.5}
    
    # Test string parameters
    params = parse_strategy_params(["name=test", "mode=aggressive"])
    assert params == {"name": "test", "mode": "aggressive"}
    
    # Test boolean parameters
    params = parse_strategy_params(["active=true", "enabled=yes", "disabled=false", "visible=no"])
    assert params == {"active": True, "enabled": True, "disabled": False, "visible": False}
    
    # Test mixed parameter types
    params = parse_strategy_params(["alpha=0.5", "count=10", "name=test", "active=true"])
    assert params == {"alpha": 0.5, "count": 10, "name": "test", "active": True}
    
    # Test empty parameters
    params = parse_strategy_params([])
    assert params == {}
    
    # Test malformed parameters
    params = parse_strategy_params(["alpha", "beta="])
    assert params == {}


@patch("stacking_sats.cli.main.get_available_strategies")
def test_cli_list_strategies(mock_get_strategies):
    """Test CLI listing available strategies."""
    # Setup the mock
    mock_get_strategies.return_value = ["DynamicAllocationStrategy", "StaticAllocationStrategy"]
    
    # Call CLI with --list-strategies
    with patch("sys.stdout") as mock_stdout:
        exit_code = main(["--list-strategies"])
        
    # Check that get_available_strategies was called
    mock_get_strategies.assert_called_once()
    
    # Check that it printed the strategies
    captured_output = mock_stdout.mock_calls
    assert len(captured_output) > 0
    
    # Check exit code
    assert exit_code == 0


@patch("stacking_sats.cli.main.load_btc_data")
@patch("stacking_sats.cli.main.load_strategy")
@patch("stacking_sats.cli.main.backtest")
def test_cli_run_backtest(mock_backtest, mock_load_strategy, mock_load_data):
    """Test CLI running a backtest."""
    # Setup the mocks
    mock_load_data.return_value = MagicMock()
    mock_strategy = MagicMock()
    mock_load_strategy.return_value = mock_strategy
    mock_backtest.return_value = {
        'spd_metrics': {
            'strategy_spd': 100.0,
            'uniform_spd': 90.0,
            'min_spd': 50.0,
            'max_spd': 150.0,
            'strategy_percentile': 50.0,
            'uniform_percentile': 40.0,
            'excess_percentile': 10.0,
            'cycles': {}
        }
    }
    
    # Call CLI with strategy and parameters
    args = [
        "DynamicAllocationStrategy",
        "--param", "alpha=1.5",
        "--start-date", "2020-01-01",
        "--end-date", "2021-01-01",
        "--capital", "10000",
        "--no-plot"
    ]
    
    with patch("stacking_sats.cli.main.print_spd_metrics") as mock_print:
        exit_code = main(args)
    
    # Check that all functions were called with correct arguments
    mock_load_data.assert_called_once()
    mock_load_strategy.assert_called_once_with("DynamicAllocationStrategy", alpha=1.5)
    mock_backtest.assert_called_once()
    backtest_kwargs = mock_backtest.call_args.kwargs
    assert backtest_kwargs["start_date"] == "2020-01-01"
    assert backtest_kwargs["end_date"] == "2021-01-01"
    assert backtest_kwargs["initial_capital"] == 10000.0
    assert backtest_kwargs["plot"] is False
    
    # Check that SPD metrics were printed
    mock_print.assert_called_once()
    
    # Check exit code
    assert exit_code == 0


@patch("stacking_sats.cli.main.load_btc_data")
def test_cli_data_error(mock_load_data):
    """Test CLI handling data loading errors."""
    # Setup the mock to raise an exception
    mock_load_data.side_effect = Exception("Mock data error")
    
    # Call CLI with strategy
    args = ["DynamicAllocationStrategy"]
    
    # Check that it returns an error code
    exit_code = main(args)
    assert exit_code == 1 