"""
Data loading utilities for the Stacking Sats library.
"""
import pandas as pd
import os
from typing import Optional
from pathlib import Path

def _get_data_dir() -> str:
    """
    Get the data directory for storing BTC price data.
    
    Returns:
        str: Path to the data directory
    """
    # Get the module directory (stacking_sats/core)
    module_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Go up a level to stacking_sats
    package_dir = module_dir.parent
    
    # Data directory is stacking_sats/data
    data_dir = os.path.join(package_dir, 'data')
    
    # Create the directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    return data_dir

def load_btc_data(file_path: Optional[str] = None, force_download: bool = False) -> pd.DataFrame:
    """
    Load BTC price data from parquet file.
    
    Parameters:
        file_path (str, optional): Path to parquet file
            If None, will look for btc_usd_daily.parquet in the data directory
        force_download (bool): Force download new data even if file exists
    
    Returns:
        pd.DataFrame: DataFrame with bitcoin price data
    """
    if file_path is None:
        # Try to find the default file path
        data_dir = _get_data_dir()
        file_path = os.path.join(data_dir, 'btc_usd_daily.parquet')
    
    # Check if we need to download data
    if force_download or not os.path.exists(file_path):
        print(f"Data file not found or force_download=True. Downloading BTC data...")
        try:
            btc_df = _download_btc_data(save_path=file_path)
            return btc_df
        except Exception as e:
            raise Exception(f"Failed to download BTC data: {str(e)}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found at {file_path}")
    
    # Load the parquet file
    print(f"Loading data from {file_path}")
    btc_df = pd.read_parquet(file_path)
    
    # Print summary
    print(f"Loaded data with shape: {btc_df.shape}")
    print(f"Columns: {btc_df.columns}")
    print(f"Date range: {btc_df.index.min()} to {btc_df.index.max()}")
    
    return btc_df

def _download_btc_data(save_path: Optional[str] = None) -> pd.DataFrame:
    """
    Download BTC price data from an API.
    
    Parameters:
        save_path (str, optional): Path to save the data
    
    Returns:
        pd.DataFrame: DataFrame with bitcoin price data
    """
    try:
        return fetch_bitcoin_api_data(save_path=save_path)
    except ImportError:
        raise Exception("cryptocompare package is required for automatic data download")

def load_csv_data(file_path: str, 
                  date_column: str = 'date',
                  price_column: str = 'close',
                  rename_price: bool = True) -> pd.DataFrame:
    """
    Load price data from CSV file.
    
    Parameters:
        file_path (str): Path to CSV file
        date_column (str): Name of date column
        price_column (str): Name of price column
        rename_price (bool): Whether to rename price column to 'btc_close'
    
    Returns:
        pd.DataFrame: DataFrame with price data
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found at {file_path}")
    
    # Load the CSV file
    df = pd.read_csv(file_path)
    
    # Parse dates and set as index
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.set_index(date_column)
    
    # Sort by date
    df = df.sort_index()
    
    # Rename price column if specified
    if rename_price and price_column != 'btc_close':
        df = df.rename(columns={price_column: 'btc_close'})
    
    # Print summary
    print(f"Loaded CSV with shape: {df.shape}")
    print(f"Columns: {df.columns}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    return df

def fetch_bitcoin_api_data(start_date: str = '2010-01-01', 
                           end_date: Optional[str] = None,
                           save_path: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch Bitcoin price data from public API.
    
    This function requires the cryptocompare library:
    pip install cryptocompare
    
    Parameters:
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str, optional): End date in YYYY-MM-DD format
        save_path (str, optional): Path to save the data to parquet
    
    Returns:
        pd.DataFrame: DataFrame with Bitcoin price data
    """
    try:
        import cryptocompare
    except ImportError:
        raise ImportError("cryptocompare package is required. Install it with: pip install cryptocompare")
    
    import datetime
    
    # Parse dates
    start_ts = pd.to_datetime(start_date)
    
    if end_date is None:
        end_ts = datetime.datetime.now()
    else:
        end_ts = pd.to_datetime(end_date)
    
    # Calculate number of days
    days = (end_ts - start_ts).days + 1
    
    # Fetch daily data
    btc_data = cryptocompare.get_historical_price_day('BTC', 'USD', limit=days, 
                                                      toTs=end_ts)
    
    # Convert to DataFrame
    df = pd.DataFrame(btc_data)
    
    # Convert timestamp to datetime and set as index
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.set_index('time')
    
    # Sort by date
    df = df.sort_index()
    
    # Rename columns
    df = df.rename(columns={'close': 'btc_close'})
    
    # Keep only the close price
    df = df[['btc_close']]
    
    # Save to file if path provided
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        df.to_parquet(save_path)
        print(f"Saved data to {save_path}")
    
    return df 