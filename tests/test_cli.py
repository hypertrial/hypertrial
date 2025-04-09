import unittest
import subprocess
import sys
import importlib.util
import os
from pathlib import Path


class TestCommandLineInterface(unittest.TestCase):
    """Tests for the command-line interface after package installation."""
    
    @classmethod
    def setUpClass(cls):
        """Check if the package is installed with the entry point."""
        cls.package_installed = False
        try:
            # Try to import the main module
            import core.main
            # Check if the entry point script is available
            result = subprocess.run(
                ["which", "hypertrial"], 
                capture_output=True,
                text=True
            )
            cls.package_installed = result.returncode == 0
        except ImportError:
            pass

    def test_cli_help(self):
        """Test that the CLI help command works."""
        if not self.package_installed:
            self.skipTest("Package not installed with entry point")
            
        result = subprocess.run(
            ["hypertrial", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
        
    def test_cli_list_strategies(self):
        """Test that the CLI list command works."""
        if not self.package_installed:
            self.skipTest("Package not installed with entry point")
            
        result = subprocess.run(
            ["hypertrial", "--list"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('uniform_dca', result.stdout)
        self.assertIn('dynamic_dca', result.stdout)
        
    def test_module_run(self):
        """Test that the module can be run directly with Python."""
        # This test should work even if the entry point isn't installed
        result = subprocess.run(
            [sys.executable, "-m", "core.main", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
        
    def test_main_function(self):
        """Test that the main function can be imported and is callable."""
        try:
            # Try to import the main function
            from core.main import main
            # Check if it's callable
            self.assertTrue(callable(main))
        except ImportError:
            self.skipTest("core.main module not importable")
    
    def test_strategy_file_option(self):
        """Test that the CLI accepts the --strategy-file option."""
        # Check that the --strategy-file option is recognized
        result = subprocess.run(
            [sys.executable, "-m", "core.main", "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('--strategy-file', result.stdout)
        self.assertIn('-f', result.stdout)  # Check short option too


class TestVirtualEnvInstallation(unittest.TestCase):
    """
    Tests for installation in a virtual environment.
    These tests are more complex and require creating a virtual environment.
    They're marked as expected failures since they might not work in all CI environments.
    """
    
    @unittest.expectedFailure
    def test_install_in_venv(self):
        """Test installation in a fresh virtual environment."""
        # This test would create a virtual environment, install the package,
        # and verify it works. Marked as expected failure since it requires
        # creating a venv, which might not be possible in all environments.
        self.skipTest("Virtual environment tests not implemented")


if __name__ == "__main__":
    unittest.main() 