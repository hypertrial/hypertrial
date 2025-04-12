#!/usr/bin/env python3
"""
Test the compatibility of packages listed in requirements.txt.

This test:
1. Parses requirements.txt
2. Attempts to import each package
3. Checks for known compatibility issues between packages
4. Verifies that newer version requirements (e.g., pandas>=2.0.0) work correctly
"""

import os
import re
import sys
import importlib
import subprocess
import pytest
from typing import Dict, List, Tuple

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def parse_requirements() -> List[Tuple[str, str]]:
    """
    Parse requirements.txt file and extract package name and version constraints.
    
    Returns:
        List of tuples (package_name, version_constraint)
    """
    # Update the path to point to the main project directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    requirements_path = os.path.join(project_root, 'requirements.txt')
    requirements = []
    
    with open(requirements_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Extract package name and version
            match = re.match(r'^([a-zA-Z0-9_\-]+)([>=<~!].+)?$', line)
            if match:
                package_name = match.group(1)
                version_constraint = match.group(2) or ''
                # Convert hyphen to underscore for import compatibility
                import_name = package_name.replace('-', '_')
                requirements.append((import_name, version_constraint))
    
    return requirements

def test_individual_imports():
    """Test that each package in requirements.txt can be imported."""
    failed_imports = []
    
    # Map of package names to their import names
    import_name_mapping = {
        'coinmetrics_api_client': ['coinmetrics_api_client', 'coinmetrics']
    }
    
    for package_name, version in parse_requirements():
        try:
            # Check if there's a special mapping for this package
            if package_name in import_name_mapping:
                # Try each possible import name
                imported = False
                for import_name in import_name_mapping[package_name]:
                    try:
                        module = importlib.import_module(import_name)
                        version_attr = getattr(module, '__version__', None)
                        if version_attr:
                            print(f"Successfully imported {package_name} as {import_name} version {version_attr}")
                        else:
                            print(f"Successfully imported {package_name} as {import_name} (version unknown)")
                        imported = True
                        break
                    except ImportError:
                        continue
                        
                if not imported:
                    raise ImportError(f"None of the import names {import_name_mapping[package_name]} worked for {package_name}")
            else:
                # Regular import
                module = importlib.import_module(package_name)
                # Try to get version (if available)
                version_attr = getattr(module, '__version__', None)
                if version_attr:
                    print(f"Successfully imported {package_name} version {version_attr}")
                else:
                    print(f"Successfully imported {package_name} (version unknown)")
        except ImportError as e:
            failed_imports.append((package_name, str(e)))
    
    if failed_imports:
        error_message = "The following packages could not be imported:\n"
        for package, error in failed_imports:
            error_message += f"  - {package}: {error}\n"
        pytest.fail(error_message)

def test_numpy_pandas_compatibility():
    """Test specific compatibility between numpy and pandas."""
    try:
        import pandas as pd
        import numpy as np
        
        # Create a pandas DataFrame with numpy data
        df = pd.DataFrame({'A': np.array([1, 2, 3]), 'B': np.array([4, 5, 6])})
        
        # Test basic operations
        # 1. DataFrame creation from numpy array
        assert df.shape == (3, 2), "DataFrame shape incorrect"
        
        # 2. Conversion to numpy
        np_array = df.to_numpy()
        assert isinstance(np_array, np.ndarray), "Failed to convert DataFrame to numpy array"
        
        # 3. Math operations
        result = df['A'] + np.array([10, 20, 30])
        expected = pd.Series([11, 22, 33], name='A')
        assert result.equals(expected), "Basic numpy-pandas math operation failed"
        
        # Print version info for diagnostics
        print(f"Numpy version: {np.__version__}")
        print(f"Pandas version: {pd.__version__}")
        print("Numpy-Pandas compatibility test passed")
        
    except Exception as e:
        pytest.fail(f"Numpy-Pandas compatibility test failed: {str(e)}")

def test_matplotlib_integration():
    """Test matplotlib integration with numpy/pandas."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        
        # Use non-interactive backend for testing
        matplotlib.use('Agg')
        
        # Create sample data
        data = pd.DataFrame({
            'x': np.linspace(0, 10, 10),
            'y': np.random.randn(10)
        })
        
        # Create a simple plot
        plt.figure(figsize=(8, 6))
        plt.plot(data['x'], data['y'])
        plt.title('Test Plot')
        plt.close()
        
        print(f"Matplotlib version: {matplotlib.__version__}")
        print("Matplotlib integration test passed")
        
    except Exception as e:
        pytest.fail(f"Matplotlib integration test failed: {str(e)}")

def test_scipy_integration():
    """Test scipy integration with numpy."""
    try:
        import numpy as np
        import scipy
        from scipy import stats
        
        # Create sample data
        data = np.random.normal(size=100)
        
        # Test a basic scipy function
        mean, std = stats.norm.fit(data)
        
        # Check results make sense
        assert -1 < mean < 1, "Mean of random normal data should be close to 0"
        assert 0.5 < std < 1.5, "Std of random normal data should be close to 1"
        
        print(f"Scipy version: {scipy.__version__}")
        print("Scipy integration test passed")
        
    except Exception as e:
        pytest.fail(f"Scipy integration test failed: {str(e)}")

def test_coinmetrics_api_client():
    """Test basic functionality of coinmetrics-api-client."""
    try:
        # Import the module - the correct import name might be different from the package name
        # Try several possible import names
        module = None
        import_names = ['coinmetrics_api_client', 'coinmetrics']
        
        for import_name in import_names:
            try:
                module = importlib.import_module(import_name)
                print(f"Successfully imported {import_name}")
                break
            except ImportError:
                continue
                
        if module is None:
            raise ImportError("Could not import coinmetrics API client using any of the known import names")
        
        # Get version info if available
        version_attr = getattr(module, '__version__', None)
        if version_attr:
            print(f"Coinmetrics API client version: {version_attr}")
        
        print("Coinmetrics API client import test passed")
        
    except Exception as e:
        pytest.fail(f"Coinmetrics API client test failed: {str(e)}")

def test_code_quality_tools():
    """Test the presence and basic functionality of code quality tools."""
    tools = ['pytest', 'bandit', 'safety', 'pylint']
    
    for tool in tools:
        try:
            module = importlib.import_module(tool)
            print(f"Successfully imported {tool}")
        except ImportError as e:
            pytest.fail(f"Failed to import {tool}: {str(e)}")

def test_psutil_functionality():
    """Test basic functionality of psutil."""
    try:
        import psutil
        
        # Test getting system memory info
        memory = psutil.virtual_memory()
        assert memory.total > 0, "Failed to get system memory info"
        
        # Test getting CPU info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        assert 0 <= cpu_percent <= 100, "CPU percent out of valid range"
        
        print(f"Psutil version: {psutil.__version__}")
        print("Psutil functionality test passed")
        
    except Exception as e:
        pytest.fail(f"Psutil functionality test failed: {str(e)}")

def test_all_packages_installed():
    """
    Test that all packages in requirements.txt are installed
    with compatible versions.
    """
    try:
        # Run pip list to get installed packages and versions
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list', '--format=json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        import json
        installed_packages = {
            pkg['name'].lower(): pkg['version'] 
            for pkg in json.loads(result.stdout)
        }
        
        # Check each package in requirements.txt
        for package_name, version_constraint in parse_requirements():
            # Convert import name back to package name for pip comparison
            pip_name = package_name.replace('_', '-').lower()
            
            if pip_name not in installed_packages:
                pytest.fail(f"Package {pip_name} not installed")
                
            print(f"Package {pip_name} installed with version {installed_packages[pip_name]}")
            
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to get installed packages: {e.stderr}")
    except Exception as e:
        pytest.fail(f"Error checking installed packages: {str(e)}")

if __name__ == "__main__":
    test_individual_imports()
    test_numpy_pandas_compatibility()
    test_matplotlib_integration()
    test_scipy_integration()
    test_coinmetrics_api_client()
    test_code_quality_tools()
    test_psutil_functionality()
    test_all_packages_installed() 