#!/usr/bin/env python3
"""
Release Script

This script automates the release process for the package by:
1. Updating the version number in setup.py
2. Synchronizing the version across all __init__.py files
3. Creating a git tag
4. Building the distribution packages
5. Uploading to PyPI (with confirmation)

Usage:
    python scripts/release.py [major|minor|patch]
"""

import os
import re
import sys
import subprocess
from pathlib import Path

def get_current_version():
    """Extract current version from setup.py."""
    with open('setup.py', 'r') as f:
        content = f.read()
    
    version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not version_match:
        print("Error: Could not find version in setup.py")
        sys.exit(1)
    
    return version_match.group(1)

def bump_version(current_version, bump_type):
    """Bump version according to semver rules."""
    major, minor, patch = map(int, current_version.split('.'))
    
    if bump_type == 'major':
        major += 1
        minor = 0
        patch = 0
    elif bump_type == 'minor':
        minor += 1
        patch = 0
    elif bump_type == 'patch':
        patch += 1
    else:
        print(f"Error: Invalid bump type '{bump_type}'. Use 'major', 'minor', or 'patch'.")
        sys.exit(1)
    
    return f"{major}.{minor}.{patch}"

def update_setup_py(new_version):
    """Update version in setup.py."""
    with open('setup.py', 'r') as f:
        content = f.read()
    
    new_content = re.sub(
        r'version\s*=\s*["\']([^"\']+)["\']',
        f'version="{new_version}"',
        content
    )
    
    with open('setup.py', 'w') as f:
        f.write(new_content)

def sync_versions():
    """Run the version synchronization script."""
    sync_script = Path('scripts/sync_versions.py')
    if not sync_script.exists():
        print("Error: sync_versions.py script not found")
        sys.exit(1)
    
    try:
        subprocess.run(['python', str(sync_script)], check=True)
    except subprocess.CalledProcessError:
        print("Error: Failed to synchronize versions")
        sys.exit(1)

def create_git_tag(version):
    """Create a git tag for the release."""
    tag = f"v{version}"
    try:
        # Add all modified files
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit changes
        commit_msg = f"Bump version to {version}"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        
        # Create tag
        tag_msg = f"Release {version}"
        subprocess.run(['git', 'tag', '-a', tag, '-m', tag_msg], check=True)
        
        print(f"Created git tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"Error during git operations: {e}")
        sys.exit(1)

def build_package():
    """Build the distribution packages."""
    try:
        subprocess.run(['python', 'setup.py', 'sdist', 'bdist_wheel'], check=True)
        print("Built distribution packages")
    except subprocess.CalledProcessError:
        print("Error: Failed to build distribution packages")
        sys.exit(1)

def upload_to_pypi():
    """Upload the package to PyPI (with confirmation)."""
    confirm = input("Upload to PyPI? [y/N] ")
    if confirm.lower() != 'y':
        print("Skipping PyPI upload")
        return
    
    try:
        subprocess.run(['twine', 'upload', 'dist/*'], check=True)
        print("Uploaded to PyPI")
    except subprocess.CalledProcessError:
        print("Error: Failed to upload to PyPI")
        sys.exit(1)

def main():
    # Check arguments
    if len(sys.argv) != 2 or sys.argv[1] not in ['major', 'minor', 'patch']:
        print("Usage: python scripts/release.py [major|minor|patch]")
        sys.exit(1)
    
    bump_type = sys.argv[1]
    
    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    
    # Bump version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")
    
    # Confirm
    confirm = input(f"Proceed with release {new_version}? [y/N] ")
    if confirm.lower() != 'y':
        print("Release aborted")
        sys.exit(0)
    
    # Update setup.py
    update_setup_py(new_version)
    print(f"Updated version in setup.py to {new_version}")
    
    # Sync versions across __init__.py files
    sync_versions()
    
    # Create git tag
    create_git_tag(new_version)
    
    # Build package
    build_package()
    
    # Upload to PyPI
    upload_to_pypi()
    
    print(f"Release {new_version} completed successfully!")

if __name__ == "__main__":
    main() 