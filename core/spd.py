# spd.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from core.config import BACKTEST_START, BACKTEST_END
from core.strategies import get_strategy, list_strategies
import os
import logging

def compute_cycle_spd(df, strategy_name):
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()
    rows = []
    
    # Get the strategy function by name and pre-compute weights once
    weight_fn = get_strategy(strategy_name)
    full_weights = weight_fn(df).fillna(0).clip(lower=0)
    
    # Pre-calculate inverted prices multiplied by 1e8 for efficiency
    inverted_prices = (1 / df_backtest['btc_close']) * 1e8

    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        
        if cycle.empty:
            break

        cycle_label = f"{current.year}–{end_date.year}"
        
        # More efficient min/max calculation
        cycle_prices = cycle['btc_close'].values
        high, low = np.max(cycle_prices), np.min(cycle_prices)
        min_spd = (1 / high) * 1e8
        max_spd = (1 / low) * 1e8
        
        # Vectorized calculation of uniform SPD
        cycle_inverted = inverted_prices.loc[cycle.index]
        uniform_spd = cycle_inverted.mean()
        
        # Vectorized calculation of dynamic SPD
        w_slice = full_weights.loc[cycle.index]
        dynamic_spd = (w_slice * cycle_inverted).sum()
        
        # Calculate percentiles
        spd_range = max_spd - min_spd
        uniform_pct = (uniform_spd - min_spd) / spd_range * 100
        dynamic_pct = (dynamic_spd - min_spd) / spd_range * 100
        excess_pct = dynamic_pct - uniform_pct

        rows.append({
            'cycle': cycle_label,
            'min_spd': min_spd,
            'max_spd': max_spd,
            'uniform_spd': uniform_spd,
            'dynamic_spd': dynamic_spd,
            'uniform_pct': uniform_pct,
            'dynamic_pct': dynamic_pct,
            'excess_pct': excess_pct
        })

        current += cycle_length

    return pd.DataFrame(rows).set_index('cycle')

def plot_spd_comparison(df_res, strategy_name):
    x = np.arange(len(df_res.index))
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_yscale('log')
    
    # Plot all lines in one call for better performance
    lines = ax1.plot(
        x, df_res['min_spd'], 'o-',
        x, df_res['max_spd'], 'o-',
        x, df_res['uniform_spd'], 'o-',
        x, df_res['dynamic_spd'], 'o-'
    )
    
    # Set labels after plotting
    ax1.set_title(f"Uniform vs {strategy_name} DCA (SPD)")
    ax1.set_ylabel('Sats per Dollar (Log Scale)')
    ax1.set_xlabel("Cycle")
    ax1.grid(True, linestyle='--', linewidth=0.5)
    ax1.legend(lines, ['Min spd (High)', 'Max spd (Low)', 'Uniform DCA spd', f"{strategy_name} spd"], loc='upper left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df_res.index)

    ax2 = ax1.twinx()
    barw = 0.4
    
    # Call bar separately for each series instead of trying to pass lists of arrays
    bar1 = ax2.bar(x - barw/2, df_res['uniform_pct'], width=barw, alpha=0.3)
    bar2 = ax2.bar(x + barw/2, df_res['dynamic_pct'], width=barw, alpha=0.3)
    
    ax2.set_ylabel('SPD Percentile (%)')
    ax2.set_ylim(0, 100)
    ax2.legend([bar1, bar2], ['Uniform %', f"{strategy_name} %"], loc='upper right')

    plt.tight_layout()
    plt.show()

def backtest_dynamic_dca(df, strategy_name="dynamic_dca", show_plots=True):
    # Log backtest date range
    logger = logging.getLogger(__name__)
    logger.info(f"Running backtest from {BACKTEST_START} to {BACKTEST_END}")
    
    df_res = compute_cycle_spd(df, strategy_name)
    
    # Calculate metrics with vectorized operations
    dynamic_spd = df_res['dynamic_spd']
    dynamic_pct = df_res['dynamic_pct']
    
    dynamic_spd_metrics = {
        'min': dynamic_spd.min(),
        'max': dynamic_spd.max(),
        'mean': dynamic_spd.mean(),
        'median': dynamic_spd.median()
    }
    
    dynamic_pct_metrics = {
        'min': dynamic_pct.min(),
        'max': dynamic_pct.max(),
        'mean': dynamic_pct.mean(),
        'median': dynamic_pct.median()
    }

    print(f"\nAggregated Metrics for {strategy_name}:")
    print("Dynamic SPD:")
    for key, value in dynamic_spd_metrics.items():
        print(f"  {key}: {value:.2f}")
    print("Dynamic SPD Percentile:")
    for key, value in dynamic_pct_metrics.items():
        print(f"  {key}: {value:.2f}")

    print("\nExcess SPD Percentile Difference (Dynamic - Uniform) per Cycle:")
    for cycle, row in df_res.iterrows():
        print(f"  {cycle}: {row['excess_pct']:.2f}%")
    
    # Run SPD validation checks and store the results
    from core.spd_checks import check_strategy_submission_ready
    try:
        # Get validation results from spd_checks
        validation_results = check_strategy_submission_ready(df, strategy_name, return_details=True)
        
        # Add validation results to the dataframe as a new column
        for key, value in validation_results.items():
            df_res[key] = value
        
        # Display validation summary
        if validation_results['validation_passed']:
            print(f"\nStrategy '{strategy_name}' passed all validation checks.")
        else:
            print(f"\nStrategy '{strategy_name}' failed validation checks. See details in output CSV.")
    except Exception as e:
        logger.error(f"Error running validation checks: {str(e)}")
        # Set validation fields to default values in case of error
        df_res['validation_passed'] = False
        df_res['validation_error'] = str(e)

    if show_plots:
        plot_spd_comparison(df_res, strategy_name)
    
    return df_res

def list_available_strategies():
    """
    Print a list of all available strategies with their descriptions
    """
    strategies = list_strategies()
    
    if not strategies:
        print("\nNo strategies available. Please check your installation.")
        return strategies
    
    print("\nAvailable Strategies:")
    print("=====================")
    
    # Group by core and custom strategies
    core_strategies = {}
    custom_strategies = {}
    
    for name, description in strategies.items():
        if any(name.startswith(prefix) for prefix in ['dynamic_dca', 'uniform_dca']):
            core_strategies[name] = description
        else:
            custom_strategies[name] = description
    
    # Print core strategies
    if core_strategies:
        print("\nCore Strategies:")
        print("-----------------")
        for name, description in sorted(core_strategies.items()):
            print(f"  {name:20}: {description.split('.')[0] if description else 'No description'}")
    
    # Print custom strategies
    if custom_strategies:
        print("\nCustom Strategies:")
        print("------------------")
        for name, description in sorted(custom_strategies.items()):
            print(f"  {name:20}: {description.split('.')[0] if description else 'No description'}")
    
    return strategies

def compute_spd_metrics(df, weights, strategy_name="custom_strategy"):
    """
    Compute SPD metrics for a single strategy with comparison to uniform DCA
    
    Args:
        df (pd.DataFrame): Price data
        weights (pd.Series): Strategy weights
        strategy_name (str): Name of the strategy
        
    Returns:
        dict: SPD metrics including cycle comparisons with uniform DCA
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Computing SPD metrics for '{strategy_name}' from {BACKTEST_START} to {BACKTEST_END}")
    
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    weights = weights.fillna(0).clip(lower=0)
    
    # Pre-calculate inverted prices multiplied by 1e8 for efficiency
    inverted_prices = (1 / df_backtest['btc_close']) * 1e8
    
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()
    
    cycles = []
    min_spd_list = []
    max_spd_list = []
    uniform_spd_list = []
    dynamic_spd_list = []
    excess_pct_list = []
    
    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        
        if cycle.empty:
            break
            
        cycle_label = f"{current.year}–{end_date.year}"
        cycles.append(cycle_label)
        
        # Calculate cycle metrics
        cycle_prices = cycle['btc_close'].values
        high, low = np.max(cycle_prices), np.min(cycle_prices)
        min_spd = (1 / high) * 1e8
        max_spd = (1 / low) * 1e8
        
        # Calculate uniform SPD (equal weight for each day)
        cycle_inverted = inverted_prices.loc[cycle.index]
        uniform_spd = cycle_inverted.mean()
        
        # Calculate dynamic SPD for this cycle
        w_slice = weights.loc[cycle.index]
        dynamic_spd = (w_slice * cycle_inverted).sum()
        
        # Calculate percentiles
        spd_range = max_spd - min_spd
        uniform_pct = (uniform_spd - min_spd) / spd_range * 100
        dynamic_pct = (dynamic_spd - min_spd) / spd_range * 100
        excess_pct = dynamic_pct - uniform_pct
        
        min_spd_list.append(min_spd)
        max_spd_list.append(max_spd)
        uniform_spd_list.append(uniform_spd)
        dynamic_spd_list.append(dynamic_spd)
        excess_pct_list.append(excess_pct)
        
        current += cycle_length
    
    # Convert to arrays for calculations
    min_spd_array = np.array(min_spd_list)
    max_spd_array = np.array(max_spd_list)
    uniform_spd_array = np.array(uniform_spd_list)
    dynamic_spd_array = np.array(dynamic_spd_list)
    
    # Calculate dynamic percentiles
    spd_range_array = max_spd_array - min_spd_array
    uniform_pct_array = (uniform_spd_array - min_spd_array) / spd_range_array * 100
    dynamic_pct_array = (dynamic_spd_array - min_spd_array) / spd_range_array * 100
    
    # Calculate overall metrics
    metrics = {
        'min_spd': dynamic_spd_array.min(),
        'max_spd': dynamic_spd_array.max(),
        'mean_spd': dynamic_spd_array.mean(),
        'median_spd': np.median(dynamic_spd_array),
        'min_pct': dynamic_pct_array.min(),
        'max_pct': dynamic_pct_array.max(),
        'mean_pct': dynamic_pct_array.mean(),
        'median_pct': np.median(dynamic_pct_array),
        'cycles': cycles,
        'excess_pct_by_cycle': dict(zip(cycles, excess_pct_list)),
        'mean_excess_pct': np.mean(excess_pct_list),
        'uniform_spd': uniform_spd_list,
        'dynamic_spd': dynamic_spd_list,
        'uniform_pct': uniform_pct_array.tolist(),
        'dynamic_pct': dynamic_pct_array.tolist(),
        'excess_pct': excess_pct_list
    }
    
    return metrics

def standalone_plot_comparison(df, weights, strategy_name="custom_strategy", save_to_file=False, output_dir="results"):
    """
    Create a plot comparing the strategy with uniform DCA in standalone mode
    
    Args:
        df (pd.DataFrame): Price data
        weights (pd.Series): Strategy weights
        strategy_name (str): Name of the strategy
        save_to_file (bool): Whether to save the plot to a file
        output_dir (str): Directory to save the plot to
    
    Returns:
        pd.DataFrame: DataFrame with plot data
    """
    # Log backtest date range
    logger = logging.getLogger(__name__)
    logger.info(f"Running standalone backtest comparison from {BACKTEST_START} to {BACKTEST_END}")
    
    # Calculate metrics
    metrics = compute_spd_metrics(df, weights, strategy_name)
    
    # Create a DataFrame for plotting
    cycles = metrics['cycles']
    min_spd_list = []
    max_spd_list = []
    uniform_spd_list = []
    dynamic_spd_list = []
    uniform_pct_list = []
    dynamic_pct_list = []
    excess_pct_list = []
    
    # Extract data for each cycle
    df_backtest = df.loc[BACKTEST_START:BACKTEST_END]
    cycle_length = pd.DateOffset(years=4)
    current = df_backtest.index.min()
    
    while current <= df_backtest.index.max():
        cycle_end = current + cycle_length - pd.Timedelta(days=1)
        end_date = min(cycle_end, df_backtest.index.max())
        cycle_mask = (df_backtest.index >= current) & (df_backtest.index <= end_date)
        cycle = df_backtest.loc[cycle_mask]
        
        if cycle.empty:
            break
            
        # Calculate cycle metrics
        cycle_prices = cycle['btc_close'].values
        high, low = np.max(cycle_prices), np.min(cycle_prices)
        min_spd = (1 / high) * 1e8
        max_spd = (1 / low) * 1e8
        
        # Calculate uniform SPD (equal weight for each day)
        cycle_inverted = (1 / cycle['btc_close']) * 1e8
        uniform_spd = cycle_inverted.mean()
        
        # Calculate dynamic SPD for this cycle
        w_slice = weights.loc[cycle.index]
        dynamic_spd = (w_slice * cycle_inverted).sum()
        
        # Calculate percentiles
        spd_range = max_spd - min_spd
        uniform_pct = (uniform_spd - min_spd) / spd_range * 100
        dynamic_pct = (dynamic_spd - min_spd) / spd_range * 100
        excess_pct = dynamic_pct - uniform_pct
        
        min_spd_list.append(min_spd)
        max_spd_list.append(max_spd)
        uniform_spd_list.append(uniform_spd)
        dynamic_spd_list.append(dynamic_spd)
        uniform_pct_list.append(uniform_pct)
        dynamic_pct_list.append(dynamic_pct)
        excess_pct_list.append(excess_pct)
        
        current += cycle_length
    
    # Create DataFrame for plotting
    plot_data = pd.DataFrame({
        'cycle': cycles,
        'min_spd': min_spd_list,
        'max_spd': max_spd_list,
        'uniform_spd': uniform_spd_list,
        'dynamic_spd': dynamic_spd_list,
        'uniform_pct': uniform_pct_list,
        'dynamic_pct': dynamic_pct_list,
        'excess_pct': excess_pct_list
    }).set_index('cycle')
    
    # Create the plot
    x = np.arange(len(plot_data.index))
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.set_yscale('log')
    
    # Plot all lines in one call for better performance
    lines = ax1.plot(
        x, plot_data['min_spd'], 'o-',
        x, plot_data['max_spd'], 'o-',
        x, plot_data['uniform_spd'], 'o-',
        x, plot_data['dynamic_spd'], 'o-'
    )
    
    # Set labels after plotting
    ax1.set_title(f"Uniform vs {strategy_name} DCA (SPD)")
    ax1.set_ylabel('Sats per Dollar (Log Scale)')
    ax1.set_xlabel("Cycle")
    ax1.grid(True, linestyle='--', linewidth=0.5)
    ax1.legend(lines, ['Min spd (High)', 'Max spd (Low)', 'Uniform DCA spd', f"{strategy_name} spd"], loc='upper left')
    ax1.set_xticks(x)
    ax1.set_xticklabels(plot_data.index)

    ax2 = ax1.twinx()
    barw = 0.4
    
    # Call bar separately for each series instead of trying to pass lists of arrays
    bar1 = ax2.bar(x - barw/2, plot_data['uniform_pct'], width=barw, alpha=0.3)
    bar2 = ax2.bar(x + barw/2, plot_data['dynamic_pct'], width=barw, alpha=0.3)
    
    ax2.set_ylabel('SPD Percentile (%)')
    ax2.set_ylim(0, 100)
    ax2.legend([bar1, bar2], ['Uniform %', f"{strategy_name} %"], loc='upper right')

    plt.tight_layout()
    
    if save_to_file:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the plot
        plot_file = os.path.join(output_dir, f"{strategy_name}_vs_uniform_dca.png")
        plt.savefig(plot_file, dpi=100)
        print(f"\nPlot saved to: {plot_file}")
    else:
        # Only show the plot if not saving to file
        plt.show()
    
    return plot_data
