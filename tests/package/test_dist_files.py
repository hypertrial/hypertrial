import unittest
import os
import subprocess
import sys
import tempfile
import zipfile
import tarfile
import re
import json
from pathlib import Path

class TestDistributionFiles(unittest.TestCase):
    """Tests to verify that distribution files are correct before uploading to PyPI."""
    
    def setUp(self):
        # Skip these tests if dist directory doesn't exist
        if not os.path.exists("dist"):
            self.skipTest("dist/ directory not found. Run python -m build first.")
        
        # Find wheel and sdist files
        self.wheel_files = list(Path("dist").glob("*.whl"))
        self.sdist_files = list(Path("dist").glob("*.tar.gz"))
        
        if not self.wheel_files:
            self.skipTest("No wheel file found in dist/. Run python -m build first.")
        if not self.sdist_files:
            self.skipTest("No sdist file found in dist/. Run python -m build first.")
            
        # Use the latest versions if there are multiple
        self.wheel_file = sorted(self.wheel_files)[-1]
        self.sdist_file = sorted(self.sdist_files)[-1]
    
    def test_dist_files_exist(self):
        """Test that distribution files exist and have expected names."""
        # Check wheel file format (name-version-pythontag-abiver-platform.whl)
        wheel_pattern = r"hypertrial-[\d\.]+(\.dev\d+)?-py\d-none-any\.whl"
        self.assertTrue(re.match(wheel_pattern, self.wheel_file.name), 
                      f"Wheel filename {self.wheel_file.name} doesn't match expected pattern")
        
        # Check sdist file format (name-version.tar.gz)
        sdist_pattern = r"hypertrial-[\d\.]+(\.dev\d+)?\.tar\.gz"
        self.assertTrue(re.match(sdist_pattern, self.sdist_file.name),
                      f"SDist filename {self.sdist_file.name} doesn't match expected pattern")
    
    def test_wheel_contents(self):
        """Test that the wheel file contains required files."""
        with zipfile.ZipFile(self.wheel_file, 'r') as wheel:
            wheel_files = wheel.namelist()
            
            # Check for metadata files
            self.assertTrue(any(f.endswith('.dist-info/METADATA') for f in wheel_files),
                         "METADATA file missing from wheel")
            self.assertTrue(any(f.endswith('.dist-info/entry_points.txt') for f in wheel_files),
                         "entry_points.txt file missing from wheel")
            self.assertTrue(any(f.endswith('.dist-info/WHEEL') for f in wheel_files),
                         "WHEEL file missing from wheel")
            
            # Check for package files
            self.assertTrue(any(f.startswith('core/') for f in wheel_files),
                         "core/ directory missing from wheel")
            self.assertTrue(any(f.startswith('hypertrial/') for f in wheel_files),
                         "hypertrial/ directory missing from wheel")
            
            # Check specific essential files
            essential_files = [
                'core/__init__.py',
                'hypertrial/__init__.py',
                'core/main.py',
                'core/strategies/__init__.py'
            ]
            for file in essential_files:
                self.assertTrue(any(f.endswith(file) for f in wheel_files),
                             f"Essential file {file} missing from wheel")
    
    def test_sdist_contents(self):
        """Test that the sdist file contains required files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with tarfile.open(self.sdist_file, 'r:gz') as sdist:
                sdist.extractall(path=temp_dir)
                
                # The extracted directory should be named like "hypertrial-0.1.0"
                extracted_dirs = [d for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d))]
                self.assertEqual(len(extracted_dirs), 1, "Expected a single directory in sdist")
                
                extracted_dir = os.path.join(temp_dir, extracted_dirs[0])
                
                # Check essential files
                essential_files = [
                    'setup.py',
                    'README.md',
                    'LICENSE',
                    'requirements.txt',
                    'core/__init__.py',
                    'hypertrial/__init__.py',
                    'core/main.py'
                ]
                
                for file in essential_files:
                    self.assertTrue(os.path.exists(os.path.join(extracted_dir, file)),
                                 f"Essential file {file} missing from sdist")
    
    def test_metadata_in_wheel(self):
        """Test that the wheel contains correct metadata."""
        with zipfile.ZipFile(self.wheel_file, 'r') as wheel:
            # Find the METADATA file
            metadata_file = next((f for f in wheel.namelist() if f.endswith('.dist-info/METADATA')), None)
            self.assertIsNotNone(metadata_file, "METADATA file not found in wheel")
            
            # Read metadata
            metadata_content = wheel.read(metadata_file).decode('utf-8')
            
            # Check essential metadata
            self.assertIn('Name: hypertrial', metadata_content)
            self.assertIn('Version:', metadata_content)
            self.assertIn('Summary:', metadata_content)
            self.assertIn('Home-page:', metadata_content)
            self.assertIn('Author:', metadata_content)
            self.assertIn('Author-email:', metadata_content)
            # Modern wheels use License-File instead of License field
            self.assertIn('License-File:', metadata_content)
            
            # Check dependencies
            essential_deps = [
                'pandas', 'numpy', 'matplotlib', 'coinmetrics-api-client'
            ]
            for dep in essential_deps:
                self.assertIn(f'Requires-Dist: {dep}', metadata_content, 
                           f"Dependency {dep} missing from wheel metadata")
    
    def test_entry_points_in_wheel(self):
        """Test that the wheel contains correct entry point configuration."""
        with zipfile.ZipFile(self.wheel_file, 'r') as wheel:
            # Find the entry_points.txt file
            entry_points_file = next((f for f in wheel.namelist() if f.endswith('.dist-info/entry_points.txt')), None)
            self.assertIsNotNone(entry_points_file, "entry_points.txt file not found in wheel")
            
            # Read entry points
            entry_points_content = wheel.read(entry_points_file).decode('utf-8')
            
            # Check for console script entry point
            self.assertIn('[console_scripts]', entry_points_content)
            # Account for possible whitespace variations
            self.assertTrue(
                'hypertrial=core.cli:cli_main' in entry_points_content or 
                'hypertrial = core.cli:cli_main' in entry_points_content,
                "Entry point 'hypertrial=core.cli:cli_main' not found in entry_points.txt"
            )
    
    def test_wheel_validation(self):
        """Test the wheel using twine check."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "twine", "check", str(self.wheel_file)],
                capture_output=True,
                text=True,
                check=False
            )
            self.assertEqual(result.returncode, 0, 
                          f"Twine check failed for wheel: {result.stdout}\n{result.stderr}")
        except FileNotFoundError:
            self.skipTest("twine not installed, skipping validation")
    
    def test_sdist_validation(self):
        """Test the sdist using twine check."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "twine", "check", str(self.sdist_file)],
                capture_output=True,
                text=True,
                check=False
            )
            self.assertEqual(result.returncode, 0, 
                          f"Twine check failed for sdist: {result.stdout}\n{result.stderr}")
        except FileNotFoundError:
            self.skipTest("twine not installed, skipping validation")

if __name__ == "__main__":
    unittest.main() 