**Real data, Feb 2013 to Oct 2026, net of trading costs** (165 monthly rebalances)

|                          | Momentum   | Equal-weight universe   | 0050 ETF   |
|:-------------------------|:-----------|:------------------------|:-----------|
| CAGR                     | 37.5%      | 23.3%                   | 20.1%      |
| Volatility               | 29.7%      | 15.4%                   | 18.9%      |
| Sharpe                   | 1.17       | 1.35                    | 0.99       |
| Max drawdown             | -24.8%     | -18.0%                  | -29.2%     |
| Calmar                   | 1.51       | 1.29                    | 0.69       |
| Best month               | 45.3%      | 17.7%                   | 25.1%      |
| Worst month              | -18.6%     | -12.8%                  | -14.1%     |
| Beta vs benchmark        | 1.08       | 0.69                    | -          |
| Alpha (annual)           | 14.5%      | 8.4%                    | -          |
| Tracking error           | 21.7%      | 10.2%                   | -          |
| Information ratio        | 0.74       | 0.20                    | -          |
| Months beating benchmark | 60.0%      | 58.2%                   | -          |
| Annual turnover          | 279.3%     | -                       | -          |

Average trading cost drag: 1.64% per year

**Data checks** (TWSE's 10% daily limit means larger one-day moves are corporate actions or errors):

- 0050.TW 2014-01-02: -75.1% jump matches a 1-for-4 split ratio (price-scale break in source data); earlier prices rescaled
- 1301.TW 2025-08-04: -11.3% one-day move, CHECK MANUALLY
- 2360.TW 2025-08-04: +14.9% one-day move, CHECK MANUALLY
- 2603.TW 2022-09-19: -16.3% one-day move, CHECK MANUALLY
- 2609.TW 2021-04-07: +15.4% one-day move, CHECK MANUALLY
- 3661.TW 2017-10-02: +20.7% one-day move, CHECK MANUALLY

![Equity curve](results/equity_curve.png)

![Drawdown](results/drawdown.png)

**Robustness check: net Sharpe ratio for other settings**

|   Lookback (months) |    5 |   10 |   15 |
|--------------------:|-----:|-----:|-----:|
|                   3 | 1.08 | 1.12 | 1.26 |
|                   6 | 1.12 | 1.11 | 1.24 |
|                   9 | 1.12 | 1.24 | 1.32 |
|                  12 | 1.11 | 1.17 | 1.2  |

![Parameter sweep](results/parameter_sweep.png)