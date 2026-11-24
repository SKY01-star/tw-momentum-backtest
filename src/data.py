"""Load daily adjusted prices: download from Yahoo Finance once, then reuse a local cache."""

from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(__file__).resolve().parent.parent / "data" / "prices.csv"


def download_prices(tickers, start, end=None):
    """Download dividend- and split-adjusted daily closes for each ticker."""
    import yfinance as yf

    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    return prices.dropna(how="all")


def load_prices(tickers, start, end=None, refresh=False):
    """Return a DataFrame of prices (rows = dates, columns = tickers)."""
    if CACHE.exists() and not refresh:
        prices = pd.read_csv(CACHE, index_col=0, parse_dates=True)
        missing = set(tickers) - set(prices.columns)
        if not missing:
            return prices[tickers]
        print(f"Cache missing {len(missing)} tickers, downloading again...")

    prices = download_prices(tickers, start, end)
    CACHE.parent.mkdir(exist_ok=True)
    prices.to_csv(CACHE)
    return prices


def fix_unadjusted_splits(prices, limit=0.11, tolerance=0.06):
    """
    Repair stock splits that the data source failed to adjust for.

    TWSE stocks and ETFs have a 10% daily price limit, so a one-day move far
    beyond that is a corporate action or a data error, not a real return.
    If the move is close to a whole-number ratio (e.g. price / 4 after a
    1-for-4 split), all earlier prices are divided by that ratio.
    Any other large move is printed so it can be checked by hand.

    The date logged is where the source data breaks, which can differ from the
    real split date. Example: Yahoo's 0050 history adjusts the June 2025 split
    correctly but has a 4x price-scale break on 2 January 2014.
    """
    prices = prices.copy()
    log = []
    for ticker in prices.columns:
        series = prices[ticker].dropna()
        ratio = series / series.shift(1)
        for date, r in ratio[(ratio - 1).abs() > limit].items():
            k = round(1 / r) if r < 1 else round(r)
            split_like = k >= 2 and abs((r * k if r < 1 else r / k) - 1) < tolerance
            if split_like:
                factor = 1 / k if r < 1 else k
                prices.loc[prices.index < date, ticker] *= factor
                kind = f"1-for-{k}" if r < 1 else f"{k}-to-1 reverse"
                log.append(f"{ticker} {date:%Y-%m-%d}: {r - 1:+.1%} jump matches a {kind} split "
                           f"ratio (price-scale break in source data); earlier prices rescaled")
            else:
                log.append(f"{ticker} {date:%Y-%m-%d}: {r - 1:+.1%} one-day move, CHECK MANUALLY")
    return prices, log


def trim_to_listing(prices, listing_dates):
    """Blank out each stock's prices before its TWSE listing date."""
    prices = prices.copy()
    for ticker, date in listing_dates.items():
        if ticker in prices.columns:
            prices.loc[prices.index < pd.Timestamp(date), ticker] = np.nan
    return prices


def drop_incomplete_month(prices, today=None):
    """Remove the current calendar month so a partial month isn't treated as a full one."""
    today = pd.Timestamp(today or pd.Timestamp.today()).normalize()
    month_start = today.replace(day=1)
    return prices[prices.index < month_start]


def synthetic_prices(tickers, start="2012-01-01", end="2025-12-31", seed=42):
    """Random-walk prices for testing the pipeline offline. Not real data."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, end)
    drift = rng.normal(0.0003, 0.0002, len(tickers))
    shocks = rng.normal(drift, 0.018, (len(dates), len(tickers)))
    prices = pd.DataFrame(100 * np.exp(np.cumsum(shocks, axis=0)), index=dates, columns=tickers)
    # Simulate a late listing so the code has to handle missing history
    prices.iloc[: len(dates) // 3, -1] = np.nan
    return prices
