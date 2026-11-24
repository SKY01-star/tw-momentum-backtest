"""Performance statistics for a series of monthly returns."""

import numpy as np
import pandas as pd


def equity_curve(returns):
    return (1 + returns).cumprod()


def max_drawdown(returns):
    curve = equity_curve(returns)
    return (curve / curve.cummax() - 1).min()


def summary(returns, benchmark=None, rf=0.0, turnover=None):
    """Annualised statistics. `returns` and `benchmark` are monthly."""
    returns = returns.dropna()
    years = len(returns) / 12
    cagr = equity_curve(returns).iloc[-1] ** (1 / years) - 1
    vol = returns.std() * np.sqrt(12)
    excess = returns - rf / 12
    sharpe = excess.mean() / returns.std() * np.sqrt(12)
    mdd = max_drawdown(returns)

    stats = {
        "CAGR": cagr,
        "Volatility": vol,
        "Sharpe": sharpe,
        "Max drawdown": mdd,
        "Calmar": cagr / abs(mdd) if mdd < 0 else np.nan,
        "Best month": returns.max(),
        "Worst month": returns.min(),
    }

    if benchmark is not None:
        both = pd.concat([returns, benchmark], axis=1, join="inner").dropna()
        r, b = both.iloc[:, 0], both.iloc[:, 1]
        active = r - b
        beta = np.cov(r, b)[0, 1] / b.var()
        stats["Beta vs benchmark"] = beta
        stats["Alpha (annual)"] = (r.mean() - beta * b.mean()) * 12
        stats["Tracking error"] = active.std() * np.sqrt(12)
        stats["Information ratio"] = active.mean() / active.std() * np.sqrt(12)
        stats["Months beating benchmark"] = (active > 0).mean()

    if turnover is not None:
        stats["Annual turnover"] = turnover.mean() * 12

    return pd.Series(stats)
