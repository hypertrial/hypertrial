"""
Run comparison between class-based and functional implementations of the
dynamic allocation strategy to identify differences in results.
"""
import pandas as pd
import numpy as np
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path so we can import our modules
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import the implementations to compare
from stacking_sats.core.data_loader import load_btc_data
from stacking_sats.strategies.examples.dynamic_allocation_strategy import DynamicAllocationStrategy
from stacking_sats.examples.debug_functional_model import dynamic_rule_causal, compare_weights

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("comparison_run.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ComparisonRun")

def run_comparison():
    """
    Run and compare both implementations of the dynamic allocation strategy.
    """
    logger.info("=== STARTING IMPLEMENTATION COMPARISON ===")
    
    # Load data
    logger.info("Loading Bitcoin price data")
    try:
        btc_df = load_btc_data()
        logger.info(f"Data loaded successfully: {btc_df.shape} rows, from {btc_df.index.min()} to {btc_df.index.max()}")
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        print(f"Error loading data: {e}")
        return
    
    # Run class-based implementation
    logger.info("Running class-based implementation")
    strategy = DynamicAllocationStrategy()
    prepared_data = strategy.prepare_data(btc_df)
    class_weights = strategy.generate_weights(prepared_data)
    logger.info(f"Class-based weights generated: {class_weights.shape}")
    
    # Run functional implementation
    logger.info("Running functional implementation")
    functional_weights = dynamic_rule_causal(btc_df)
    logger.info(f"Functional weights generated: {functional_weights.shape}")
    
    # Compare results
    logger.info("Comparing implementation results")
    comparison_result = compare_weights(class_weights, functional_weights)
    
    # Print summary
    logger.info("=== COMPARISON SUMMARY ===")
    for key, value in comparison_result.items():
        logger.info(f"{key}: {value}")
    
    # Print very detailed cycle-by-cycle comparison for the last cycle (which showed the largest difference)
    start_year = pd.to_datetime('2013-01-01').year
    cycle_labels = class_weights.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
    
    # Identify the last cycle (typically the 2021-2024 cycle that showed the issue)
    last_cycle = max(cycle_labels.unique())
    logger.info(f"Detailed analysis of cycle {last_cycle}:")
    
    last_cycle_dates = cycle_labels[cycle_labels == last_cycle].index
    class_cycle_weights = class_weights.loc[last_cycle_dates]
    func_cycle_weights = functional_weights.loc[last_cycle_dates]
    
    # Get stats on the weight differences
    diff = class_cycle_weights - func_cycle_weights
    max_idx = diff.abs().idxmax()
    logger.info(f"Max difference at date: {max_idx}, difference: {diff[max_idx]:.8f}")
    logger.info(f"Class weight: {class_cycle_weights[max_idx]:.8f}, Func weight: {func_cycle_weights[max_idx]:.8f}")
    
    # Print first few days where the strategies activate their boosting
    active_days = (diff != 0)
    first_active_day = active_days[active_days].index.min() if active_days.any() else None
    
    if first_active_day:
        logger.info(f"First day with weight difference: {first_active_day}")
        
        # Print a window of days around the first difference
        start_idx = max(0, active_days.index.get_loc(first_active_day) - 5)
        end_idx = min(len(active_days), active_days.index.get_loc(first_active_day) + 10)
        comparison_days = active_days.index[start_idx:end_idx]
        
        # Create comparison table
        comparison_data = []
        for day in comparison_days:
            price = prepared_data.loc[day, 'btc_close']
            ma200 = prepared_data.loc[day, 'ma200']
            std200 = prepared_data.loc[day, 'std200']
            z_score = (ma200 - price) / std200 if price < ma200 and std200 > 0 else 0
            
            comparison_data.append({
                'date': day,
                'price': price,
                'ma200': ma200,
                'std200': std200,
                'z_score': z_score,
                'class_weight': class_cycle_weights[day],
                'func_weight': func_cycle_weights[day],
                'diff': diff[day]
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        logger.info("\nComparison around first difference:")
        logger.info(comparison_df.to_string())
    
    logger.info("=== COMPARISON COMPLETE ===")
    return comparison_result

if __name__ == "__main__":
    run_comparison() 