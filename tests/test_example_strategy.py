import unittest
import os
import sys
import pandas as pd
import numpy as np
import importlib.util
from pathlib import Path

# Suppress matplotlib output for testing
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
plt.ioff()  # Turn off interactive mode

# Function to import a module from a file path
def import_module_from_path(file_path, module_name="dynamic_module"):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class TestExampleStrategy(unittest.TestCase):
    """Test the example_strategy.py file in the tutorials directory."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Path to the example strategy
        cls.example_strategy_path = os.path.abspath("tutorials/example_strategy.py")
        
        # Verify the file exists
        if not os.path.exists(cls.example_strategy_path):
            raise FileNotFoundError(f"Example strategy file not found at {cls.example_strategy_path}")
        
        # Import the module
        cls.strategy_module = import_module_from_path(cls.example_strategy_path, "example_strategy")
        
        # Create a simple test DataFrame for testing
        date_range = pd.date_range(start='2013-01-01', end='2023-12-31', freq='D')
        cls.test_df = pd.DataFrame({
            'btc_close': np.random.normal(loc=10000, scale=5000, size=len(date_range))
        }, index=date_range)
        
        # Make sure the price is always positive
        cls.test_df['btc_close'] = cls.test_df['btc_close'].abs()
    
    def test_module_imports(self):
        """Test that the module can be imported successfully."""
        self.assertIsNotNone(self.strategy_module)
        self.assertTrue(hasattr(self.strategy_module, 'DynamicDCA10MAStrategy'))
        self.assertTrue(hasattr(self.strategy_module, 'dynamic_rule_causal_10ma'))
    
    def test_strategy_class(self):
        """Test the DynamicDCA10MAStrategy class."""
        strategy_class = self.strategy_module.DynamicDCA10MAStrategy
        
        # Test class methods
        self.assertTrue(hasattr(strategy_class, 'construct_features'))
        self.assertTrue(hasattr(strategy_class, 'compute_weights'))
        self.assertTrue(hasattr(strategy_class, 'get_strategy_function'))
    
    def test_construct_features(self):
        """Test the construct_features method."""
        strategy_class = self.strategy_module.DynamicDCA10MAStrategy
        
        # Call the method
        result_df = strategy_class.construct_features(self.test_df)
        
        # Check the result
        self.assertIsInstance(result_df, pd.DataFrame)
        self.assertIn('ma10', result_df.columns)
        self.assertIn('std10', result_df.columns)
        
        # Check that the original DataFrame is not modified
        self.assertNotIn('ma10', self.test_df.columns)
        self.assertNotIn('std10', self.test_df.columns)
    
    def test_compute_weights(self):
        """Test the compute_weights method."""
        strategy_class = self.strategy_module.DynamicDCA10MAStrategy
        
        # First construct features
        df_with_features = strategy_class.construct_features(self.test_df)
        
        # Call the method
        weights = strategy_class.compute_weights(df_with_features)
        
        # Check the result
        self.assertIsInstance(weights, pd.Series)
        self.assertEqual(len(weights), len(df_with_features.loc['2013-01-01':'2023-12-31']))
        
        # Check that weights sum to 1.0 for each cycle
        years = weights.index.year
        unique_years = years.unique()
        for start_year in range(2013, 2024, 4):
            if start_year in unique_years:
                cycle_years = [y for y in range(start_year, start_year + 4) if y in unique_years]
                cycle_mask = years.isin(cycle_years)
                cycle_sum = weights[cycle_mask].sum()
                self.assertAlmostEqual(cycle_sum, 1.0, places=4)
    
    def test_strategy_function(self):
        """Test the registered strategy function."""
        strategy_fn = self.strategy_module.dynamic_rule_causal_10ma
        
        # Call the function
        weights = strategy_fn(self.test_df)
        
        # Check the result
        self.assertIsInstance(weights, pd.Series)
        self.assertEqual(len(weights), len(self.test_df.loc['2013-01-01':'2023-12-31']))
        
        # Check that weights are all positive
        self.assertTrue((weights >= 0).all())
        
        # Check that weights sum to 1.0 for each cycle
        years = weights.index.year
        unique_years = years.unique()
        for start_year in range(2013, 2024, 4):
            if start_year in unique_years:
                cycle_years = [y for y in range(start_year, start_year + 4) if y in unique_years]
                cycle_mask = years.isin(cycle_years)
                cycle_sum = weights[cycle_mask].sum()
                self.assertAlmostEqual(cycle_sum, 1.0, places=4)
    
    def test_strategy_registration(self):
        """Test that the strategy is properly registered."""
        # We can't directly import core.strategies without affecting the real registry,
        # so we'll just check if the registration decorator is applied correctly
        source_code = open(self.example_strategy_path, 'r').read()
        self.assertIn('@register_strategy("dynamic_dca_10ma")', source_code)

if __name__ == "__main__":
    unittest.main() 