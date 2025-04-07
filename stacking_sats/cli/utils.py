"""
Utility functions for the CLI.
"""
from typing import Dict, Any, List


def parse_strategy_params(param_strings: List[str]) -> Dict[str, Any]:
    """
    Parse strategy parameters from command line arguments.
    
    Args:
        param_strings: List of parameter strings in format 'name=value'
        
    Returns:
        Dictionary of parameter name-value pairs
    """
    params = {}
    for param_str in param_strings:
        if '=' not in param_str:
            continue
        key, value = param_str.split('=', 1)
        # Skip empty values
        if not value:
            continue
        # Try to convert to appropriate type
        try:
            # Try as int
            params[key] = int(value)
        except ValueError:
            try:
                # Try as float
                params[key] = float(value)
            except ValueError:
                # Boolean values
                if value.lower() in ('true', 'yes', 'y', '1'):
                    params[key] = True
                elif value.lower() in ('false', 'no', 'n', '0'):
                    params[key] = False
                else:
                    # Keep as string
                    params[key] = value
    return params


def print_spd_metrics(spd_metrics: Dict[str, Any]) -> None:
    """
    Print SPD metrics in a well-formatted way.
    
    Args:
        spd_metrics: Dictionary of SPD metrics
    """
    print("\nSPD Metrics:")
    print("-" * 40)
    print(f"Strategy SPD: {spd_metrics['strategy_spd']:.2f} sats/dollar")
    print(f"Uniform DCA SPD: {spd_metrics['uniform_spd']:.2f} sats/dollar")
    print(f"Min SPD (highest price): {spd_metrics['min_spd']:.2f} sats/dollar")
    print(f"Max SPD (lowest price): {spd_metrics['max_spd']:.2f} sats/dollar")
    
    print(f"\nStrategy Percentile: {spd_metrics['strategy_percentile']:.2f}%")
    print(f"Uniform Percentile: {spd_metrics['uniform_percentile']:.2f}%")
    
    if spd_metrics['excess_percentile'] > 0:
        print(f"Strategy outperforms uniform DCA by: +{spd_metrics['excess_percentile']:.2f}%")
    else:
        print(f"Strategy underperforms uniform DCA by: {spd_metrics['excess_percentile']:.2f}%")
    
    # Print cycle-specific metrics
    print("\nPerformance by 4-Year Cycles:")
    print("-" * 40)
    for cycle, metrics in spd_metrics['cycles'].items():
        print(f"Cycle {cycle}:")
        print(f"  Strategy SPD: {metrics['strategy_spd']:.2f} sats/dollar ({metrics['strategy_percentile']:.2f}%)")
        print(f"  Uniform SPD: {metrics['uniform_spd']:.2f} sats/dollar ({metrics['uniform_percentile']:.2f}%)")
        
        excess = metrics['excess_percentile']
        if excess > 0:
            print(f"  Strategy outperforms by: +{excess:.2f}%")
        else:
            print(f"  Strategy underperforms by: {excess:.2f}%")
        print() 