"""
Dynamic Allocation Strategy based on price vs moving average.

This strategy implements a dynamic budget allocation approach that boosts
investment when price is below the 200-day moving average.
"""
import pandas as pd
import numpy as np
import logging
from stacking_sats.strategies.base_strategy import BaseStrategy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dynamic_strategy_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DynamicAllocationStrategy")

class DynamicAllocationStrategy(BaseStrategy):
    """
    Dynamic Allocation Strategy that invests more when price is below the 200-day MA.
    
    When price is below MA200, this strategy boosts the weight proportional to the z-score,
    and redistributes the excess over future days in the rebalancing window.
    """
    
    def __init__(self, 
                 alpha: float = 1.25,
                 rebalance_window: int = 365 * 2,
                 min_weight: float = 1e-4):
        """
        Initialize the strategy.
        
        Parameters:
            alpha (float): Boost factor multiplier based on z-score
            rebalance_window (int): Window (in days) over which redistribution is applied
            min_weight (float): Minimum allowable weight for any day
        """
        super().__init__(
            alpha=alpha,
            rebalance_window=rebalance_window,
            min_weight=min_weight
        )
        
        self.alpha = alpha
        self.rebalance_window = rebalance_window
        self.min_weight = min_weight
        
        logger.info(f"Strategy initialized with parameters: "
                   f"alpha={alpha}, rebalance_window={rebalance_window}, min_weight={min_weight}")
    
    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data by computing 200-day moving average and standard deviation.
        
        Parameters:
            data (pd.DataFrame): Raw price data with 'btc_close' column
            
        Returns:
            pd.DataFrame: Data with added features
        """
        logger.info(f"Original data shape: {data.shape}, date range: {data.index.min()} to {data.index.max()}")
        
        df = data.copy()
        
        # Ensure we have the price column
        if 'btc_close' not in df.columns:
            raise ValueError("Price column 'btc_close' not found in data")
        
        # Calculate moving average and standard deviation
        df['ma200'] = df['btc_close'].rolling(window=200, min_periods=1).mean()
        df['std200'] = df['btc_close'].rolling(window=200, min_periods=1).std()
        
        logger.info(f"Prepared data shape: {df.shape}, date range: {df.index.min()} to {df.index.max()}")
        
        return df
    
    def generate_weights(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate dynamic allocation weights using z-score based approach.
        
        When price is below MA200, boost the weight proportional to the z-score.
        Excess weight is redistributed evenly over future days in the rebalancing window,
        ensuring no weight falls below MIN_WEIGHT.
        
        Parameters:
            data (pd.DataFrame): Prepared data with features
            
        Returns:
            pd.Series: Series of weights indexed by date
        """
        # Initialize weights
        weights = pd.Series(0.0, index=data.index, dtype=float)
        
        logger.info(f"Generating weights for data with shape: {data.shape}")
        logger.info(f"Data date range: {data.index.min()} to {data.index.max()}")
        
        # Get starting year for cycle calculation
        start_year = data.index.min().year
        logger.info(f"Using start year for cycle calculation: {start_year}")
        
        # Create cycle labels for 4-year cycles
        cycle_labels = data.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        # Log cycle information
        for cycle_num, cycle_dates in cycle_labels.groupby(cycle_labels):
            cycle_start = cycle_dates.index.min()
            cycle_end = cycle_dates.index.max()
            logger.info(f"Cycle {cycle_num}: {cycle_start.strftime('%Y-%m-%d')} to {cycle_end.strftime('%Y-%m-%d')} "
                       f"({len(cycle_dates)} days)")
        
        # Process each cycle
        for cycle, group in data.groupby(cycle_labels):
            N = len(group)
            base_weight = 1.0 / N
            temp_weights = np.full(N, base_weight)
            strategy_active = True
            
            logger.info(f"Processing cycle {cycle}: {group.index.min().strftime('%Y-%m-%d')} to "
                       f"{group.index.max().strftime('%Y-%m-%d')} with {N} days")
            logger.info(f"Base weight for cycle {cycle}: {base_weight}")
            
            # Track total boost applied
            total_boost = 0
            total_excess = 0
            
            # Process each day in the cycle
            for i in range(N):
                if not strategy_active:
                    logger.info(f"Strategy deactivated for remaining days in cycle {cycle}")
                    break
                
                current_date = group.index[i]
                
                # Get price, MA, and std for the day
                price = group['btc_close'].iloc[i]
                ma200 = group['ma200'].iloc[i]
                std200 = group['std200'].iloc[i]
                
                # Apply boost only when price is below MA200
                if price < ma200 and std200 > 0:
                    # Calculate z-score
                    z = (ma200 - price) / std200
                    
                    # Apply boost multiplier
                    boost_multiplier = 1 + self.alpha * z
                    current_weight = temp_weights[i]
                    boosted_weight = current_weight * boost_multiplier
                    excess = boosted_weight - current_weight
                    
                    logger.debug(f"Date: {current_date.strftime('%Y-%m-%d')}, Price: {price}, MA200: {ma200}, "
                               f"Z-score: {z:.4f}, Boost: {boost_multiplier:.4f}, "
                               f"Original weight: {current_weight:.6f}, Boosted: {boosted_weight:.6f}")
                    
                    # Determine redistribution window
                    start_redistribution = max(N - self.rebalance_window, i + 1)
                    if start_redistribution >= N:
                        logger.debug(f"No redistribution possible - at end of cycle")
                        continue
                    
                    # Calculate redistribution
                    redistribution_idx = np.arange(start_redistribution, N)
                    if len(redistribution_idx) > 0:
                        reduction = excess / len(redistribution_idx)
                        projected = temp_weights[redistribution_idx] - reduction
                        
                        # Check if redistribution is feasible
                        if np.all(projected >= self.min_weight):
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
                                      f"redistribution would cause weights below minimum ({self.min_weight})")
            
            # Log cycle summary
            logger.info(f"Cycle {cycle} complete: Applied {total_boost} boosts with total excess of {total_excess:.6f}")
            logger.info(f"Final weights sum for cycle {cycle}: {temp_weights.sum():.6f}")
            
            # Check if weights sum to 1.0
            if not 0.999 <= temp_weights.sum() <= 1.001:
                logger.warning(f"Cycle {cycle} weights sum is not 1.0: {temp_weights.sum():.6f}")
            
            # Assign weights for this cycle to the main weights Series
            weights.loc[group.index] = temp_weights
        
        # Final validation
        total_weight_sum = weights.sum()
        logger.info(f"Total weights sum across all cycles: {total_weight_sum:.6f}")
        logger.info(f"Final weights shape: {weights.shape}")
        
        # Ensure all indices have weights (if any are zero, they weren't assigned in a cycle)
        if (weights == 0).any():
            zero_weight_days = weights[weights == 0].shape[0]
            if zero_weight_days > 0:
                logger.warning(f"Found {zero_weight_days} days with zero weight. Assigning minimum weight.")
                base_weight = (1.0 - weights.sum()) / zero_weight_days if zero_weight_days > 0 else 0
                if base_weight < self.min_weight:
                    base_weight = self.min_weight
                weights[weights == 0] = base_weight
                
                # Re-normalize to ensure sum is 1.0
                weights = weights / weights.sum()
        
        return weights 