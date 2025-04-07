"""
Core backtesting engine for the Stacking Sats library.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, Tuple
import matplotlib.pyplot as plt
from pathlib import Path
import os

class BacktestEngine:
    """
    A backtesting engine that runs user-defined strategies on historical price data.
    """
    
    def __init__(self, 
                 data: pd.DataFrame,
                 strategy: 'BaseStrategy',
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 initial_capital: float = 1000.0,
                 fee_pct: float = 0.0):
        """
        Initialize the backtesting engine.
        
        Parameters:
            data (pd.DataFrame): DataFrame with at least a price column
            strategy (BaseStrategy): Strategy instance to be tested
            start_date (str, optional): Start date for backtest period
            end_date (str, optional): End date for backtest period
            initial_capital (float): Starting capital
            fee_pct (float): Trading fee percentage
        """
        self.data = data.copy()
        if not isinstance(self.data.index, pd.DatetimeIndex):
            raise ValueError("Data must have a DatetimeIndex")
        
        # Filter data by date range if provided
        if start_date:
            self.data = self.data[self.data.index >= start_date]
        if end_date:
            self.data = self.data[self.data.index <= end_date]
            
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.fee_pct = fee_pct
        
        # Results
        self.weights = None
        self.position_values = None
        self.portfolio_value = None
        self.spd_metrics = {}
        
    def run(self) -> Dict[str, Any]:
        """
        Run the backtest using the provided strategy.
        
        Returns:
            Dict[str, Any]: Dictionary of backtest results
        """
        # Prepare the data with strategy-specific features
        prepared_data = self.strategy.prepare_data(self.data)
        
        # Generate allocation weights
        self.weights = self.strategy.generate_weights(prepared_data)
        
        # Calculate portfolio values 
        self._calculate_portfolio_values()
        
        # Calculate SPD metrics
        self._calculate_spd_metrics(prepared_data)
        
        return {
            'data': prepared_data,
            'weights': self.weights,
            'portfolio_value': self.portfolio_value,
            'spd_metrics': self.spd_metrics
        }
    
    def _calculate_portfolio_values(self):
        """
        Calculate portfolio values based on allocation weights.
        """
        # Ensure weights are properly aligned with data
        if not self.weights.index.equals(self.data.index):
            raise ValueError("Weight index does not match data index")
        
        # Calculate daily position values (weights * capital)
        self.position_values = self.weights * self.initial_capital
        
        # Apply fees when weight changes (rebalancing)
        weight_changes = self.weights.diff().abs()
        fee_costs = weight_changes * self.initial_capital * self.fee_pct
        
        # Calculate daily portfolio values
        self.portfolio_value = self.position_values.copy()
        self.portfolio_value = self.portfolio_value - fee_costs
    
    def _calculate_spd_metrics(self, data: pd.DataFrame):
        """
        Calculate SPD (Sats-Per-Dollar) metrics over 4-year investment cycles.
        
        This is a Bitcoin-specific metric that measures how many satoshis (1e-8 BTC)
        were acquired per dollar invested across different time periods.
        
        Parameters:
            data (pd.DataFrame): DataFrame with prepared data including 'btc_close'
        """
        if 'btc_close' not in data.columns:
            raise ValueError("Price column 'btc_close' not found in data for SPD calculation")
        
        # Create uniform weights for comparison
        uniform_weights = pd.Series(1/len(data), index=data.index)
        
        # Calculate SPD for the strategy
        strategy_spd = ((self.weights / data['btc_close']).sum()) * 1e8  # Convert to sats
        
        # Calculate SPD for uniform DCA
        uniform_spd = ((uniform_weights / data['btc_close']).sum()) * 1e8
        
        # Calculate min and max SPD (best and worst case scenarios)
        min_spd = (1 / data['btc_close'].max()) * 1e8  # Worst case: buying at highest price
        max_spd = (1 / data['btc_close'].min()) * 1e8  # Best case: buying at lowest price
        
        # Calculate percentiles to show where the strategy falls between extremes
        uniform_pct = (uniform_spd - min_spd) / (max_spd - min_spd) * 100 if max_spd > min_spd else 0
        strategy_pct = (strategy_spd - min_spd) / (max_spd - min_spd) * 100 if max_spd > min_spd else 0
        
        # Calculate excess SPD (how much better the strategy is compared to uniform DCA)
        excess_spd = strategy_spd - uniform_spd
        excess_pct = strategy_pct - uniform_pct
        
        # Cycle-based analysis (4-year Bitcoin cycles)
        cycle_metrics = self._calculate_cycle_spd_metrics(data)
        
        self.spd_metrics = {
            'strategy_spd': strategy_spd,
            'uniform_spd': uniform_spd,
            'min_spd': min_spd,
            'max_spd': max_spd,
            'strategy_percentile': strategy_pct,
            'uniform_percentile': uniform_pct,
            'excess_spd': excess_spd,
            'excess_percentile': excess_pct,
            'cycles': cycle_metrics
        }
    
    def _calculate_cycle_spd_metrics(self, data: pd.DataFrame) -> dict:
        """
        Calculate SPD metrics for each 4-year Bitcoin cycle.
        
        Parameters:
            data (pd.DataFrame): DataFrame with btc_close column
            
        Returns:
            dict: Dictionary with SPD metrics by cycle
        """
        # Determine cycle start
        start_year = data.index.min().year
        
        # Create cycle labels based on 4-year cycles
        cycle_labels = data.index.to_series().apply(lambda dt: (dt.year - start_year) // 4)
        
        cycle_results = {}
        
        # Process each cycle
        for cycle, group in data.groupby(cycle_labels):
            cycle_label = f"{group.index.min().year}–{group.index.max().year}"
            
            high, low = group['btc_close'].max(), group['btc_close'].min()
            min_spd = (1 / high) * 1e8  # Convert to sats (1 BTC = 100,000,000 sats)
            max_spd = (1 / low) * 1e8
            
            # Uniform DCA - equal weight each day
            uniform_weights = pd.Series(1/len(group), index=group.index)
            uniform_spd = ((uniform_weights / group['btc_close']).sum()) * 1e8
            
            # Strategy weights
            strategy_weights = self.weights.loc[group.index]
            strategy_spd = ((strategy_weights / group['btc_close']).sum()) * 1e8
            
            # Calculate percentiles
            uniform_pct = (uniform_spd - min_spd) / (max_spd - min_spd) * 100 if max_spd > min_spd else 0
            strategy_pct = (strategy_spd - min_spd) / (max_spd - min_spd) * 100 if max_spd > min_spd else 0
            excess_pct = strategy_pct - uniform_pct
            
            cycle_results[cycle_label] = {
                'min_spd': min_spd,
                'max_spd': max_spd,
                'uniform_spd': uniform_spd,
                'strategy_spd': strategy_spd,
                'uniform_percentile': uniform_pct,
                'strategy_percentile': strategy_pct,
                'excess_percentile': excess_pct
            }
            
        return cycle_results
        
    def plot_weights(self):
        """
        Plot only the allocation weights.
        """
        if self.weights is None:
            raise ValueError("Weights not calculated. Run backtest first.")
            
        plt.figure(figsize=(12, 6))
        self.weights.plot(title='Allocation Weights')
        plt.ylabel('Weight')
        plt.xlabel('Date')
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        
    def plot_spd_metrics(self):
        """
        Plot SPD metrics and percentiles by cycle.
        """
        if not hasattr(self, 'spd_metrics') or not self.spd_metrics:
            raise ValueError("SPD metrics not calculated. Run backtest first.")
        
        # Get metrics from the cycles
        cycles = list(self.spd_metrics['cycles'].keys())
        
        # Create figure
        fig, ax1 = plt.subplots(figsize=(12, 6))
        ax1.set_yscale('log')
        
        # X-axis positions
        x = np.arange(len(cycles))
        
        # Get metrics for each cycle
        min_spd = [self.spd_metrics['cycles'][c]['min_spd'] for c in cycles]
        max_spd = [self.spd_metrics['cycles'][c]['max_spd'] for c in cycles]
        uniform_spd = [self.spd_metrics['cycles'][c]['uniform_spd'] for c in cycles]
        strategy_spd = [self.spd_metrics['cycles'][c]['strategy_spd'] for c in cycles]
        
        # Plot SPD values on log scale
        ax1.plot(x, min_spd, marker='o', label='Min SPD (High price)')
        ax1.plot(x, max_spd, marker='o', label='Max SPD (Low price)')
        ax1.plot(x, uniform_spd, marker='o', label='Uniform DCA SPD')
        ax1.plot(x, strategy_spd, marker='o', label='Strategy SPD')
        
        # If improvement is positive, show it in the title
        if self.spd_metrics['excess_percentile'] > 0:
            improvement = f"+{self.spd_metrics['excess_percentile']:.1f}%"
        else:
            improvement = f"{self.spd_metrics['excess_percentile']:.1f}%"
            
        ax1.set_title(f"Cycle SPD Comparison (Strategy outperforms by {improvement})")
        ax1.set_ylabel('Sats per Dollar (Log Scale)')
        ax1.set_xlabel("Cycle")
        ax1.grid(True, linestyle='--', linewidth=0.5)
        ax1.legend(loc='upper left')
        ax1.set_xticks(x)
        ax1.set_xticklabels(cycles)
        
        # Create second axis for percentiles
        ax2 = ax1.twinx()
        barw = 0.4
        
        # Get percentiles for each cycle
        uniform_pct = [self.spd_metrics['cycles'][c]['uniform_percentile'] for c in cycles]
        strategy_pct = [self.spd_metrics['cycles'][c]['strategy_percentile'] for c in cycles]
        
        # Plot percentile bars
        ax2.bar(x - barw/2, uniform_pct, width=barw, alpha=0.3, label='Uniform Percentile')
        ax2.bar(x + barw/2, strategy_pct, width=barw, alpha=0.3, label='Strategy Percentile')
        ax2.set_ylabel('SPD Percentile (%)')
        ax2.set_ylim(0, 100)
        ax2.legend(loc='upper right')
        
        # Add text annotations for excess percentile for each cycle
        for i, cycle in enumerate(cycles):
            excess = self.spd_metrics['cycles'][cycle]['excess_percentile']
            if excess >= 0:
                text = f"+{excess:.1f}%"
                color = 'green'
            else:
                text = f"{excess:.1f}%"
                color = 'red'
                
            ax2.text(i, max(uniform_pct[i], strategy_pct[i]) + 5, 
                    text, ha='center', va='bottom', 
                    color=color, fontweight='bold',
                    bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2))
        
        plt.tight_layout()
        plt.show()
        
    def save_results(self, output_dir: str):
        """
        Save backtest results to files.
        
        Parameters:
            output_dir (str): Directory to save results
        """
        if self.portfolio_value is None:
            raise ValueError("Portfolio values not calculated. Run backtest first.")
            
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save results to CSV
        self.weights.to_csv(os.path.join(output_dir, 'weights.csv'))
        self.portfolio_value.to_csv(os.path.join(output_dir, 'portfolio_value.csv'))
        
        # Save SPD metrics (convert nested dict to DataFrame first)
        if hasattr(self, 'spd_metrics') and self.spd_metrics:
            # Save overall SPD metrics
            spd_overall = {k: v for k, v in self.spd_metrics.items() if k != 'cycles'}
            pd.Series(spd_overall).to_csv(os.path.join(output_dir, 'spd_metrics.csv'))
            
            # Save cycle-specific SPD metrics
            cycles_df = pd.DataFrame.from_dict(self.spd_metrics['cycles'], orient='index')
            cycles_df.to_csv(os.path.join(output_dir, 'spd_cycles.csv'))

def backtest(data: pd.DataFrame, 
             strategy: 'BaseStrategy',
             start_date: Optional[str] = None,
             end_date: Optional[str] = None,
             initial_capital: float = 1000.0,
             fee_pct: float = 0.0,
             plot: bool = True,
             plot_weights: bool = True,
             plot_spd: bool = True,
             save_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple function to run a backtest with minimal configuration.
    
    Parameters:
        data (pd.DataFrame): DataFrame with price data
        strategy (BaseStrategy): Strategy instance
        start_date (str, optional): Start date for backtest
        end_date (str, optional): End date for backtest
        initial_capital (float): Starting capital
        fee_pct (float): Trading fee percentage
        plot (bool): Whether to enable any plotting
        plot_weights (bool): Whether to plot allocation weights
        plot_spd (bool): Whether to plot SPD metrics
        save_dir (str, optional): Directory to save results
        
    Returns:
        Dict[str, Any]: Dictionary with backtest results
    """
    engine = BacktestEngine(
        data=data,
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
        fee_pct=fee_pct
    )
    
    results = engine.run()
    
    if plot:
        if plot_weights:
            engine.plot_weights()
    
        if plot_spd:
            engine.plot_spd_metrics()
        
    if save_dir:
        engine.save_results(save_dir)
        
    return results 