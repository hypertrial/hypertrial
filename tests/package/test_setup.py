import unittest
import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path


class TestSetup(unittest.TestCase):
    """Tests to verify the setup.py configuration works correctly."""

    def setUp(self):
        """Set up a temporary directory for testing package builds."""
        self.temp_dir = tempfile.mkdtemp()
        self.old_dir = os.getcwd()
        self.project_root = Path(__file__).parent.parent.parent.absolute()
        
    def tearDown(self):
        """Clean up temporary directory after tests."""
        os.chdir(self.old_dir)
        shutil.rmtree(self.temp_dir)
        
    def test_setup_py_syntax(self):
        """Test that setup.py has valid Python syntax."""
        setup_path = os.path.join(self.project_root, "setup.py")
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", setup_path],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"setup.py has syntax errors: {result.stderr}")
        
    def test_package_buildable(self):
        """Test that package can be built with setuptools."""
        os.chdir(self.project_root)
        
        # Check if wheel package is installed
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "wheel"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            self.skipTest("wheel package not installed, skipping build test")
            
        # Try to build a wheel
        result = subprocess.run(
            [sys.executable, "setup.py", "bdist_wheel", "--universal", "--quiet"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Failed to build wheel: {result.stderr}")
        
        # Check that the wheel file was created
        self.assertTrue(os.path.exists(os.path.join(self.project_root, "dist")))
        wheel_files = list(Path(self.project_root, "dist").glob("*.whl"))
        self.assertGreater(len(wheel_files), 0, "No wheel file was created")
        
    def test_find_packages(self):
        """Test that setuptools.find_packages finds the core package."""
        # This requires importing from setup.py, which might not be possible
        # in all environments. Use a subprocess to check instead.
        os.chdir(self.project_root)
        result = subprocess.run(
            [
                sys.executable, 
                "-c", 
                "from setuptools import find_packages; print(find_packages())"
            ],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("core", result.stdout, "find_packages() should include the core package")
        
    def test_entry_point(self):
        """Test that the console script entry point is correctly configured."""
        # This test checks if the entry point is defined correctly in setup.py
        # It doesn't verify the script works, just that it's properly configured
        with open(os.path.join(self.project_root, "setup.py"), "r") as f:
            setup_content = f.read()
            
        self.assertIn("entry_points", setup_content)
        self.assertIn("console_scripts", setup_content)
        self.assertIn("hypertrial=core.cli:cli_main", setup_content)


if __name__ == "__main__":
    unittest.main() 