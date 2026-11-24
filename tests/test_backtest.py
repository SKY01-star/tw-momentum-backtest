"""Checks that the backtest has no look-ahead bias and that costs and metrics are right."""

import numpy as np
import pandas as pd
import pytest

from src.backtest import run_backtest
from src.data import drop_incomplete_month, fix_unadjusted_splits, trim_to_listing
from src.metrics import max_drawdown, summary
from src.strategy import momentum_signal, top_n_weights


def monthly_index(n):
    return pd.date_range("2020-01-31", periods=n, freq="ME")


def test_signal_uses_only_past_prices():
    prices = pd.DataFrame({"A": np.arange(1, 25, dtype=float)}, index=monthly_index(24))
    signal = momentum_signal(prices, lookback=12, skip=1)
    # Changing this month's price must not change this month's signal
    shocked = prices.copy()
    shocked.iloc[-1] = 1_000
    pd.testing.assert_series_equal(signal.iloc[-1], momentum_signal(shocked, 12, 1).iloc[-1])
    assert signal.iloc[-1, 0] == pytest.approx(23 / 12 - 1)  # price[t-1] / price[t-12] - 1


def test_top_n_picks_strongest_and_sums_to_one():
    signal = pd.DataFrame({"A": [0.3], "B": [0.1], "C": [0.2], "D": [np.nan]})
    w = top_n_weights(signal, top_n=2).iloc[0]
    assert w["A"] == 0.5 and w["C"] == 0.5 and w["B"] == 0 and w["D"] == 0


def test_weights_earn_next_month_return():
    prices = pd.DataFrame({"A": [100.0, 110.0], "B": [100.0, 90.0]}, index=monthly_index(2))
    weights = pd.DataFrame({"A": [1.0, 1.0], "B": [0.0, 0.0]}, index=prices.index)
    res = run_backtest(prices, weights, commission=0, tax=0)
    assert res["gross"].iloc[0] == pytest.approx(0.10)


def test_costs_first_buy_and_full_switch():
    prices = pd.DataFrame({"A": [100.0] * 3, "B": [100.0] * 3}, index=monthly_index(3))
    weights = pd.DataFrame({"A": [1.0, 0.0, 0.0], "B": [0.0, 1.0, 1.0]}, index=prices.index)
    res = run_backtest(prices, weights, commission=0.001425, tax=0.003)
    assert res["cost"].iloc[0] == pytest.approx(0.001425)                 # buy A from cash
    assert res["cost"].iloc[1] == pytest.approx(0.001425 * 2 + 0.003)     # sell A, buy B
    assert res["turnover"].iloc[1] == pytest.approx(1.0)


def test_split_is_repaired():
    dates = pd.bdate_range("2025-06-09", periods=4)
    raw = pd.DataFrame({"0050.TW": [188.0, 188.65, 47.16, 47.5]}, index=dates)
    fixed, log = fix_unadjusted_splits(raw)
    returns = fixed["0050.TW"].pct_change().dropna()
    assert returns.abs().max() < 0.02          # the fake -75% day is gone
    assert fixed["0050.TW"].iloc[-1] == 47.5   # recent prices untouched
    assert "1-for-4" in log[0]


def test_odd_jump_is_flagged_not_changed():
    dates = pd.bdate_range("2025-01-01", periods=3)
    raw = pd.DataFrame({"X.TW": [100.0, 63.0, 64.0]}, index=dates)
    fixed, log = fix_unadjusted_splits(raw)
    pd.testing.assert_frame_equal(fixed, raw)
    assert "CHECK MANUALLY" in log[0]


def test_incomplete_month_dropped():
    dates = pd.bdate_range("2026-10-28", "2026-11-20")
    kept = drop_incomplete_month(pd.DataFrame({"A": 1.0}, index=dates), today="2026-11-22")
    assert kept.index.max() < pd.Timestamp("2026-11-01")


def test_max_drawdown_and_cagr():
    r = pd.Series([0.10, -0.50, 0.20])
    assert max_drawdown(r) == pytest.approx(-0.50)
    flat = pd.Series([0.01] * 12)
    assert summary(flat)["CAGR"] == pytest.approx(1.01 ** 12 - 1)


def test_prices_before_listing_removed():
    dates = pd.bdate_range("2019-03-25", periods=4)
    raw = pd.DataFrame({"6669.TW": [400.0, 420.0, 450.0, 460.0]}, index=dates)
    trimmed = trim_to_listing(raw, {"6669.TW": "2019-03-27"})
    assert trimmed["6669.TW"].isna().sum() == 2
    assert trimmed["6669.TW"].iloc[-1] == 460.0
