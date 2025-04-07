# main.py
from data import load_data
from user_strategy import construct_features, dynamic_rule_causal
from plots import plot_price_vs_ma200, plot_final_weights, plot_weight_sums_by_cycle
from spd import backtest_dynamic_dca
from config import BACKTEST_START

def main():
    # Load BTC data
    btc_df = load_data()
    print(btc_df.info())
    print(btc_df.head())

    # Compute features and strategy weights using the user-supplied file
    df_features = construct_features(btc_df).loc[BACKTEST_START:]
    weights = dynamic_rule_causal(btc_df)

    # Plot results
    plot_price_vs_ma200(df_features, weights=weights)
    plot_final_weights(weights)
    plot_weight_sums_by_cycle(weights)

    # Run SPD backtest and plot results
    strategy_name = "Threshold-Based DCA"
    backtest_dynamic_dca(btc_df, strategy_name=strategy_name)

if __name__ == '__main__':
    main()
