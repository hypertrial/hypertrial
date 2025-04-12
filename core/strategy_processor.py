#!/usr/bin/env python3
"""
Strategy processing and execution functionality for the Hypertrial framework.
"""
import logging
import core.strategies  # Import the module explicitly for patching
from core.config import BACKTEST_START
from core.spd import backtest_dynamic_dca, compute_spd_metrics, standalone_plot_comparison
from core.plots import plot_price_vs_lookback_avg, plot_final_weights, plot_weight_sums_by_cycle
from core.spd_checks import check_strategy_submission_ready
from core.strategy_loader import load_strategy_from_file, find_strategy_class

# Configure logging
logger = logging.getLogger(__name__)

def process_single_strategy(btc_df, strategy_name=None, strategy_file=None, show_plots=True, save_plots=False, output_dir='results', standalone=False, validate=True):
    """
    Process a single strategy - either from name or file.
    
    Args:
        btc_df (pd.DataFrame): Bitcoin price dataframe
        strategy_name (str, optional): Name of a registered strategy
        strategy_file (str, optional): Path to a strategy file
        show_plots (bool): Whether to show plots
        save_plots (bool): Whether to save plots to files
        output_dir (str): Directory to save results
        standalone (bool): Whether to run in standalone mode
        validate (bool): Whether to validate strategy against submission criteria (True by default)
    """
    strategy_fn = None
    strategy_class = None
    
    # Load strategy from file if provided
    if strategy_file:
        strategy_name, strategy_fn, strategy_class = load_strategy_from_file(strategy_file)
        if not strategy_fn:
            return  # Error already logged
    # Otherwise, load registered strategy by name
    else:
        try:
            # Get the requested strategy with security checks
            strategy_fn = core.strategies.get_strategy(strategy_name)
            # Find the strategy class
            strategy_class = find_strategy_class(strategy_name)
        except ValueError as e:
            logger.error(f"Strategy not found: {strategy_name}")
            logger.error("Available strategies:")
            for name in core.strategies.list_strategies():
                logger.error(f" - {name}")
            return
    
    # Prepare features for visualization
    if strategy_class:
        # Use the strategy class's construct_features method if available
        df_features = strategy_class.construct_features(btc_df).loc[BACKTEST_START:]
    else:
        # Generic preprocessing for basic plotting - no strategy-specific features
        df_features = btc_df.copy().loc[BACKTEST_START:]
        
    # Compute weights using the strategy function with security checks
    weights = strategy_fn(btc_df)

    # Run validation checks if requested
    if validate:
        logger.info(f"Validating strategy '{strategy_name}' against submission criteria...")
        is_valid = check_strategy_submission_ready(btc_df, strategy_name)
        if not is_valid:
            logger.warning(f"Strategy '{strategy_name}' validation failed")
        else:
            logger.info(f"Strategy '{strategy_name}' passed all validation checks")

    # Plot results only if not disabled
    from core.plots import print_weight_sums_by_cycle  # Import here to be used in both cases
    
    if show_plots:
        # Pass the full features dataframe to the plot functions
        # Each plot function should extract only the features it needs
        try:
            plot_price_vs_lookback_avg(df_features, weights=weights)
        except ValueError as e:
            logger.warning(f"Could not plot price vs moving average: {str(e)}")
            logger.warning("Only strategies that calculate moving average features can use this plot.")
            
        plot_final_weights(weights)
        plot_weight_sums_by_cycle(weights)
    else:
        # Still print the weight sums even if plots are disabled
        print_weight_sums_by_cycle(weights)

    # Run SPD backtest and plot results with security checks
    if standalone and strategy_file:
        # In standalone mode, only compute SPD for the specified strategy
        # Print numeric results
        result = compute_spd_metrics(btc_df, weights, strategy_name=strategy_name)
        print(f"\nSPD Metrics for {strategy_name}:")
        print("Dynamic SPD:")
        print(f"  min: {result['min_spd']:.2f}")
        print(f"  max: {result['max_spd']:.2f}")
        print(f"  mean: {result['mean_spd']:.2f}")
        print(f"  median: {result['median_spd']:.2f}")
        
        print("\nExcess SPD Percentile Difference (Dynamic - Uniform) per Cycle:")
        for cycle, excess_pct in result['excess_pct_by_cycle'].items():
            print(f"  {cycle}: {excess_pct:.2f}%")
        
        print(f"\nMean Excess Percentile: {result['mean_excess_pct']:.2f}%")
        
        # Generate plots if not disabled
        if show_plots:
            standalone_plot_comparison(btc_df, weights, strategy_name=strategy_name,
                                       save_to_file=save_plots, output_dir=output_dir)
    else:
        # Regular mode: run comparison against uniform DCA
        backtest_dynamic_dca(btc_df, strategy_name=strategy_name, show_plots=show_plots) 