# data.py
import pandas as pd
import os
import logging
import numpy as np
import requests
import json
from datetime import timedelta, datetime

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def validate_price_data(df, required_columns=['btc_close'], min_days=None, allow_gaps=True):
    """
    Validate Bitcoin price data for correctness and completeness.
    
    Args:
        df (pandas.DataFrame): DataFrame with price data
        required_columns (list): List of required column names
        min_days (int, optional): Minimum number of days required
        allow_gaps (bool): Whether to allow gaps in the date range
    
    Returns:
        bool: True if data is valid
        
    Raises:
        ValueError: If data validation fails
    """
    # Check if DataFrame is empty
    if df is None or df.empty:
        raise ValueError("Price data DataFrame is empty")
        
    # Check required columns
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Required column '{column}' is missing")
            
    # Check index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame index must be a DatetimeIndex")
        
    # Check for duplicate dates
    if df.index.duplicated().any():
        raise ValueError("DataFrame contains duplicate dates")
        
    # Check minimum date range
    if min_days is not None and len(df) < min_days:
        raise ValueError(f"DataFrame contains fewer than {min_days} days")
        
    # Check for gaps in date range
    if not allow_gaps:
        date_range = pd.date_range(start=df.index.min(), end=df.index.max())
        if len(date_range) != len(df):
            raise ValueError("DataFrame contains gaps in date range")
            
    # Check for invalid values in price data
    for column in required_columns:
        # Check for negative or zero values
        if (df[column] <= 0).any():
            raise ValueError(f"Column '{column}' contains negative or zero values")
            
        # Check for NaN or infinite values
        if df[column].isna().any() or np.isinf(df[column]).any():
            raise ValueError(f"Column '{column}' contains NaN or infinite values")
            
    return True

def clean_price_data(df, fill_gaps=False):
    """
    Clean Bitcoin price data by handling missing values, duplicates, and gaps.
    
    Args:
        df (pandas.DataFrame): DataFrame with price data
        fill_gaps (bool): Whether to fill gaps in the date range
        
    Returns:
        pandas.DataFrame: Cleaned DataFrame
    """
    # Make a copy to avoid modifying the original
    cleaned_df = df.copy()
    
    # Ensure index is datetime
    if not isinstance(cleaned_df.index, pd.DatetimeIndex):
        try:
            cleaned_df.index = pd.to_datetime(cleaned_df.index)
        except:
            raise ValueError("Could not convert index to DatetimeIndex")
    
    # Sort by date
    cleaned_df = cleaned_df.sort_index()
    
    # Handle duplicate dates (keep last occurrence)
    cleaned_df = cleaned_df[~cleaned_df.index.duplicated(keep='last')]
    
    # Fill gaps if requested
    if fill_gaps:
        date_range = pd.date_range(start=cleaned_df.index.min(), end=cleaned_df.index.max())
        cleaned_df = cleaned_df.reindex(date_range)
        
    # Handle NaN and infinite values for numeric columns
    numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Replace infinite values with NaN
        cleaned_df[col] = cleaned_df[col].replace([np.inf, -np.inf], np.nan)
        
        # If the column has "close" in the name, use special handling for price data
        if 'close' in col.lower():
            # Identify extreme values (too large or too small)
            # Reasonable Bitcoin price range (adjust as needed)
            extreme_high = 1e9  # 1 billion USD
            extreme_low = 1e-9  # Fraction of a cent
            
            # Create masks for extreme values
            high_mask = cleaned_df[col] > extreme_high
            low_mask = cleaned_df[col] < extreme_low
            extreme_mask = high_mask | low_mask
            
            # Get non-extreme values
            valid_values = cleaned_df.loc[~extreme_mask & ~cleaned_df[col].isna(), col]
            
            if not valid_values.empty:
                # Calculate reasonable replacement value (mean of valid values)
                mean_valid = valid_values.mean()
                
                # Replace extreme values with the mean of valid values
                if extreme_mask.any():
                    cleaned_df.loc[extreme_mask, col] = mean_valid
            
            # Use forward fill to handle any NaN values including those from replaced infinities
            cleaned_df[col] = cleaned_df[col].ffill()
            cleaned_df[col] = cleaned_df[col].bfill()
            
            # Replace any remaining NaNs with the mean
            if cleaned_df[col].isna().any():
                mean_value = cleaned_df[col].mean()
                cleaned_df[col] = cleaned_df[col].fillna(mean_value)
                
            # Replace zero or negative values with previous valid value
            mask = cleaned_df[col] <= 0
            if mask.any():
                # Get valid values
                valid_values = cleaned_df.loc[~mask, col]
                if not valid_values.empty:
                    mean_value = valid_values.mean()
                    cleaned_df.loc[mask, col] = mean_value
                    
            # For the fill_gaps case, ensure interpolation for missing dates
            if fill_gaps:
                # Use linear interpolation for missing values in the middle
                cleaned_df[col] = cleaned_df[col].interpolate(method='linear')
        else:
            # For other columns, just replace NaNs with the mean
            if cleaned_df[col].isna().any():
                mean_value = cleaned_df[col].mean()
                if np.isnan(mean_value):  # If the mean is also NaN
                    mean_value = 0
                cleaned_df[col] = cleaned_df[col].fillna(mean_value)
    
    return cleaned_df

def load_data(csv_path='core/data/btc_price_data.csv'):
    """
    Load Bitcoin price data from a local CSV file.
    If the file doesn't exist, try to fetch it from CoinMetrics.
    
    Args:
        csv_path (str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: DataFrame with price data
        
    Raises:
        RuntimeError: If data cannot be loaded
    """
    # SAFEGUARD: Detect if running in test and using production data path
    if 'core/data/btc_price_data.csv' in csv_path and 'TEST_ONLY' not in csv_path and 'test_' not in csv_path:
        from core.data.extract_data import is_running_in_test
        if is_running_in_test():
            logging.warning(f"Test environment detected. Redirecting from production data path {csv_path}")
            logging.warning(f"Using TEST_ONLY_btc_data.csv instead")
            csv_path = 'core/data/TEST_ONLY_btc_data.csv'
    
    # Check if the file exists
    if os.path.exists(csv_path):
        logging.info(f"Loading BTC data from {csv_path}")
        try:
            # Try different separators
            for separator in [',', ';', '\t']:
                try:
                    btc_df = pd.read_csv(csv_path, index_col=0, parse_dates=True, sep=separator)
                    if not btc_df.empty:
                        logging.info(f"Loaded {len(btc_df)} records from {btc_df.index.min()} to {btc_df.index.max()}")
                        return btc_df
                except:
                    # Try the next separator
                    continue
            
            # If none of the separators worked, try the default
            btc_df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            logging.info(f"Loaded {len(btc_df)} records from {btc_df.index.min()} to {btc_df.index.max()}")
            return btc_df
        except Exception as e:
            logging.error(f"Failed to load data from CSV: {e}")
            logging.info("Attempting to fetch data from CoinMetrics instead...")
    else:
        logging.info(f"Local CSV not found at '{csv_path}'. Attempting to fetch data from CoinMetrics...")
    
    # If file doesn't exist or couldn't be read, try to fetch it from CoinMetrics
    try:
        # Import directly from core.data package to avoid circular imports
        from core.data import extract_btc_data
        btc_df = extract_btc_data(csv_path=csv_path)
        
        # Ensure we got valid data
        if btc_df is not None and not btc_df.empty:
            logging.info(f"Successfully fetched data from CoinMetrics: {len(btc_df)} records")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Save to the expected CSV location for future use
            btc_df.to_csv(csv_path)
            logging.info(f"Saved downloaded data to {csv_path} for future use")
            
            return btc_df
        else:
            raise RuntimeError("Downloaded data is empty or invalid")
            
    except ImportError as e:
        logging.error(f"CoinMetrics API client not available: {e}")
        raise RuntimeError("CoinMetrics API client is required but not installed. Run 'pip install coinmetrics-api-client'.")
    except requests.ConnectionError as e:
        logging.error(f"Connection error when fetching data from CoinMetrics: {e}")
        raise RuntimeError(f"Could not load BTC price data: Connection error - {str(e)}. Please check your internet connection.")
    except requests.Timeout as e:
        logging.error(f"Timeout error when fetching data from CoinMetrics: {e}")
        raise RuntimeError(f"Could not load BTC price data: Request timed out - {str(e)}. Please try again later.")
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error when fetching data from CoinMetrics: {e}")
        raise RuntimeError(f"Could not load BTC price data: Invalid JSON response - {str(e)}. API may be experiencing issues.")
    except Exception as e:
        logging.error(f"Failed to fetch data from CoinMetrics: {e}")
        raise RuntimeError(f"Could not load BTC price data: {str(e)}. Please check your internet connection or run extract_data.py manually to create the CSV file.")

if __name__ == "__main__":
    # Test data loading
    df = load_data()
    print(df.head())
