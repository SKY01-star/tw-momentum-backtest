"""Turn month-end prices into a momentum signal and target portfolio weights."""

import pandas as pd


def to_monthly(prices):
    """Last available price in each calendar month."""
    return prices.resample("ME").last()


def momentum_signal(monthly_prices, lookback=12, skip=1):
    """
    Return from (lookback) months ago to (skip) months ago.

    At month t with lookback=12, skip=1: price[t-1] / price[t-12] - 1.
    Only past prices are used, so there is no look-ahead.
    """
    return monthly_prices.shift(skip) / monthly_prices.shift(lookback) - 1


def top_n_weights(signal, top_n=10):
    """Equal-weight the top_n stocks by signal each month; everything else gets 0."""
    ranks = signal.rank(axis=1, ascending=False, method="first")
    picks = (ranks <= top_n) & signal.notna()
    weights = picks.astype(float)
    return weights.div(weights.sum(axis=1), axis=0).fillna(0.0)
