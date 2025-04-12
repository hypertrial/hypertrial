#!/usr/bin/env python3
"""
File handling utilities for the Hypertrial framework.
"""
import os
import logging
import sys

# Configure logging
logger = logging.getLogger(__name__)

def check_submit_strategies_path():
    """Check if the submit_strategies directory exists in the correct location"""
    # Get path to project root directory
    core_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(core_dir)
    strategies_dir = os.path.join(root_dir, 'submit_strategies')
    
    if not os.path.exists(strategies_dir):
        logger.error(f"submit_strategies directory not found at: {strategies_dir}")
        logger.error("Please make sure this directory exists and contains your strategy files.")
        return False
        
    # Make sure the submit_strategies directory is in the Python path
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
        logger.info(f"Added {root_dir} to Python path")
        
    return True

def find_strategy_files(root_dir, recursive=False, exclude_dirs=None, exclude_patterns=None, 
                       include_patterns=None, max_files=None):
    """
    Find strategy files in the given directory with filtering options.
    
    Args:
        root_dir (str): Root directory to search
        recursive (bool): Whether to search recursively in subdirectories
        exclude_dirs (list): Directories to exclude from search
        exclude_patterns (list): File patterns to exclude
        include_patterns (list): File patterns to include (only files matching these patterns will be included)
        max_files (int): Maximum number of files to return
        
    Returns:
        list: Paths to found strategy files
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.pytest_cache', '__pycache__', 'venv', 'test_venv', 'build', 'dist']
    if exclude_patterns is None:
        exclude_patterns = ['__init__.py', 'test_*.py', 'conftest.py']
    if include_patterns is None:
        include_patterns = []
    
    # Handle MagicMock objects (for testing) or convert to int
    if max_files is None or hasattr(max_files, '_mock_name'):
        max_files = 100
    else:
        try:
            max_files = int(max_files)
        except (TypeError, ValueError):
            max_files = 100
    
    strategy_files = []
    
    if recursive:
        logger.info(f"Recursively searching for Python files in {root_dir}")
        # Walk the directory structure manually to exclude unwanted directories
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            # Find Python files in this directory
            for file in files:
                if file.endswith('.py'):
                    # Check if the file matches any exclude pattern
                    if not any(file == pattern or (pattern.endswith('*.py') and file.startswith(pattern[:-3])) 
                              for pattern in exclude_patterns):
                        
                        # Check if the file matches include patterns (if specified)
                        if not include_patterns or any(file == pattern or 
                                                    (pattern.endswith('*.py') and file.startswith(pattern[:-3])) or
                                                    (pattern.endswith('.py') and file == pattern) or
                                                    ('*' not in pattern and pattern in file)
                                                    for pattern in include_patterns):
                            file_path = os.path.join(root, file)
                            strategy_files.append(file_path)
                            # Stop if we've reached the max files limit
                            if len(strategy_files) >= max_files:
                                logger.info(f"Reached maximum file limit ({max_files}). Stopping search.")
                                break
            
            # Also stop outer loop if we've reached the limit
            if len(strategy_files) >= max_files:
                break
    else:
        logger.info(f"Searching for Python files in {root_dir}")
        all_files = [os.path.join(root_dir, f) for f in os.listdir(root_dir) 
                    if f.endswith('.py')]
        
        logger.info(f"Found {len(all_files)} Python files before filtering")
        
        # Filter excluded patterns
        filtered_files = [f for f in all_files 
                         if not any(os.path.basename(f) == pattern or 
                                   (pattern.endswith('*.py') and os.path.basename(f).startswith(pattern[:-3])) 
                                   for pattern in exclude_patterns)]
        
        logger.info(f"After exclude filters: {len(filtered_files)} files")
        
        # Apply include patterns if specified
        if include_patterns:
            logger.info(f"Applying include patterns: {include_patterns}")
            include_filtered = []
            for f in filtered_files:
                basename = os.path.basename(f)
                match = False
                for pattern in include_patterns:
                    # Simple exact match
                    if basename == pattern:
                        match = True
                        break
                    # Pattern ends with *.py, check prefix
                    elif pattern.endswith('*.py') and basename.startswith(pattern[:-4]):
                        match = True
                        break
                    # Pattern is just a part of the filename
                    elif pattern in basename:
                        match = True
                        break
                
                if match:
                    include_filtered.append(f)
            
            filtered_files = include_filtered
            logger.info(f"After include filters: {len(filtered_files)} files")
        
        # Limit to max files
        if max_files:
            strategy_files = filtered_files[:max_files]
        else:
            strategy_files = filtered_files
    
    # Print out the strategy files found
    logger.info(f"Found {len(strategy_files)} potential strategy files")
    for i, f in enumerate(strategy_files[:5]):  # Show first 5 only
        logger.info(f"  {i+1}. {f}")
    if len(strategy_files) > 5:
        logger.info(f"  ... and {len(strategy_files) - 5} more")
        
    return strategy_files 