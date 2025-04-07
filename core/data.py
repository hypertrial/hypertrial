# data.py
import pandas as pd
import os
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_data():
    """
    Load Bitcoin price data from a local CSV file.
    If the file doesn't exist, try to fetch it from CoinMetrics.
    """
    csv_path = 'core/data/btc_price_data.csv'
    
    # Check if the file exists
    if os.path.exists(csv_path):
        logging.info(f"Loading BTC data from {csv_path}")
        btc_df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        logging.info(f"Loaded {len(btc_df)} records from {btc_df.index.min()} to {btc_df.index.max()}")
        return btc_df
    
    # If file doesn't exist, try to fetch it from CoinMetrics
    logging.info("Local CSV not found. Attempting to fetch data from CoinMetrics...")
    try:
        from core.data.extract_data import extract_btc_data
        return extract_btc_data()
    except Exception as e:
        logging.error(f"Failed to fetch data from CoinMetrics: {e}")
        raise RuntimeError("Could not load BTC price data. Please run extract_data.py first to create the CSV file.")

if __name__ == "__main__":
    # Test data loading
    df = load_data()
    print(df.head())
