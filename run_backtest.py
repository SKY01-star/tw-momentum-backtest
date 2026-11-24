"""
Run the full backtest and write results.

    python run_backtest.py              # real data (downloads once, then cached)
    python run_backtest.py --refresh    # force a fresh download
    python run_backtest.py --synthetic  # fake random data, for testing offline
"""

import argparse
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config as cfg
from src.backtest import run_backtest
from src.data import (drop_incomplete_month, fix_unadjusted_splits, load_prices,
                      synthetic_prices, trim_to_listing)
from src.metrics import equity_curve, summary
from src.strategy import momentum_signal, to_monthly, top_n_weights

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def backtest_strategy(monthly, lookback, top_n):
    signal = momentum_signal(monthly[cfg.UNIVERSE], lookback, cfg.SKIP_MONTHS)
    weights = top_n_weights(signal, top_n)
    return run_backtest(monthly[cfg.UNIVERSE], weights, cfg.COMMISSION, cfg.TRANSACTION_TAX)


def equal_weight_universe(monthly, lookback):
    """Same eligible stocks, no momentum ranking - isolates what momentum adds."""
    signal = momentum_signal(monthly[cfg.UNIVERSE], lookback, cfg.SKIP_MONTHS)
    weights = top_n_weights(signal, top_n=len(cfg.UNIVERSE))
    return run_backtest(monthly[cfg.UNIVERSE], weights, cfg.COMMISSION, cfg.TRANSACTION_TAX)


def parameter_sweep(monthly):
    grid = pd.DataFrame(index=cfg.SWEEP_LOOKBACKS, columns=cfg.SWEEP_TOP_N, dtype=float)
    for lb in cfg.SWEEP_LOOKBACKS:
        for n in cfg.SWEEP_TOP_N:
            res = backtest_strategy(monthly, lb, n)
            grid.loc[lb, n] = summary(res["net"], rf=cfg.RISK_FREE_RATE)["Sharpe"]
    grid.index.name = "Lookback (months)"
    grid.columns.name = "Stocks held"
    return grid


def fmt(stats):
    pct = {"CAGR", "Volatility", "Max drawdown", "Best month", "Worst month",
           "Alpha (annual)", "Tracking error", "Months beating benchmark", "Annual turnover"}
    return stats.apply(lambda col: ["-" if pd.isna(v) else f"{v:.1%}" if k in pct else f"{v:.2f}"
                                    for k, v in col.items()])


def plot_results(curves, drawdowns, sweep):
    fig, ax = plt.subplots(figsize=(10, 5))
    for name, curve in curves.items():
        ax.plot(curve.index, curve, label=name, linewidth=2 if name == "Momentum" else 1.2)
    ax.set_yscale("log")
    ax.set_title("Growth of NT$1 (log scale, after costs)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "equity_curve.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 3.5))
    for name, dd in drawdowns.items():
        ax.fill_between(dd.index, dd, 0, alpha=0.35, label=name)
    ax.set_title("Drawdown from previous peak")
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.legend(loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "drawdown.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    im = ax.imshow(sweep.values, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(sweep.columns)), sweep.columns)
    ax.set_yticks(range(len(sweep.index)), sweep.index)
    ax.set_xlabel(sweep.columns.name)
    ax.set_ylabel(sweep.index.name)
    for i in range(sweep.shape[0]):
        for j in range(sweep.shape[1]):
            ax.text(j, i, f"{sweep.values[i, j]:.2f}", ha="center", va="center")
    ax.set_title("Net Sharpe ratio across settings")
    fig.colorbar(im)
    fig.tight_layout()
    fig.savefig(RESULTS / "parameter_sweep.png", dpi=150)
    plt.close(fig)


def update_readme(markdown):
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    block = f"<!-- RESULTS:START -->\n{markdown}\n<!-- RESULTS:END -->"
    text = re.sub(r"<!-- RESULTS:START -->.*<!-- RESULTS:END -->", lambda _: block, text, flags=re.S)
    readme.write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", action="store_true", help="use fake data (offline test)")
    parser.add_argument("--refresh", action="store_true", help="re-download prices")
    args = parser.parse_args()

    tickers = cfg.UNIVERSE + [cfg.BENCHMARK]
    if args.synthetic:
        prices = synthetic_prices(tickers)
    else:
        prices = load_prices(tickers, cfg.START_DATE, cfg.END_DATE, refresh=args.refresh)

    prices = drop_incomplete_month(prices)
    prices = trim_to_listing(prices, cfg.LISTING_DATES)
    prices, data_log = fix_unadjusted_splits(prices)
    print("Data checks:")
    print("\n".join(f"  {line}" for line in data_log) or "  no large one-day moves found")

    monthly = to_monthly(prices)
    RESULTS.mkdir(exist_ok=True)

    mom = backtest_strategy(monthly, cfg.LOOKBACK_MONTHS, cfg.TOP_N)
    ew = equal_weight_universe(monthly, cfg.LOOKBACK_MONTHS)
    bench = monthly[cfg.BENCHMARK].pct_change(fill_method=None).reindex(mom.index)

    mom_stats = summary(mom["net"], bench, cfg.RISK_FREE_RATE, mom["turnover"])
    stats = pd.DataFrame({
        "Momentum": mom_stats,
        "Equal-weight universe": summary(ew["net"].reindex(mom.index), bench, cfg.RISK_FREE_RATE),
        "0050 ETF": summary(bench, rf=cfg.RISK_FREE_RATE),
    }).reindex(mom_stats.index)
    sweep = parameter_sweep(monthly)

    curves = {"Momentum": equity_curve(mom["net"]),
              "Equal-weight universe": equity_curve(ew["net"].reindex(mom.index)),
              "0050 ETF": equity_curve(bench)}
    drawdowns = {k: v / v.cummax() - 1 for k, v in curves.items() if k != "Equal-weight universe"}
    plot_results(curves, drawdowns, sweep)

    period = f"{mom.index[0]:%b %Y} to {mom.index[-1]:%b %Y}"
    label = "SYNTHETIC DATA - pipeline test only, not real results" if args.synthetic \
        else f"Real data, {period}, net of trading costs"
    md = (f"**{label}** ({len(mom)} monthly rebalances)\n\n"
          f"{fmt(stats).to_markdown()}\n\n"
          f"Average trading cost drag: {mom['cost'].mean() * 12:.2%} per year\n\n"
          f"**Data checks** (TWSE's 10% daily limit means larger one-day moves are corporate actions or errors):\n\n"
          + ("\n".join(f"- {line}" for line in data_log) or "- none found") + "\n\n"
          f"![Equity curve](results/equity_curve.png)\n\n"
          f"![Drawdown](results/drawdown.png)\n\n"
          f"**Robustness check: net Sharpe ratio for other settings**\n\n"
          f"{sweep.round(2).to_markdown()}\n\n"
          f"![Parameter sweep](results/parameter_sweep.png)")

    (RESULTS / "summary.md").write_text(md, encoding="utf-8")
    mom.to_csv(RESULTS / "monthly_returns.csv")
    update_readme(md)
    print(fmt(stats).to_string())
    print("\nSharpe sweep:\n", sweep.round(2).to_string())


if __name__ == "__main__":
    main()
