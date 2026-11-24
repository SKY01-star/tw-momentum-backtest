"""Simulate holding the target weights month by month, after trading costs."""

import pandas as pd


def run_backtest(monthly_prices, target_weights, commission=0.001425, tax=0.003):
    """
    Weights chosen at the end of month t earn the returns of month t+1.

    Costs are charged when rebalancing: commission on every trade, plus the
    securities transaction tax on sells. Trades are measured against the
    *drifted* weights (what we actually held after last month's price moves).

    Returns a DataFrame with gross return, cost, net return, and turnover per month.
    """
    returns = monthly_prices.pct_change(fill_method=None).fillna(0.0)
    tickers = target_weights.columns
    held = pd.Series(0.0, index=tickers)  # start in cash
    rows = []

    dates = target_weights.index
    for i in range(len(dates) - 1):
        today, next_month = dates[i], dates[i + 1]
        target = target_weights.loc[today]
        if target.sum() == 0:  # not enough history yet: stay in cash
            continue

        trades = target - held
        buys = trades.clip(lower=0).sum()
        sells = -trades.clip(upper=0).sum()
        cost = commission * (buys + sells) + tax * sells

        r = returns.loc[next_month, tickers]
        gross = (target * r).sum()
        net = (1 - cost) * (1 + gross) - 1

        rows.append({"date": next_month, "gross": gross, "cost": cost,
                     "net": net, "turnover": sells})

        # Weights drift with prices until the next rebalance
        grown = target * (1 + r)
        held = grown / grown.sum()

    return pd.DataFrame(rows).set_index("date")
