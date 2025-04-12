#!/usr/bin/env python3
"""
Test if the version constraints in requirements.txt are satisfied.

This test:
1. Parses requirements.txt for version constraints
2. Checks if installed packages meet these constraints
3. Checks for version incompatibilities among packages
"""

import os
import re
import sys
import importlib
import subprocess
import pytest
from packaging import version
from typing import Dict, List, Tuple, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def parse_requirement(line: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a single requirement line.
    
    Args:
        line: A line from requirements.txt
        
    Returns:
        Tuple of (package_name, version_constraint, import_name) or None
    """
    line = line.strip()
    # Skip comments and empty lines
    if not line or line.startswith('#'):
        return None
        
    # Extract package name and version
    match = re.match(r'^([a-zA-Z0-9_\-]+)([>=<~!].+)?$', line)
    if match:
        package_name = match.group(1)
        version_constraint = match.group(2) or ''
        # Convert hyphen to underscore for import compatibility
        import_name = package_name.replace('-', '_')
        return (package_name, version_constraint, import_name)
    
    return None

def get_requirements() -> List[Tuple[str, str, str]]:
    """
    Parse requirements.txt file and extract package name, version constraints, and import name.
    
    Returns:
        List of tuples (package_name, version_constraint, import_name)
    """
    # Update the path to point to the main project directory
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    requirements_path = os.path.join(project_root, 'requirements.txt')
    requirements = []
    
    with open(requirements_path, 'r') as f:
        for line in f:
            req = parse_requirement(line)
            if req:
                requirements.append(req)
    
    return requirements

def get_installed_packages() -> Dict[str, str]:
    """
    Get all installed packages and their versions.
    
    Returns:
        Dictionary mapping package names to versions
    """
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'list', '--format=json'],
        capture_output=True,
        text=True,
        check=True
    )
    
    import json
    return {
        pkg['name'].lower(): pkg['version'] 
        for pkg in json.loads(result.stdout)
    }

def check_version_constraint(installed_version: str, constraint: str) -> bool:
    """
    Check if an installed version satisfies a version constraint.
    
    Args:
        installed_version: The installed version string
        constraint: The version constraint (e.g., ">=1.0.0")
        
    Returns:
        True if the constraint is satisfied, False otherwise
    """
    if not constraint:
        return True  # No constraint specified
        
    installed = version.parse(installed_version)
    
    # Handle different constraint types
    if constraint.startswith('>='):
        req_version = version.parse(constraint[2:])
        return installed >= req_version
    elif constraint.startswith('>'):
        req_version = version.parse(constraint[1:])
        return installed > req_version
    elif constraint.startswith('<='):
        req_version = version.parse(constraint[2:])
        return installed <= req_version
    elif constraint.startswith('<'):
        req_version = version.parse(constraint[1:])
        return installed < req_version
    elif constraint.startswith('=='):
        req_version = version.parse(constraint[2:])
        return installed == req_version
    elif constraint.startswith('!='):
        req_version = version.parse(constraint[2:])
        return installed != req_version
    
    # Default case - assume it's a specific version
    req_version = version.parse(constraint)
    return installed == req_version

def test_version_constraints():
    """Test that installed packages satisfy version constraints in requirements.txt."""
    installed_packages = get_installed_packages()
    requirements = get_requirements()
    
    violations = []
    
    for package_name, constraint, _ in requirements:
        # Skip if no constraint
        if not constraint:
            continue
            
        pip_name = package_name.lower()
        
        if pip_name not in installed_packages:
            violations.append(f"Package {package_name} is not installed")
            continue
            
        installed_version = installed_packages[pip_name]
        
        if not check_version_constraint(installed_version, constraint):
            violations.append(
                f"Package {package_name} version {installed_version} "
                f"does not satisfy constraint {constraint}"
            )
        else:
            print(f"Package {package_name} version {installed_version} "
                  f"satisfies constraint {constraint}")
    
    if violations:
        error_message = "The following version constraints are not satisfied:\n"
        for violation in violations:
            error_message += f"  - {violation}\n"
        pytest.fail(error_message)

def check_import_version(import_name: str) -> Optional[str]:
    """
    Get the version of an imported module.
    
    Args:
        import_name: The name of the module to import
        
    Returns:
        The version string or None if not available
    """
    try:
        module = importlib.import_module(import_name)
        version_attr = getattr(module, '__version__', None)
        return version_attr
    except (ImportError, AttributeError):
        return None

def test_pandas_numpy_versions():
    """Test that pandas and numpy versions are compatible."""
    try:
        import pandas as pd
        import numpy as np
        
        pandas_version = pd.__version__
        numpy_version = np.__version__
        
        print(f"Testing compatibility of pandas {pandas_version} with numpy {numpy_version}")
        
        # Test numpy array creation and manipulation with pandas
        array = np.array([1, 2, 3])
        series = pd.Series(array)
        assert list(series) == [1, 2, 3], "Failed to create pandas Series from numpy array"
        
        # Test more complex data structures
        df = pd.DataFrame({
            'A': np.random.rand(5),
            'B': np.random.randint(0, 10, 5)
        })
        
        # Test operations that use numpy under the hood
        mean_values = df.mean()
        std_values = df.std()
        
        # Test conversion back to numpy
        array2d = df.to_numpy()
        assert array2d.shape == (5, 2), "Incorrect shape after converting DataFrame to numpy array"
        
        # If pandas>=2.0.0 and numpy>=2.0.0, test new features
        if version.parse(pandas_version) >= version.parse('2.0.0') and \
           version.parse(numpy_version) >= version.parse('2.0.0'):
            # Test pandas 2.0+ specific features that work with numpy 2.0+
            # For example, test PyArrow integration if available
            try:
                import pyarrow
                # PyArrow is often used with newer pandas versions
                arrow_table = df.to_arrow()
                assert arrow_table.num_rows == 5, "Incorrect row count in Arrow table"
                print("PyArrow integration test passed")
            except (ImportError, AttributeError):
                # PyArrow might not be installed or to_arrow might not exist
                print("PyArrow integration test skipped")
        
        print("Pandas-Numpy compatibility test passed")
        
    except Exception as e:
        pytest.fail(f"Pandas-Numpy compatibility test failed: {str(e)}")

def test_matplotlib_integration_with_latest_numpy_pandas():
    """Test matplotlib integration with latest numpy/pandas versions."""
    try:
        import matplotlib
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        
        # Use non-interactive backend for testing
        matplotlib.use('Agg')
        
        # Check versions
        pandas_version = pd.__version__
        numpy_version = np.__version__
        matplotlib_version = matplotlib.__version__
        
        print(f"Testing matplotlib {matplotlib_version} with "
              f"pandas {pandas_version} and numpy {numpy_version}")
        
        # Create data using newer NumPy/Pandas features
        df = pd.DataFrame({
            'x': np.linspace(0, 10, 20),
            'y': np.sin(np.linspace(0, 10, 20)) + np.random.normal(0, 0.1, 20)
        })
        
        # Test plotting
        fig, axes = plt.subplots(2, 1, figsize=(10, 8))
        
        # Basic line plot
        axes[0].plot(df['x'], df['y'])
        axes[0].set_title('Basic Line Plot')
        
        # Scatter plot
        axes[1].scatter(df['x'], df['y'], c=df['y'], cmap='viridis')
        axes[1].set_title('Scatter Plot with Color Mapping')
        
        # Test creating a more complex plot using pandas plotting capabilities
        grouped = pd.DataFrame({
            'group': np.repeat(['A', 'B', 'C'], 10),
            'value': np.random.randn(30) 
        })
        
        fig, ax = plt.subplots()
        grouped.groupby('group').value.plot.kde(ax=ax)
        
        plt.close('all')  # Close all figures to clean up
        
        print("Matplotlib integration test with latest numpy/pandas passed")
        
    except Exception as e:
        pytest.fail(f"Matplotlib integration test with latest numpy/pandas failed: {str(e)}")

def test_scipy_with_latest_numpy():
    """Test scipy compatibility with latest numpy version."""
    try:
        import numpy as np
        import scipy
        from scipy import stats, optimize, signal
        
        # Check versions
        numpy_version = np.__version__
        scipy_version = scipy.__version__
        
        print(f"Testing scipy {scipy_version} with numpy {numpy_version}")
        
        # Test statistical functions
        data = np.random.normal(size=100)
        stats_result = stats.describe(data)
        assert len(stats_result) >= 6, "Stats describe should return at least 6 values"
        
        # Test optimization
        def f(x):
            return x**2 + 10*np.sin(x)
        result = optimize.minimize(f, x0=0)
        assert result.success, "Optimization failed to converge"
        
        # Test signal processing
        t = np.linspace(0, 1, 1000, endpoint=False)
        sig = np.sin(2*np.pi*10*t) + np.sin(2*np.pi*20*t)
        filtered = signal.filtfilt(*signal.butter(4, 0.15), sig)
        assert filtered.shape == sig.shape, "Signal filtering output shape mismatch"
        
        print("Scipy compatibility test with latest numpy passed")
        
    except Exception as e:
        pytest.fail(f"Scipy compatibility test with latest numpy failed: {str(e)}")

if __name__ == "__main__":
    test_version_constraints()
    test_pandas_numpy_versions()
    test_matplotlib_integration_with_latest_numpy_pandas()
    test_scipy_with_latest_numpy() 