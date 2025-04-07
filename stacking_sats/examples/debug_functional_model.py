"""
Debug version of the functional dynamic allocation model with logging.
This file contains the same algorithm as the original model but with added logging
to help identify differences between implementations.
"""
import pandas as pd
import numpy as np
import logging
import os
import matplotlib.pyplot as plt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("functional_model_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FunctionalModel")

# -----------------------------------------------------------------------------
# GLOBAL CONFIGURATION
# -----------------------------------------------------------------------------
# Define the start and end dates for the backtest period
BACKTEST_START = '2013-01-01'
BACKTEST_END = '2024-12-31'

# Scaling factor for the boost based on the z-score
ALPHA = 1.25  # For each unit z, the weight is increased by 25%

# The window (in days) over which redistribution is applied
REBALANCE_WINDOW = 365 * 2  # Two years' worth of days

# Minimum allowable weight for any day to ensure no weight falls below this value
MIN_WEIGHT = 1e-4         

logger.info(f"Model initialized with parameters: start={BACKTEST_START}, end={BACKTEST_END}, "
           f"alpha={ALPHA}, rebalance_window={REBALANCE_WINDOW}, min_weight={MIN_WEIGHT}")

# -----------------------------------------------------------------------------
# 1) Feature Construction Function: construct_features
# -----------------------------------------------------------------------------
def construct_features(df):
    """
    Constructs additional features needed for the strategy.
    
    This function calculates:
      - The 200-day moving average ('ma200') of btc_close.
      - The 200-day rolling standard deviation ('std200') of btc_close.
    
    Parameters:
        df (pd.DataFrame): DataFrame with at least a 'btc_close' column.
    
    Returns:
        pd.DataFrame: A new DataFrame including the original data and the computed features.
    """
    logger.info(f"Original data shape: {df.shape}, date range: {df.index.min()} to {df.index.max()}")
    
    # Create a copy of the DataFrame to avoid modifying the original data
    df = df.copy()
    
    # Calculate the 200-day moving average of the 'btc_close' price.
    df['ma200'] = df['btc_close'].rolling(window=200, min_periods=1).mean()
    
    # Calculate the 200-day rolling standard deviation of the 'btc_close' price.
    df['std200'] = df['btc_close'].rolling(window=200, min_periods=1).std()
    
    return df

# -----------------------------------------------------------------------------
# 2) Dynamic Budget Allocation Function:
#    Implements a constrained early bias rebalancing strategy using a z-score.
# -----------------------------------------------------------------------------
def dynamic_budget_allocation(df):
    """
    Allocates dynamic weights based on a constrained early bias rebalancing strategy.
    
    For each cycle (defined as a 4-year period starting from the backtest start year), 
    the function adjusts the weights for each day. If the current price is below its 
    200-day moving average, it calculates the z-score:
    
        z = (ma200 - price) / std200
        
    and then computes a boost multiplier:
    
        boost_multiplier = 1 + ALPHA * z
    
    The boosted weight is then derived by multiplying the current weight with this 
    multiplier. The excess weight (boosted_weight - current_weight) is redistributed 
    evenly over the future days in the rebalancing window, ensuring that no day's 
    weight falls below MIN_WEIGHT.
    
    Parameters:
        df (pd.DataFrame): DataFrame with required features (e.g., 'btc_close', 'ma200', 'std200').
    
    Returns:
        pd.Series: A Series containing the dynamically allocated weights for each day.
    """
    logger.info(f"Generating weights for data with shape: {df.shape}")
    logger.info(f"Data date range: {df.index.min()} to {df.index.max()}")
    
    # Initialize an empty Series to store the final weights with the same index as the input DataFrame
    weights = pd.Series(index=df.index, dtype=float)
    
    # Determine the starting year from the backtest start date for cycle calculation
    start_year = pd.to_datetime(BACKTEST_START).year
    logger.info(f"Using start year for cycle calculation: {start_year}")
    
    # Create cycle labels for grouping: each cycle spans 4 years.
    cycle_labels = df.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    
    # Log cycle information
    for cycle_num, cycle_dates in cycle_labels.groupby(cycle_labels):
        cycle_start = cycle_dates.index.min()
        cycle_end = cycle_dates.index.max()
        logger.info(f"Cycle {cycle_num}: {cycle_start.strftime('%Y-%m-%d')} to {cycle_end.strftime('%Y-%m-%d')} "
                   f"({len(cycle_dates)} days)")
    
    # Iterate through each cycle group based on the calculated labels
    for cycle, group in df.groupby(cycle_labels):
        N = len(group)  # Total number of days in the current cycle
        base_weight = 1.0 / N  # Initial equal weight for each day in the cycle
        temp_weights = np.full(N, base_weight)  # Create an array of weights for the cycle
        
        logger.info(f"Processing cycle {cycle}: {group.index.min().strftime('%Y-%m-%d')} to "
                   f"{group.index.max().strftime('%Y-%m-%d')} with {N} days")
        logger.info(f"Base weight for cycle {cycle}: {base_weight}")
        
        # Track total boost applied
        total_boost = 0
        total_excess = 0
        
        # This flag controls whether the boosting strategy is active.
        # Once the feasibility check fails for a day, further boosting attempts will be stopped.
        strategy_active = True

        # Loop over each day in the current cycle to evaluate and adjust weights
        for i in range(N):
            if not strategy_active:
                logger.info(f"Strategy deactivated for remaining days in cycle {cycle}")
                break

            current_date = group.index[i]
            price = group['btc_close'].iloc[i]
            ma200 = group['ma200'].iloc[i]
            std200 = group['std200'].iloc[i]
            
            # Only attempt to boost if the price is below MA200 and we have a valid std deviation
            if price < ma200 and std200 > 0:
                # Compute the z-score for how much cheaper the price is compared to MA200
                z = (ma200 - price) / std200
                # Calculate the boost multiplier based on the z-score
                boost_multiplier = 1 + ALPHA * z
                current_weight = temp_weights[i]
                boosted_weight = current_weight * boost_multiplier
                excess = boosted_weight - current_weight

                logger.debug(f"Date: {current_date.strftime('%Y-%m-%d')}, Price: {price}, MA200: {ma200}, "
                           f"Z-score: {z:.4f}, Boost: {boost_multiplier:.4f}, "
                           f"Original weight: {current_weight:.6f}, Boosted: {boosted_weight:.6f}")

                # Determine the start index for redistribution.
                # Redistribution applies to future days, starting from day i+1 up to the REBALANCE_WINDOW limit.
                start_redistribution = max(N - REBALANCE_WINDOW, i + 1)
                if start_redistribution >= N:
                    logger.debug(f"No redistribution possible - at end of cycle")
                    continue

                redistribution_idx = np.arange(start_redistribution, N)
                if len(redistribution_idx) > 0:
                    reduction = excess / len(redistribution_idx)
                    projected = temp_weights[redistribution_idx] - reduction

                    if np.all(projected >= MIN_WEIGHT):
                        temp_weights[i] = boosted_weight
                        temp_weights[redistribution_idx] -= reduction
                        
                        total_boost += 1
                        total_excess += excess
                        
                        if i % 20 == 0:  # Log every 20th boost to avoid excessive logging
                            logger.debug(f"Applied boost: {current_date.strftime('%Y-%m-%d')}, "
                                       f"Boosted weight: {boosted_weight:.6f}, "
                                       f"Redistributed {excess:.6f} over {len(redistribution_idx)} days")
                    else:
                        strategy_active = False
                        logger.info(f"Strategy deactivated at {current_date.strftime('%Y-%m-%d')} - "
                                  f"redistribution would cause weights below minimum ({MIN_WEIGHT})")

        # Log cycle summary
        logger.info(f"Cycle {cycle} complete: Applied {total_boost} boosts with total excess of {total_excess:.6f}")
        logger.info(f"Final weights sum for cycle {cycle}: {temp_weights.sum():.6f}")
        
        # Check if weights sum to 1.0
        if not 0.999 <= temp_weights.sum() <= 1.001:
            logger.warning(f"Cycle {cycle} weights sum is not 1.0: {temp_weights.sum():.6f}")

        weights.loc[group.index] = temp_weights

    # Final validation
    total_weight_sum = weights.sum()
    logger.info(f"Total weights sum across all cycles: {total_weight_sum:.6f}")
    logger.info(f"Final weights shape: {weights.shape}")

    return weights

# -----------------------------------------------------------------------------
# 3) Dynamic Rule Causal Function: dynamic_rule_causal
# -----------------------------------------------------------------------------
def dynamic_rule_causal(df):
    """
    Orchestrates the dynamic strategy by constructing features, limiting the DataFrame 
    to the backtest period, and then applying the dynamic budget allocation strategy.
    
    Parameters:
        df (pd.DataFrame): Original DataFrame containing the 'btc_close' column.
    
    Returns:
        pd.Series: A Series of dynamically allocated weights corresponding to the backtest period.
    """
    logger.info("Starting dynamic_rule_causal execution")
    logger.info(f"Original data shape: {df.shape}, date range: {df.index.min()} to {df.index.max()}")
    
    df_features = construct_features(df)
    logger.info(f"Features constructed, data shape: {df_features.shape}")
    
    df_features = df_features.loc[BACKTEST_START:BACKTEST_END]
    logger.info(f"Data filtered to backtest period: {df_features.shape}, "
               f"from {df_features.index.min()} to {df_features.index.max()}")
    
    weights = dynamic_budget_allocation(df_features)
    logger.info(f"Weights generated: {weights.shape}")
    
    return weights

# Function to compare outputs from both implementations
def compare_weights(class_weights, functional_weights):
    """
    Compare weights from class-based and functional implementations to identify differences.
    
    Parameters:
        class_weights (pd.Series): Weights from class-based implementation
        functional_weights (pd.Series): Weights from functional implementation
    """
    logger.info("=== WEIGHT COMPARISON ===")
    
    # Check if indices match
    if not class_weights.index.equals(functional_weights.index):
        logger.warning("Weight indices do not match!")
        logger.info(f"Class weights: {class_weights.index.min()} to {class_weights.index.max()}, {len(class_weights)} entries")
        logger.info(f"Functional weights: {functional_weights.index.min()} to {functional_weights.index.max()}, {len(functional_weights)} entries")
        
        # Align indices for further comparison
        common_index = class_weights.index.intersection(functional_weights.index)
        logger.info(f"Common dates: {len(common_index)} entries")
        
        if len(common_index) > 0:
            class_weights = class_weights.loc[common_index]
            functional_weights = functional_weights.loc[common_index]
    
    # Check overall statistics
    logger.info(f"Class weights sum: {class_weights.sum():.6f}")
    logger.info(f"Functional weights sum: {functional_weights.sum():.6f}")
    
    # Check differences
    diff = class_weights - functional_weights
    max_diff = diff.abs().max()
    logger.info(f"Maximum absolute difference: {max_diff:.6f}")
    
    # Check cycle-wise differences
    start_year = pd.to_datetime(BACKTEST_START).year
    cycle_labels = class_weights.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    
    for cycle, group in cycle_labels.groupby(cycle_labels):
        cycle_dates = group.index
        cycle_class_sum = class_weights.loc[cycle_dates].sum()
        cycle_func_sum = functional_weights.loc[cycle_dates].sum()
        cycle_diff = cycle_class_sum - cycle_func_sum
        logger.info(f"Cycle {cycle} weight sum difference: {cycle_diff:.6f} "
                   f"(Class: {cycle_class_sum:.6f}, Func: {cycle_func_sum:.6f})")
    
    # Plot differences
    plt.figure(figsize=(12, 8))
    
    plt.subplot(311)
    class_weights.plot(label='Class weights')
    plt.title('Class-based Implementation Weights')
    plt.grid(True, linestyle='--', alpha=0.5)
    
    plt.subplot(312)
    functional_weights.plot(label='Functional weights')
    plt.title('Functional Implementation Weights')
    plt.grid(True, linestyle='--', alpha=0.5)
    
    plt.subplot(313)
    diff.plot(label='Difference')
    plt.title('Weight Difference (Class - Functional)')
    plt.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('weight_comparison.png')
    
    # Return summary information
    return {
        'max_diff': max_diff,
        'class_sum': class_weights.sum(),
        'func_sum': functional_weights.sum(),
        'diff_sum': diff.sum(),
        'num_different': (diff.abs() > 1e-8).sum()
    }

# Main execution function
def main(btc_df):
    """
    Main function to run both implementations and compare results.
    
    Parameters:
        btc_df (pd.DataFrame): Bitcoin price data with 'btc_close' column
    """
    logger.info("=== STARTING COMPARISON RUN ===")
    
    # Run functional implementation
    logger.info("Running functional implementation")
    functional_weights = dynamic_rule_causal(btc_df)
    
    logger.info("=== FUNCTIONAL IMPLEMENTATION COMPLETE ===")
    logger.info(f"Functional weights: shape={functional_weights.shape}, "
              f"sum={functional_weights.sum():.6f}")
    
    return functional_weights

if __name__ == "__main__":
    # This would be run manually after the class implementation is executed
    logger.info("This module is designed to be imported and used for comparison") 