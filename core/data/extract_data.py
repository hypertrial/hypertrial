# extract_data.py
import pandas as pd
import logging
from datetime import datetime
import requests
import json
import os
import sys

try:
    from coinmetrics.api_client import CoinMetricsClient
except ImportError:
    raise ImportError("coinmetrics.api_client module is required. Install it via pip if necessary.")

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def is_running_in_test():
    """
    Detect if we're running in a test environment to avoid overwriting production data.
    
    Returns:
        bool: True if running in test, False otherwise
    """
    # Check if pytest is running
    if any("pytest" in arg for arg in sys.argv):
        return True
    
    # Check if the calling frame comes from a test file
    import inspect
    frames = inspect.stack()
    for frame in frames:
        if 'test_' in frame.filename:
            return True
    
    return False

def extract_btc_data(save_to_csv=True, timeout=30, csv_path=None):
    """
    Extract Bitcoin price data from CoinMetrics and optionally save it as a CSV file.
    
    Args:
        save_to_csv (bool): Whether to save the data as a CSV file
        timeout (int): Timeout for API requests in seconds
        csv_path (str, optional): Custom path to save the CSV file
        
    Returns:
        pandas.DataFrame: DataFrame with Bitcoin price data
        
    Raises:
        Exception: If there was an error fetching data
    """
    try:
        # Create client with or without timeout based on library version
        try:
            # Try with timeout parameter
            client = CoinMetricsClient(timeout=timeout)
        except TypeError:
            # If timeout is not supported, create without timeout
            client = CoinMetricsClient()
            
        asset = 'btc'
        metric = 'PriceUSD'
        start_time = '2010-01-01'
        end_time = datetime.today().strftime('%Y-%m-%d')
        frequency = '1d'
        
        logging.info(f"Fetching BTC data from {start_time} to {end_time}...")
        
        # Attempt to retrieve data from CoinMetrics API
        try:
            response = client.get_asset_metrics(
                assets=asset,
                metrics=[metric],
                frequency=frequency,
                start_time=start_time,
                end_time=end_time
            )
            
            # Check if response is None or if it appears to be empty
            if response is None:
                raise ValueError("Received None response from CoinMetrics API")
                
            # Convert to dataframe and check if it's empty
            btc_df = response.to_dataframe()
            if btc_df is None or btc_df.empty:
                raise ValueError("Received empty dataframe from CoinMetrics API")
            
        except requests.ConnectionError as e:
            logging.error(f"Connection error while fetching data from CoinMetrics API: {str(e)}")
            raise requests.ConnectionError(f"Failed to connect to CoinMetrics API: {str(e)}")
        except requests.Timeout as e:
            logging.error(f"Timeout error while fetching data from CoinMetrics API: {str(e)}")
            raise requests.Timeout(f"Request timed out when connecting to CoinMetrics API: {str(e)}")
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error while fetching data from CoinMetrics API: {str(e)}")
            raise json.JSONDecodeError(f"Invalid JSON response from CoinMetrics API", e.doc, e.pos)
        except ValueError as e:
            logging.error(f"Error while fetching data from CoinMetrics API: {str(e)}")
            raise  # Re-raise the ValueError directly
        except Exception as e:
            logging.error(f"Error while fetching data from CoinMetrics API: {str(e)}")
            raise Exception(f"Failed to retrieve data from CoinMetrics API: {str(e)}")

        # Process the dataframe
        btc_df = btc_df.rename(columns={metric: 'Close'})
        btc_df['time'] = pd.to_datetime(btc_df['time']).dt.normalize()
        btc_df['time'] = btc_df['time'].dt.tz_localize(None)
        btc_df.set_index('time', inplace=True)
        btc_df = btc_df[['Close']]
        btc_df = btc_df.rename(columns={"Close": "btc_close"})
        
        # Check if dataframe is valid and has sufficient data
        if btc_df.empty:
            raise ValueError("Downloaded dataframe is empty")
            
        if len(btc_df) < 100:  # Reasonable minimum for Bitcoin historical data
            logging.warning(f"Downloaded data has only {len(btc_df)} records, which seems unusually low")
        
        # Save to CSV if requested
        if save_to_csv:
            # Determine the CSV path
            if csv_path is None:
                csv_path = 'core/data/btc_price_data.csv'
            
            # SAFEGUARD: Detect if we're running in a test environment
            if is_running_in_test() and 'TEST_ONLY' not in csv_path and 'test_' not in csv_path:
                logging.warning(f"Detected test environment. Refusing to overwrite production data file at {csv_path}")
                logging.warning(f"Saving test data to TEST_ONLY_btc_data.csv instead")
                csv_path = 'core/data/TEST_ONLY_btc_data.csv'
            
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            # Save to CSV
            btc_df.to_csv(csv_path)
            logging.info(f"Saved BTC data to {csv_path}")
        
        logging.info(f"Total records: {len(btc_df)}")
        logging.info(f"Date range: {btc_df.index.min()} to {btc_df.index.max()}")
        
        return btc_df
        
    except ImportError as e:
        logging.error(f"CoinMetrics API client not properly installed: {str(e)}")
        raise ImportError("Please install the CoinMetrics API client: pip install coinmetrics-api-client")
    except requests.ConnectionError as e:
        logging.error(f"Connection error in extract_btc_data: {str(e)}")
        raise
    except requests.Timeout as e:
        logging.error(f"Timeout error in extract_btc_data: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in extract_btc_data: {str(e)}")
        raise
    except ValueError as e:
        logging.error(f"Error in extract_btc_data: {str(e)}")
        raise  # Re-raise ValueError directly
    except Exception as e:
        logging.error(f"Error in extract_btc_data: {str(e)}")
        raise

if __name__ == '__main__':
    extract_btc_data() 