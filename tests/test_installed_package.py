import unittest
import sys
import os
import subprocess
import importlib
import importlib.util
from pathlib import Path

class TestInstalledPackage(unittest.TestCase):
    """Tests to verify that the installed package works correctly."""
    
    def setUp(self):
        # Skip these tests if the package is not installed
        try:
            import hypertrial
            self.package_installed = True
        except ImportError:
            self.package_installed = False
    
    def test_package_importable(self):
        """Test that the hypertrial package can be imported."""
        if not self.package_installed:
            self.skipTest("hypertrial package not installed")
        
        import hypertrial
        self.assertTrue(hasattr(hypertrial, '__version__'))
    
    def test_public_api(self):
        """Test that the public API is accessible."""
        if not self.package_installed:
            self.skipTest("hypertrial package not installed")
        
        import hypertrial
        
        # Check that key functions are exposed
        expected_attributes = [
            'main',
            'register_strategy',
            'load_strategies',
            'get_strategy',
            'list_strategies',
            'backtest_dynamic_dca',
            'compute_cycle_spd',
            'load_data',
            'plot_price_vs_lookback_avg',
            'plot_final_weights',
            'plot_weight_sums_by_cycle'
        ]
        
        for attr in expected_attributes:
            with self.subTest(attribute=attr):
                self.assertTrue(hasattr(hypertrial, attr), f"Public API attribute {attr} not found")
                # Verify it's callable if it's a function
                if attr != 'security':  # security is a module
                    self.assertTrue(callable(getattr(hypertrial, attr)), f"{attr} is not callable")
    
    def test_cli_command(self):
        """Test that the CLI command is installed and runs correctly."""
        if not self.package_installed:
            self.skipTest("hypertrial package not installed")
        
        # Test the CLI is accessible
        result = subprocess.run(
            ["hypertrial", "--help"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if command exists and returns help
        if result.returncode != 0:
            # Try with module invocation as fallback
            result = subprocess.run(
                [sys.executable, "-m", "hypertrial", "--help"],
                capture_output=True,
                text=True,
                check=False
            )
        
        self.assertEqual(result.returncode, 0, f"CLI command failed: {result.stderr}")
        self.assertIn("usage", result.stdout.lower())
    
    def test_version_consistency(self):
        """Test that the version is consistent between package and import."""
        if not self.package_installed:
            self.skipTest("hypertrial package not installed")
        
        # Get version from code
        import hypertrial
        code_version = hypertrial.__version__
        
        # Get version from pip list
        pip_result = subprocess.run(
            [sys.executable, "-m", "pip", "list"],
            capture_output=True,
            text=True,
            check=False
        )
        
        pip_output = pip_result.stdout
        import re
        version_match = re.search(r"hypertrial\s+(\S+)", pip_output)
        
        if version_match:
            pip_version = version_match.group(1)
            self.assertEqual(code_version, pip_version, 
                            f"Version mismatch: {code_version} (code) vs {pip_version} (pip)")
        else:
            self.fail("Could not find hypertrial in pip list output")
    
    def test_strategies_functionality(self):
        """Test that the strategies functionality works correctly."""
        if not self.package_installed:
            self.skipTest("hypertrial package not installed")
        
        from hypertrial import load_strategies, list_strategies
        
        # Load strategies
        load_strategies()
        
        # List strategies
        strategies = list_strategies()
        
        # Check that some core strategies are available
        self.assertGreater(len(strategies), 0, "No strategies loaded")
        
        # Convert to list if it's a dict (keys)
        if isinstance(strategies, dict):
            strategy_names = strategies.keys()
        else:
            strategy_names = strategies
            
        expected_strategies = ['uniform_dca', 'dynamic_dca']
        for strategy in expected_strategies:
            with self.subTest(strategy=strategy):
                self.assertTrue(any(strategy in s for s in strategy_names), 
                              f"Core strategy {strategy} not found in loaded strategies")

if __name__ == "__main__":
    unittest.main() 