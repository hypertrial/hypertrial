import unittest
import importlib
import sys
import subprocess
import os
from pathlib import Path


class TestInstallation(unittest.TestCase):
    """Tests to verify that the package installation works correctly."""

    def test_core_module_importable(self):
        """Test that core module can be imported."""
        import core
        self.assertTrue(hasattr(core, '__version__'))
        
    def test_strategies_importable(self):
        """Test that strategies module can be imported."""
        import core.strategies
        self.assertTrue(hasattr(core.strategies, 'available_strategies'))
        
    def test_entry_point_accessible(self):
        """Test that the main entry point is accessible."""
        # Check that core.main is importable
        try:
            from core.main import main
            self.assertTrue(callable(main))
        except ImportError:
            self.fail("Could not import main function from core.main")
        
    def test_package_metadata(self):
        """Test package metadata is correctly set."""
        try:
            import pkg_resources
            pkg = pkg_resources.get_distribution('hypertrial')
            self.assertEqual(pkg.project_name, 'hypertrial')
            self.assertTrue(hasattr(pkg, 'version'))
        except (pkg_resources.DistributionNotFound, ImportError):
            self.skipTest("Package not installed or pkg_resources not available")


class TestCommandLine(unittest.TestCase):
    """Tests for the command-line interface."""
    
    def test_help_option(self):
        """Test that --help option works."""
        result = subprocess.run(
            [sys.executable, '-m', 'core.main', '--help'], 
            capture_output=True, 
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
        
    def test_list_strategies(self):
        """Test that --list option works."""
        result = subprocess.run(
            [sys.executable, '-m', 'core.main', '--list'], 
            capture_output=True, 
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('uniform_dca', result.stdout)
        self.assertIn('dynamic_dca', result.stdout)


class TestDependencies(unittest.TestCase):
    """Tests for required dependencies."""
    
    def test_dependencies_installed(self):
        """Test that all required dependencies are installed."""
        required_packages = ['pandas', 'numpy', 'matplotlib']
        for package in required_packages:
            with self.subTest(package=package):
                try:
                    importlib.import_module(package)
                except ImportError:
                    self.fail(f"Required dependency {package} not installed")


if __name__ == '__main__':
    unittest.main() 