#!/usr/bin/env python3
import pandas as pd
from datetime import datetime
import logging
import matplotlib.pyplot as plt
import numpy as np

try:
    from coinmetrics.api_client import CoinMetricsClient
except ImportError:
    raise ImportError("coinmetrics.api_client module is required. Install it via pip if necessary.")

def main():
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    client = CoinMetricsClient()

    asset = 'btc'
    metric = 'PriceUSD'
    start_time = '2010-01-01'
    end_time = datetime.today().strftime('%Y-%m-%d')
    frequency = '1d'

    logging.info("Fetching BTC ReferenceRate...")
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

    print(btc_df.info())
    print(btc_df)

    # Save DataFrame as a Parquet file
    btc_df.to_parquet("btc_data.parquet")

    BACKTEST_START = '2013-01-01'
    BACKTEST_END = '2024-12-31'

if __name__ == '__main__':
    main()
