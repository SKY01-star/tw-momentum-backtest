"""All settings for the backtest live here, so experiments never require editing the logic."""

# ---- Universe -------------------------------------------------------------
# 50 large Taiwan-listed companies (Yahoo Finance tickers end in ".TW").
# NOTE: this is a fixed list of today's large caps, not the historical
# Taiwan 50 membership. That creates survivorship bias (see README).
UNIVERSE = [
    "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2303.TW", "3711.TW",
    "2412.TW", "2881.TW", "2882.TW", "2891.TW", "2886.TW", "2884.TW", "2885.TW",
    "2892.TW", "5880.TW", "2880.TW", "2883.TW", "2887.TW", "2890.TW", "1216.TW",
    "2357.TW", "3231.TW", "2345.TW", "3034.TW", "2002.TW", "1301.TW", "1303.TW",
    "3008.TW", "2379.TW", "2395.TW", "4938.TW", "2301.TW", "2603.TW", "2609.TW",
    "2615.TW", "2207.TW", "1101.TW", "2912.TW", "3045.TW", "4904.TW", "6669.TW",
    "3017.TW", "3661.TW", "2059.TW", "2360.TW", "1590.TW", "6505.TW", "2327.TW",
    "3037.TW",
]
BENCHMARK = "0050.TW"  # Yuanta Taiwan Top 50 ETF

START_DATE = "2012-01-01"
END_DATE = None  # None = up to today

# TWSE listing dates for stocks that traded elsewhere first. Yahoo includes
# their earlier emerging-board (興櫃) prices, where there is no daily price
# limit and few investors could trade. Prices before these dates are ignored.
LISTING_DATES = {
    "3661.TW": "2014-10-28",  # Alchip
    "6669.TW": "2019-03-27",  # Wiwynn
}

# ---- Strategy -------------------------------------------------------------
LOOKBACK_MONTHS = 12  # momentum measured over the past 12 months...
SKIP_MONTHS = 1       # ...skipping the most recent month (short-term reversal)
TOP_N = 10            # hold the 10 strongest stocks, equal weight

# ---- Trading costs (Taiwan retail, before broker discounts) ---------------
COMMISSION = 0.001425       # 0.1425% brokerage fee, charged on buys and sells
TRANSACTION_TAX = 0.003     # 0.3% securities transaction tax, sells only

# ---- Reporting ------------------------------------------------------------
RISK_FREE_RATE = 0.015      # annual, roughly Taiwan 1-year deposit rate
SWEEP_LOOKBACKS = [3, 6, 9, 12]
SWEEP_TOP_N = [5, 10, 15]
