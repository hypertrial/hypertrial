# Hypertrial

Data Preparation:

Import libraries and set global parameters (e.g. backtest dates, 4‐year cycles, budget).

Load Bitcoin price data from the Coin Metrics API, format the dates, and rename the price column.

Helper Functions & Metrics:

Define functions to determine cycle boundaries, generate cycle labels, and calculate key metrics:

Min/Max SPD: Sats per dollar for worst-case (cycle high) and best-case (cycle low) scenarios.

Uniform SPD: Sats per dollar using equal daily investments.

Dynamic SPD: Sats per dollar using variable, feature-driven weights (derived from signals like the 200-day moving average).

Convert SPD values into percentiles to visualize performance relative to the extremes.

Cycle-by-Cycle Backtesting:

Iterate through each 4-year cycle, computing the above metrics for both the uniform and dynamic strategies.

Calculate the “excess SPD” (the extra sats per dollar gained by dynamic over uniform) and corresponding ROI improvements.

Visualization & Analysis:

Plot the SPD values on a log scale along with their percentiles, showing how the dynamic approach compares with uniform DCA.

Additional plots illustrate dynamic adjustments, weight distributions, and the ROI improvement per cycle.

Dynamic Strategy Framework:

Formally define dynamic DCA as a constrained optimization problem: maximize SPD while ensuring weights remain strictly positive and sum to one.

This framework guarantees daily investments (preserving DCA’s discipline) while allowing adaptive allocation based on market conditions.

Outcome & Storage:

Results indicate that even a simple dynamic adjustment can boost both SPD and ROI compared to uniform DCA.

Save the computed dynamic weights for further analysis and future tutorials.
