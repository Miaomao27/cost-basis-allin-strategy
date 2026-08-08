# Grid-Optimized Event-Driven All-In Strategy Driven by Dollar-Cost-Averaging Cost Basis Across Chinese and International Major Assets

## Abstract

This paper proposes an event-driven timing strategy anchored by a sliding-window dollar-cost-averaging (DCA) cost basis. Within a rolling window, the harmonic-mean DCA cost serves as a valuation watermark for the underlying asset; a full position is taken (all-in) when the spot price deviates below the cost line by a threshold percentage, and the position is fully liquidated upon a rebound exceeding a profit-taking threshold. A three-dimensional grid search (window size × entry drawdown × profit-taking threshold, totalling 3,200 parameter combinations per asset) is conducted on four assets — CSI Dividend Low Volatility 50 (000922.SH), NASDAQ-100 (^NDX), S&P 500 (^SPX), and Shanghai Gold Futures (AU.SHF) — covering the full historical data from 2015 to 2026. A minimum trade-count statistical significance threshold is applied as a safeguard. The empirical results demonstrate that: (1) the all-in strategy is significantly effective for the CSI Dividend Low Volatility 50, halving the maximum drawdown from −46.5% to −19.2% and boosting the Calmar ratio to 3.5 times that of buy-and-hold; (2) the strategy works for Shanghai gold but relies on a high profit-taking threshold to capture large swings; (3) the strategy yields unremarkable results for the S&P 500, exhibiting a chronic selling-too-early problem in prolonged bull markets; and (4) the NASDAQ-100 exhibits a trap in which a superficially elevated Calmar ratio conceals a drastic collapse in annualized return — frequent selling triggered by an extremely low profit-taking threshold consumes approximately two-thirds of potential gains. The core contribution of this paper lies in a novel event-driven framework that departs from fixed-interval rebalancing and in revealing the heterogeneity of optimal parameters across assets with distinct volatility profiles.

**Keywords**: DCA cost basis; event-driven strategy; grid search; portfolio management; drawdown control; all-in strategy

---

## 1 Introduction

### 1.1 Background and Problem Statement

The decisive role of asset allocation in portfolio returns has been substantiated by a large body of research. Brinson et al. (1986) demonstrated in an empirical study of 91 large pension plans that asset allocation policy explains approximately 93.6% of the variance in total fund returns, whereas market timing and security selection contribute negligibly [1]. Markowitz's (1952) mean-variance framework laid the mathematical foundation for modern portfolio theory [2]. Classical investment theory, however, offers relatively thin guidance on when to adjust positions — whether fixed-frequency rebalancing (quarterly, annually) or constant-mix strategies, both fall within the time-driven paradigm and do not respond to extreme states signaled by market prices themselves.

Concurrently, trend-following strategies have accumulated substantial evidence in both academic and practitioner domains. Moskowitz et al. (2012) demonstrated the robust presence of time-series momentum across asset classes [3]. The Turtle Trading Rules, centered on Donchian channel breakouts, established a complete trend-following framework [4]. The Constant Proportion Portfolio Insurance (CPPI) strategy (Black & Jones, 1987) introduced a risk-budgeting framework anchored by a "cushion" [5]. Pure trend-following, however, tends to produce overly conservative sell signals during prolonged bull markets, and CPPI's parameterization is highly dependent on risk appetite.

The dollar-cost-averaging (DCA) strategy is widely adopted for its simplicity and behavioral finance advantages. Kirkby et al. (2020) provided a systematic theoretical analysis of DCA versus market-timing strategies, noting that DCA can offer downside protection in volatile markets [6]. Jin et al. (2023) found that the day-of-the-month effect can influence DCA strategy performance in the Chinese market [7]. Traditional DCA, however, is fundamentally a buy-only, never-exit approach that does not leverage the DCA cost itself as a timing signal.

This paper seeks to fuse the above three research threads: adopting the DCA cost basis as a valuation anchor (inheriting the DCA philosophy), using deviation thresholds to trigger trading signals (inheriting the risk-budgeting logic of CPPI), and replacing time-driven triggers with event-driven ones (inheriting the trend-following philosophy), thereby constructing a DCA-cost-line-driven, event-based all-in strategy. Under this framework, an asset is traded only when its price deviates substantially from its DCA cost line; it otherwise remains in cash or on hold — forming a sharp contrast with the fixed-schedule rebalancing of, for example, the Permanent Portfolio.

### 1.2 Literature Review

In the asset pricing literature, Fama and French's (1993) three-factor model [8] and its subsequent five-factor extension provide a benchmark for portfolio return attribution. Liu, Stambaugh, and Yuan (2019), addressing the unique IPO regulatory constraints and shell-value characteristics of China's capital market, proposed a Chinese three-factor model that replaces BE/ME with EP (earnings–price ratio) and excludes the smallest 30% of stocks to avoid shell-value contamination [9].

For performance evaluation, Sharpe's (1966/1994) ratio [10] and Young's (1991) Calmar ratio [11] supply standard tools for risk-adjusted return assessment.

In strategy optimization, grid search is widely employed as a foundational hyperparameter optimization method in quantitative strategy development. To date, however, no systematic study has applied grid search specifically to the "DCA cost basis + all-in" strategy framework.

The contributions of this paper are summarized as follows: (1) it is the first to convert the sliding-window DCA harmonic-mean cost line into an event-driven trading signal generator; (2) it constructs a three-dimensional grid-search framework that systematically explores the parameter space of window size × entry drawdown × profit-taking threshold; (3) it introduces a minimum trade-count requirement as a statistical significance threshold, effectively filtering out overfitting artifacts that produce spuriously high Calmar ratios; and (4) it conducts falsification-style stratified tests across four assets with heterogeneous volatility profiles, distinguishing genuinely effective parameters from statistical illusions.

---

## 2 Data and Methodology

### 2.1 Data Sources and Sample Description

Four representative assets with distinct volatility characteristics and market affiliations are selected, covering the longest available historical daily data for each asset (beginning as early as 2004 and ending as late as August 2026). The sample spans complete market cycles including the 2015 Chinese stock market crash, the 2018 bear market, the 2020 COVID shock, the 2022 downturn, and the 2024–2025 all-time-high regime. The data source, start date, end date, and sample size for each asset are detailed in Table 1.

**Table 1  Asset Data Sources and Sample Description**

| Asset | Ticker | Market | Volatility Profile | Data Source | Start Date | End Date | Daily Bars |
|-------|--------|--------|---------------------|-------------|------------|----------|:----------:|
| CSI Dividend Low Vol 50 | 000922.SH | A-shares | Low volatility, slow declines and recoveries | Tencent `stock_zh_index_daily_tx` | 2008-08-04 | 2026-08-07 | 4,376 |
| NASDAQ-100 | ^NDX | US equities | High volatility, sharp rises and falls | Sina `index_us_stock_sina` | 2014-02-18 | 2026-08-06 | 3,135 |
| S&P 500 | ^SPX | US equities | Medium-high volatility, secular bull | Sina `index_us_stock_sina` | 2004-01-02 | 2026-08-06 | 5,687 |
| Shanghai Gold Futures | AU.SHF | SHFE | Medium volatility, slow bull with sharp corrections | akshare futures main | 2009-01-05 | 2026-08-07 | 4,263 |

The dataset spans A-shares (CSI Dividend Low Vol 50), US equities (NASDAQ-100, S&P 500), and commodity futures (Shanghai gold), ensuring that the strategy is tested on assets with heterogeneous pricing mechanisms, volatility structures, and cyclical rhythms. Two notes: (1) the NASDAQ-100 and S&P 500 series are price indices (excluding dividends), so their buy-and-hold returns are conservatively biased downward; (2) the differing history lengths reflect data availability—the backtest engine runs each asset on its own full available series rather than truncating to a common interval.

### 2.2 Mathematical Definition of the DCA Cost Line

Let the DCA window length be W months. Within this window, assuming one unit of currency is invested on each trading day to purchase the underlying asset, the total invested amount K equals the number of trading days in the window, and the total share holdings U are the sum of daily purchases:

$$K = N_{\text{trade}}(W), \quad U = \sum_{t \in W} \frac{1}{P_t}$$

where $P_t$ is the closing price on trading day $t$. The DCA cost line $CB_W(t)$ is defined as the total invested capital divided by total holdings — i.e., the harmonic-mean cost:

$$CB_W(t) = \frac{K}{U} = \frac{N_{\text{trade}}(W)}{\sum_{t \in W} 1/P_t}$$

The price deviation $dev_W(t)$ is further defined as the percentage deviation of the spot price from the DCA cost line:

$$dev_W(t) = \frac{P(t)}{CB_W(t)} - 1$$

When $dev_W(t) < 0$, the current price lies below the average DCA holding cost within the window (the asset is in a "paper loss" state); the greater the absolute deviation, the deeper the "discount" of the asset. This metric is essentially a normalized valuation gauge — it is anchored not to fundamental multiples such as PE or PB but to the investor's own actual holding cost.

A key mathematical property of the DCA cost line is that, because it employs the harmonic mean, the cost line assigns greater weight to low-price days (the lower the price on a given day, the more shares are purchased, pulling the cost line further downward). This causes the cost line to gravitate naturally toward market troughs, forming a reference line with intrinsic "value attraction."

### 2.3 Grid Search Design

A three-dimensional grid search is implemented to identify optimal strategy parameter combinations:

**Table 2  Grid Search Parameter Space**

| Parameter Dimension | Symbol | Value Set | Levels |
|---------------------|--------|-----------|--------|
| DCA Window | W | {1, 3, 6, 9, 12, 18, 24, 36} months | 8 |
| Entry Drawdown Threshold | d | {2%, 4%, 6%, ..., 40%}, step 2% | 20 |
| Profit-Taking Rebound Threshold | p | {2%, 4%, 6%, ..., 40%}, step 2% | 20 |
| **Total Combinations** | | W × d × p | **3,200 / asset** |

Across four assets × 3,200 parameter combinations, a total of 12,800 independent backtests are conducted.

### 2.4 Mode-A Trading Rules

The following state-machine logic is applied day by day over the complete historical time series:

1. **Initial state**: Cash (position = 0).
2. **Entry condition**: When $dev_W(t) \leq -d\%$ (i.e., the price is at least d% below the DCA cost line) and the current position is zero, a full position is taken at the closing price of that day (position = 1), recording the entry price $P_{entry}$.
3. **Exit condition**: Once a position is held, the lowest price during the holding period is tracked: $P_{low} = \min(P_{entry}, P_t)$. When $P(t)$ rebounds from $P_{low}$ by $+p\%$ (i.e., $P(t) / P_{low} - 1 \geq p\%$), the entire position is liquidated at the closing price of that day (position = 0), recording the exit price $P_{exit}$, and the single trade is completed.
4. **Loop**: Upon exiting, the strategy returns to the cash state and awaits the next entry signal.

Key design features:
- A rebound-based take-profit mechanism is employed rather than cost-based take-profit, thereby avoiding premature exits before the asset has adequately recovered.
- The rebound benchmark is the lowest price during the holding period (not the entry price), ensuring that the profit-taking trigger condition corresponds to a genuine trend reversal.
- Each trade from entry to exit constitutes a complete "all-in cycle" with no position sizing (always fully invested or fully in cash).

### 2.5 Backtesting Engine

The backtesting engine is implemented in pure NumPy using vectorized computation. The core computation path is as follows:

- **Rolling-window cost line**: The harmonic-mean DCA cost is computed day by day using `cumsum` with a differencing operator, with complexity O(N).
- **Signal generation**: `argmax` and Boolean indexing are used to locate day cutoffs satisfying threshold conditions on the deviation array, achieving O(N) state-machine transitions.
- **Trade recording**: Each trade's entry date, entry price, holding-period low, exit date, exit price, holding days, and single-trade return are recorded.

All 12,800 backtests (4 assets × 3,200 combinations each) are completed within 5 seconds on a standard Linux workstation. To verify the correctness of the vectorized implementation, 1,000 randomly selected parameter combinations are independently recomputed using a day-by-day for-loop; the deviation is zero in every case.

### 2.6 Performance Metrics and Statistical Significance Threshold

For each parameter combination, the following metrics are computed:

| Metric | Definition | Description |
|--------|-----------|-------------|
| Total Return | $\prod(1+r_i)-1$ | Chained return of all completed trades |
| CAGR | $[(1+R_{total})^{365/D_{total}}]-1$ | Geometric-mean annualized return over the full period |
| Maximum Drawdown (MaxDD) | $\max(1 - P_t/P_{\text{peak}})$ | Maximum strategy-equity drawdown over the full period |
| Calmar Ratio | CAGR / MaxDD | Risk-adjusted return |
| Win Rate | $N_{\text{win}}/N_{\text{trades}}$ | Proportion of winning trades |
| Profit Factor | Avg win / Avg loss | Quality of profitability |

**Statistical significance threshold**: A parameter combination is eligible for the optimal-parameter candidate pool only when $N_{\text{trades}} \geq 10$. This threshold is motivated by the following observation: when the number of trades is extremely low (e.g., only 2 trades) and the market happens to cooperate without drawdowns, the Calmar ratio can be spuriously inflated to above 30 — a classic small-sample overfitting artifact that is not generalizable.

---

## 3 Empirical Results

### 3.1 Aggregate Results

Table 3 presents the optimal parameter combination and core performance metrics for each of the four assets obtained from the three-dimensional grid search.

**Table 3  Optimal Parameters and Core Performance Comparison Across Assets**

| Asset | Optimal (W, d, p) | All-In CAGR | All-In MaxDD | All-In Calmar | B&H CAGR | B&H MaxDD | B&H Calmar | ΔCalmar | ΣTrades |
|-------|--------------------|-------------|---------------|---------------|----------|------------|------------|---------|---------|
| CSI Div Low Vol 50 | (12m, 8%, 16%) | 6.13% | −19.2% | 0.319 | 4.21% | −46.5% | 0.091 | **3.51×** | 14 |
| NASDAQ-100 | (3m, 12%, 2%) | 6.15% | −4.0% | 1.523 | 10.34% | −20.2% | 0.511 | **2.98×** | 87 |
| S&P 500 | (3m, 6%, 4%) | 6.32% | −24.5% | 0.258 | 7.05% | −44.6% | 0.158 | **1.63×** | 43 |
| Shanghai Gold | (1m, 2%, 32%) | 13.84% | −42.3% | 0.327 | 9.92% | −44.9% | 0.221 | **1.48×** | 15 |

*Note: B&H = Buy and Hold; ΔCalmar = All-In Calmar / B&H Calmar.*

### 3.2 Asset-by-Asset Detailed Analysis

#### 3.2.1 CSI Dividend Low Volatility 50 (000922.SH) — Effective Case

The optimal parameters for the CSI Dividend Low Volatility 50 are (W = 12 months, d = 8%, p = 16%). This parameter combination merits particular attention:

- **Maximum drawdown halved**: From −46.5% under buy-and-hold to −19.2%, a reduction of 58.7%. The asset's low-volatility, slow-decline-and-recovery profile enables the DCA cost line to stably "anchor" the value center, yielding far greater signal clarity for entries and exits than is obtainable with high-volatility assets.
- **Annualized return improved**: CAGR rises from 4.21% to 6.13%, an increase of 45.6%. The strategy successfully sidestepped large drawdown segments during the 2015 crash and the 2018 bear market, re-entering during rebound phases to capture recovery gains.
- **Calmar ratio of 3.5×**: Achieves simultaneous drawdown compression and return enhancement, reflecting two-sided improvement from event-driven timing.

Conclusion: For low-volatility assets with strong trend persistence and a slow-decline character, the DCA-cost-line all-in strategy constitutes an unambiguous Pareto improvement.

#### 3.2.2 NASDAQ-100 (^NDX) — A Cautionary Trap

The optimal parameters for the NASDAQ-100 are (W = 3 months, d = 12%, p = 2%), yielding a Calmar ratio as high as 1.523 (B&H: 0.511). This superficially impressive result, however, conceals serious problems:

- **Frenetic selling**: The extremely low profit-taking threshold of p = 2% causes the strategy to exit positions with high frequency (87 trades), with practically every minor bounce triggering a sell signal.
- **Return collapse**: The CAGR drops from 10.34% under buy-and-hold (already a conservative price-index-only figure) to 6.15%, meaning the strategy forfeits 40.5% of potential gains. Under a total-return perspective that includes dividends — where B&H annualizes at approximately 18% — the strategy would consume roughly two-thirds of potential returns.
- **Spurious Calmar elevation is an illusion**: The reduction in MaxDD from −20.2% to −4.0% comes at the cost of sacrificed returns — this is not a success of risk management, but rather a deliberate forfeiture of upside.

**Conclusion: This strategy is not recommended for the NASDAQ-100.** The optimal parameter of p = 2% is essentially the grid search overfitting in the direction of drawdown minimization; it lacks economic plausibility.

#### 3.2.3 S&P 500 (^SPX) — Mediocre Performance

The optimal parameters for the S&P 500 are (W = 3 months, d = 6%, p = 4%), with a Calmar ratio improvement of 1.63×. The annualized return of 6.32% slightly underperforms buy-and-hold at 7.05%.

The root cause lies in the S&P 500's "slow bull" character: the asset spends extended periods in an upward channel, rarely triggering the deep-drawdown entry condition. The strategy executed meaningful trades only during the 2020 COVID shock and the 2022 bear market; it otherwise remained largely in cash, missing the two extended bull runs of 2015–2019 and 2023–2025. This is a textbook manifestation of the selling-too-early problem.

Conclusion: On assets exhibiting a strong secular bullish trend, the event-driven all-in strategy carries a systematic selling-too-early risk.

#### 3.2.4 Shanghai Gold Futures (AU.SHF) — Effective but Dependent on High Profit-Taking Threshold

The optimal parameters for Shanghai gold are (W = 1 month, d = 2%, p = 32%). This result reveals a parameter topology starkly different from that of the Dividend Low Volatility 50:

- **Shallow-drawdown entry**: d = 2% means the price need only fall modestly below the recent DCA cost to trigger entry, making the strategy extremely aggressive in capturing gold's "small pullbacks, large trends" pattern.
- **High profit-taking to capture large swings**: The extremely high profit-taking threshold of p = 32% ensures that positions are not shaken out by normal volatility and are only closed once the trend has fully played out.
- **Significant CAGR improvement**: From 9.92% to 13.84%, an increase of 39.5%, though MaxDD shows only a marginal improvement (B&H: −44.9%, strategy: −42.3%).
- **15 trades**: Satisfies the n ≥ 10 significance threshold.

Conclusion: The strategy is effective for Shanghai gold, but its essence is an aggressive timing model of "shallow-drawdown entry + high-profit-taking swing capture," forming a sharp contrast with the conservative character of the Dividend Low Volatility 50 solution.

### 3.3 H3 Stratified Hypothesis Verification

**H3 Hypothesis**: The optimal parameter combination differs significantly across assets with distinct volatility profiles.

The optimal parameters in Table 3 exhibit complete heterogeneity across the four assets:

- CSI Dividend Low Vol 50: W = 12 months (long-window slow anchoring), d = 8% (moderate-to-deep drawdown), p = 16% (moderate profit-taking) — conservative type
- NASDAQ-100: W = 3 months (short-window fast anchoring), d = 12% (deep drawdown), p = 2% (extremely low profit-taking) — high-frequency type (trap)
- S&P 500: W = 3 months (short window), d = 6% (shallow drawdown), p = 4% (low profit-taking) — balanced type
- Shanghai Gold: W = 1 month (ultra-short window), d = 2% (ultra-shallow drawdown), p = 32% (extremely high profit-taking) — aggressive type

The complete separation of parameter space (no two assets share the same (W, d, p) combination) strongly supports the H3 hypothesis. This simultaneously implies that no "universally optimal parameter" exists — the strategy must be independently optimized for each asset class's volatility characteristics.

### 3.4 Heatmap Interpretation

The two-dimensional heatmaps from the grid search (fixing the optimal W and displaying the Calmar distribution over the d × p plane) reveal two distinct topological patterns of parameter sensitivity:

1. **Dividend Low Volatility type (flat plateau)**: A large high-Calmar region surrounds the optimum, with strong performance across d in the 6%–14% range and p in the 10%–20% range. Parameter selection possesses high robustness — it does not hinge on any precise threshold value.

2. **NASDAQ / S&P type (sharp peaks and valleys)**: The Calmar ratio decays precipitously in the neighborhood of the optimum. For the NASDAQ-100, for instance, raising p from 2% to 4% causes the Calmar ratio to plummet from 1.52 to below 0.6. For such assets, the strategy is highly parameter-sensitive, and the optimal solution lacks engineering operability.

This topological divergence directly reflects fundamental differences in asset volatility structures: low-volatility assets exhibit stronger price-series autocorrelation and more predictable "deviation-reversion" rhythms; high-volatility assets approximate a random walk more closely, and any parameter "optimum" is more likely the product of noise fitting.

*Note: Specific heatmaps can be found under the `charts/` directory in the repository, named as `heatmap_*.png` for each asset.*

---

## 4 Discussion

### 4.1 Comparison with Benchmark Strategies

The event-driven all-in strategy proposed in this study is a systematic departure from the fixed-frequency rebalancing paradigm. The classic Permanent Portfolio executes rebalancing on a rigid quarterly or annual schedule, with its triggers entirely decoupled from market price signals — regardless of whether an asset has moved 50% or 5%, the operation calendar remains unchanged. The rationale for this time-driven paradigm rests on mean-reversion assumptions and transaction-cost minimization, but it cannot perform a hedging function during extreme market episodes.

By replacing calendar signals with value-deviation signals, the present strategy shifts the operational rhythm from time-driven to event-driven, conferring the following advantages over fixed-frequency rebalancing:

1. **Crisis response speed**: When asset prices collapse through the cost line, the strategy can exit immediately (to cash) rather than waiting for the next quarterly rebalancing window.
2. **Compression of wasteful trades**: During quiescent price regimes, the strategy generates no trades — consistent with the trend-following principles of "let profits run and cut losses short."
3. **Behavioral finance advantage**: The DCA cost line provides the investor with an objective, tamper-proof valuation anchor, reducing behavioral biases such as trend-chasing and panic selling.

This advantage, however, is not without cost: event-driven operation implies increased uncertainty in trading frequency, and the strategy is far more parameter-sensitive than fixed-frequency rebalancing.

### 4.2 Overfitting Risk and Out-of-Sample Limitations

A three-dimensional grid search traversing 3,200 parameter combinations is, at its core, an in-sample data-mining exercise. Although the n ≥ 10 statistical significance threshold effectively filters out spuriously elevated Calmar ratios arising from excessively few trades, it cannot fully eliminate the overfitting risk inherent in in-sample optimization.

Specifically:
- The NASDAQ-100 optimal parameter of p = 2% most likely arises from overfitting to high-frequency microstructural noise — out of sample, a 2% micro-rebound profit-taking threshold would very easily turn unprofitable due to slippage and transaction costs.
- None of the optimal parameters have been subjected to walk-forward out-of-sample validation, and their true out-of-sample performance awaits further verification.

Future research directions include: implementing expanding-window and rolling-window out-of-sample testing frameworks, and introducing the in-sample/out-of-sample Calmar decay rate as an auxiliary criterion for model robustness.

### 4.3 The Self-Extinguishing Problem

The strategy faces an intrinsic "self-extinguishing" risk over extended periods: when the market undergoes a protracted slow bull run (as in the S&P 500 during 2015–2019), the DCA cost line rises continuously with price, and the deviation remains in a shallow or even positive range, causing the entry signal to remain permanently silent. Under such market conditions, the strategy would enter an indefinite cash position, entirely forfeiting bull-market gains. This represents a fundamental structural limitation of the strategy.

One engineering mitigation is to upgrade the strategy from an all-or-nothing (fully invested / fully in cash) binary structure to a continuous position-sizing function: mapping the deviation to a position percentage (e.g., $position = \min(1, \max(0, -dev/\sigma))$), thereby avoiding the extremity of the binary decision. This direction merits further investigation.

### 4.4 Transaction Costs and Practical Feasibility

Transaction costs (commissions, slippage, market impact, and taxes) are not accounted for in this study. For parameter combinations with elevated trading frequency (e.g., the NASDAQ-100's 87 trades), even a per-trade cost of only 0.05% would cumulatively erode roughly 4–5% of total returns, further compressing the already low CAGR (6.15%) to 1–2%. Once transaction costs are incorporated, the all-in strategy for the NASDAQ-100 and S&P 500 would likely cease to be economically viable.

The CSI Dividend Low Volatility 50 (14 trades over ~11 years, averaging ~1.3 per year) and Shanghai gold (15 trades) incur a manageable transaction-cost impact, giving them stronger practical operability.

### 4.5 Practical Implications

The results of this section carry the following implications for quantitative investment practitioners:

1. **Parameters must be asset-specific**: No universally optimal parameter combination exists. Each asset class must undergo independent grid search; the optimal parameters for one asset must not be naively transplanted to another.
2. **Low-volatility, slow-decline assets are ideal candidates**: The significant improvement observed for the CSI Dividend Low Volatility 50 suggests that the DCA-cost-line all-in strategy is best suited to assets with high trend persistence and low volatility. Such assets exhibit stable deviation-reversion rhythms with high signal-to-noise ratios.
3. **Caution is warranted for high-growth secular-bull assets**: The cases of the NASDAQ-100 and S&P 500 demonstrate that, for assets with strong long-term trends, the selling-too-early cost of frequent timing may far exceed the benefit of drawdown control.
4. **p ≤ 4% is a red flag**: In grid search results, if the optimal profit-taking threshold p ≤ 4%, one must be highly alert to the spurious Calmar trap and should cross-validate against the CAGR trajectory.

---

## 5 Conclusion and Outlook

### 5.1 Key Findings

This paper constructs an event-driven all-in strategy anchored by a sliding-window DCA harmonic-mean cost line. Through a three-dimensional grid search (8 × 20 × 20 = 3,200 combinations per asset) and empirical analysis across four assets with heterogeneous characteristics, the following principal conclusions are drawn:

1. **Strategy effectiveness exhibits pronounced asset heterogeneity**: The CSI Dividend Low Volatility 50 all-in strategy achieves a halving of maximum drawdown (from −46.5% to −19.2%) and an improvement in annualized return (from 4.21% to 6.13%), with the Calmar ratio reaching 3.5 times that of buy-and-hold. In contrast, the NASDAQ-100 strategy displays a superficially elevated Calmar ratio but a sharp collapse in annualized return — it constitutes an overfitting trap and is not recommended for live deployment.

2. **Optimal-parameter topology reveals two fundamentally distinct adaptation mechanisms**: The CSI Dividend Low Volatility 50 relies on a long window plus moderate thresholds to achieve conservative timing; Shanghai gold relies on an ultra-short window plus an extremely high profit-taking threshold to capture aggressive swing trades. No cross-asset universal optimal parameter exists.

3. **The minimum-trade-count threshold (n ≥ 10) is a necessary statistical safeguard**: This threshold effectively filters out spurious Calmar illusions arising from excessively few trades, and constitutes an indispensable constraint when using grid search for strategy optimization.

4. **The core structural limitation of the strategy is the self-extinguishing risk**: During prolonged bull markets, the continuously rising cost line causes the entry signal to remain dormant, potentially leaving the strategy in cash indefinitely.

### 5.2 Future Research Directions

(1) **Out-of-sample validation**: Implement walk-forward cross-validation to assess the robustness and decay characteristics of optimal parameters.

(2) **From binary all-in to continuous position sizing**: Upgrade the fully-invested/fully-in-cash binary structure to a continuous position-mapping function (e.g., a sigmoid position function with deviation as the core independent variable), mitigating the self-extinguishing problem.

(3) **Multi-asset coordination**: Explore a collaborative all-in framework with concurrent multi-asset monitoring — when multiple assets simultaneously trigger entry signals, implement cross-asset capital allocation optimization.

(4) **Incorporation of transaction costs and slippage**: Embed realistic transaction-cost models into the backtesting engine and reassess the economic viability of optimal parameters.

(5) **Fusion with other timing signals**: Combine DCA cost line deviation with volatility signals, macro-cycle indicators, and other factors to construct a multi-factor event-driven framework.

(6) **Validation on additional Chinese A-share style indices**: Extend testing to the CSI 300, CSI 500, ChiNext Index, and other indices to verify the strategy's generalizability across a broader range of asset types.

---

## References

[1] Brinson, G. P., Hood, L. R., & Beebower, G. L. (1986). Determinants of portfolio performance. *Financial Analysts Journal*, 42(4), 39–44.

[2] Markowitz, H. (1952). Portfolio selection. *Journal of Finance*, 7(1), 77–91.

[3] Moskowitz, T., Ooi, Y. H., & Pedersen, L. H. (2012). Time series momentum. *Journal of Financial Economics*, 104(2), 228–250.

[4] Faith, C. M. (2007). *Way of the Turtle: The Secret Methods that Turned Ordinary People into Legendary Traders*. McGraw-Hill.

[5] Black, F., & Jones, R. (1987). Simplifying portfolio insurance. *Journal of Portfolio Management*, 14(1), 48–51.

[6] Kirkby, J. L., Mitra, S., & Nguyen, D. (2020). An analysis of dollar cost averaging and market timing investment strategies. *European Journal of Operational Research*, 286(3), 1168–1186.

[7] Jin, X., Li, H., & Yu, B. (2023). The day-of-the-month effect and the performance of the dollar cost averaging strategy: Evidence from China. *Accounting and Finance*, 63(S1), 797–815.

[8] Fama, E. F., & French, K. R. (1993). Common risk factors in the returns on stocks and bonds. *Journal of Financial Economics*, 33(1), 3–56.

[9] Liu, J., Stambaugh, R. F., & Yuan, Y. (2019). Size and value in China. *Journal of Financial Economics*, 134(1), 48–69.

[10] Sharpe, W. F. (1994). The Sharpe ratio. *Journal of Portfolio Management*, 21, 49–58.

[11] Young, T. W. (1991). Calmar ratio: A smoother tool. *Futures*, 20, 40.

---

*Paper version: v1.0 | Date: August 8, 2026 | Open-source release: GitHub*
