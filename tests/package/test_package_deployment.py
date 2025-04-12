import unittest
import os
import re
import subprocess
import sys
import importlib
import json
from pathlib import Path
from setuptools import find_packages

class TestPackageDeployment(unittest.TestCase):
    """Tests to verify that the package is correctly configured for PyPI deployment."""

    def test_package_structure(self):
        """Test that the package structure is correct."""
        # Check for essential files
        required_files = ["setup.py", "README.md", "LICENSE", "requirements.txt", "pyproject.toml"]
        for file in required_files:
            with self.subTest(file=file):
                self.assertTrue(os.path.exists(file), f"Required file {file} not found")
        
        # Check that packages are correctly discovered
        packages = find_packages()
        self.assertIn("core", packages, "Core package not found")
        self.assertIn("hypertrial", packages, "Hypertrial package not found")
    
    def test_version_consistency(self):
        """Test that version is consistent across files."""
        # Get version from core/__init__.py
        spec = importlib.util.find_spec("core")
        if spec is None:
            self.fail("Core module not found")
        
        with open(os.path.join(spec.submodule_search_locations[0], "__init__.py"), "r") as f:
            content = f.read()
            core_version = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if core_version:
                core_version = core_version.group(1)
            else:
                self.fail("Version not found in core/__init__.py")
        
        # Get version from setup.py
        with open("setup.py", "r") as f:
            content = f.read()
            setup_version = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if setup_version:
                setup_version = setup_version.group(1)
            else:
                self.fail("Version not found in setup.py")
        
        # Compare versions
        self.assertEqual(core_version, setup_version, "Version mismatch between core/__init__.py and setup.py")
    
    def test_metadata_completeness(self):
        """Test that all required metadata for PyPI is set."""
        with open("setup.py", "r") as f:
            content = f.read()
            
        # Check for essential metadata
        required_metadata = [
            "name", "version", "description", "long_description", 
            "author", "author_email", "url", "classifiers", 
            "python_requires", "install_requires"
        ]
        
        for metadata in required_metadata:
            with self.subTest(metadata=metadata):
                self.assertIn(f"{metadata}=", content, f"Required metadata {metadata} not found in setup.py")
    
    def test_build_wheel(self):
        """Test that the package builds successfully into a wheel."""
        # Skip if in CI environment
        if os.environ.get("CI") == "true":
            self.skipTest("Skipping wheel build test in CI environment")
        
        # Try to build the wheel
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", "dist_test"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Skip test if network connectivity issues are detected
            if "Failed to establish a new connection" in result.stderr:
                self.skipTest("Skipping wheel build test due to network connectivity issues")
            
            # Cleanup
            if os.path.exists("dist_test"):
                import shutil
                shutil.rmtree("dist_test")
            
            self.assertEqual(result.returncode, 0, f"Wheel build failed: {result.stderr}")
        except Exception as e:
            # Also skip if any network-related exception occurs
            if "connection" in str(e).lower():
                self.skipTest("Skipping wheel build test due to network connectivity issues")
            self.fail(f"Failed to build wheel: {str(e)}")
    
    def test_entry_point_configuration(self):
        """Test that entry points are correctly configured."""
        with open("setup.py", "r") as f:
            content = f.read()
        
        # Check that entry points are defined
        self.assertIn("entry_points", content, "Entry points not defined in setup.py")
        self.assertIn("console_scripts", content, "Console scripts not defined in setup.py")
        self.assertIn("hypertrial=core.cli:cli_main", content, "Main entry point not correctly defined")
    
    def test_requirements_matching(self):
        """Test that requirements.txt matches setup.py install_requires."""
        # Read requirements.txt
        with open("requirements.txt", "r") as f:
            requirements_txt = [line.strip() for line in f.readlines() if line.strip() and not line.startswith("#")]
        
        # Read setup.py install_requires
        with open("setup.py", "r") as f:
            content = f.read()
            install_requires_match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if not install_requires_match:
                self.fail("Could not find install_requires in setup.py")
            
            # Extract requirements from the matched string
            install_requires_str = install_requires_match.group(1)
            install_requires = re.findall(r'["\']([^"\']+)["\']', install_requires_str)
        
        # Compare base package names (without version specifiers)
        requirements_txt_base = [req.split(">=")[0].split("==")[0].strip() for req in requirements_txt]
        install_requires_base = [req.split(">=")[0].split("==")[0].strip() for req in install_requires]
        
        # Check that all requirements.txt packages are in install_requires
        for req in requirements_txt_base:
            with self.subTest(requirement=req):
                self.assertIn(req, install_requires_base, f"Requirement {req} from requirements.txt not found in setup.py")

if __name__ == "__main__":
    unittest.main() 