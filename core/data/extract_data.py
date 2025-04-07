# extract_data.py
import pandas as pd
import logging
from datetime import datetime

try:
    from coinmetrics.api_client import CoinMetricsClient
except ImportError:
    raise ImportError("coinmetrics.api_client module is required. Install it via pip if necessary.")

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

def extract_btc_data():
    """
    Extract Bitcoin price data from CoinMetrics and save it as a CSV file.
    """
    client = CoinMetricsClient()
    asset = 'btc'
    metric = 'PriceUSD'
    start_time = '2010-01-01'
    end_time = datetime.today().strftime('%Y-%m-%d')
    frequency = '1d'
    
    logging.info(f"Fetching BTC data from {start_time} to {end_time}...")
    
    btc_df = client.get_asset_metrics(
        assets=asset,
        metrics=[metric],
        frequency=frequency,
        start_time=start_time,
        end_time=end_time
    ).to_dataframe()

    btc_df = btc_df.rename(columns={metric: 'Close'})
    btc_df['time'] = pd.to_datetime(btc_df['time']).dt.normalize()
    btc_df['time'] = btc_df['time'].dt.tz_localize(None)
    btc_df.set_index('time', inplace=True)
    btc_df = btc_df[['Close']]
    btc_df = btc_df.rename(columns={"Close": "btc_close"})
    
    # Create data directory if it doesn't exist
    import os
    os.makedirs('core/data', exist_ok=True)
    
    # Save to CSV
    csv_path = 'core/data/btc_price_data.csv'
    btc_df.to_csv(csv_path)
    logging.info(f"Saved BTC data to {csv_path}")
    logging.info(f"Total records: {len(btc_df)}")
    logging.info(f"Date range: {btc_df.index.min()} to {btc_df.index.max()}")
    
    return btc_df

if __name__ == '__main__':
    extract_btc_data() 