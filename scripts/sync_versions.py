#!/usr/bin/env python3
"""
Version Synchronization Script

This script ensures that all __init__.py files in the project contain the same 
version number as specified in setup.py.

Usage:
    python scripts/sync_versions.py
"""

import os
import re
import sys
from pathlib import Path

def extract_version_from_setup():
    """Extract version number from setup.py."""
    setup_path = Path('setup.py')
    if not setup_path.exists():
        print("Error: setup.py not found")
        sys.exit(1)
    
    with open(setup_path, 'r') as f:
        content = f.read()
    
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        print("Error: Could not find version in setup.py")
        sys.exit(1)
    
    return version_match.group(1)

def find_init_files(root_dir='.'):
    """Find all __init__.py files in the project."""
    init_files = []
    
    # Directories to exclude
    exclude_patterns = [
        '.git', '.pytest_cache', '__pycache__', 
        'venv', 'env', '.env', 'virtualenv', 
        'site-packages', 'dist', 'build/lib'
    ]
    
    # Core project directories to focus on
    project_dirs = ['core', 'tests', 'submit_strategies', 'hypertrial']
    
    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
        
        if '__init__.py' in files:
            # Check if file path contains any project directories
            if any(project_dir in root for project_dir in project_dirs) or root == '.':
                init_path = os.path.join(root, '__init__.py')
                init_files.append(init_path)
    
    return init_files

def update_version_in_file(file_path, version):
    """Update the version number in a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if the file already has a version string
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    
    if version_match:
        # Replace existing version
        new_content = re.sub(
            r'__version__\s*=\s*["\']([^"\']+)["\']', 
            f'__version__ = "{version}"', 
            content
        )
        changed = version_match.group(1) != version
    else:
        # Add version if it doesn't exist
        if content.strip():
            new_content = f"{content.rstrip()}\n\n__version__ = \"{version}\"\n"
        else:
            new_content = f"__version__ = \"{version}\"\n"
        changed = True
    
    if changed:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    
    return False

def main():
    # Get version from setup.py
    version = extract_version_from_setup()
    print(f"Current version in setup.py: {version}")
    
    # Find all __init__.py files
    init_files = find_init_files()
    print(f"Found {len(init_files)} relevant __init__.py files")
    
    # Update version in all files
    updated_files = []
    for init_file in init_files:
        if update_version_in_file(init_file, version):
            updated_files.append(init_file)
    
    # Print summary
    if updated_files:
        print(f"Updated version to {version} in {len(updated_files)} files:")
        for file in updated_files:
            print(f"  - {file}")
    else:
        print("All files already have the correct version.")

if __name__ == "__main__":
    main() 