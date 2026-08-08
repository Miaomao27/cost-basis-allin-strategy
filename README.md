# The Cost-Basis All-In Strategy: Should You YOLO Your Whole Position When an Asset Crashes Below Its Own DCA Cost Line?

> **Your portfolio is down. Your favorite ETF has fallen 20% below the average price you've been dollar-cost-averaging into for a year. Should you dump every cent you have into it right now — or is that exactly how you blow up?**
>
> Buy at a 8% gap below your cost, or wait for 20%? Take profit at +4% or hold for +40%? And how long a DCA window should define "your cost" — 1 month or 3 years?
>
> We turned this gut instinct into a falsifiable question by running **4 assets × 3,200 parameter combos = 12,800 full-history backtests**. The answer has a clear winner and a dangerous trap: **the low-volatility dividend index really works; the Nasdaq-100 is a mirage.**

> **📄 Research paper (Chinese):** [reports/研究论文.md](reports/研究论文.md)
> **📄 Research paper (English):** [reports/research_paper.md](reports/research_paper.md)
> **📖 中文版 README:** [README_ZH.md](README_ZH.md)

---

## 🤔 Questions This Project Answers

1. **Is the DCA cost basis a usable "traffic light"?** When price breaks below the average price of your own recurring buys, is that really a signal that the asset is cheap?
2. **Does all-in actually work?** Buy the full position when price drops below a threshold, exit the full position when it rebounds — does this "Mode A" make money or lose money on real history?
3. **Do different assets need different parameters?** Should a slow-moving dividend index and a whipsawing Nasdaq be traded with the same "how far to buy, how far to sell" settings?
4. **Are those pretty backtest numbers real or overfit?** We enforce a **minimum 10-trade gate** to filter out the "2 trades happened to avoid a drawdown → Calmar 30+" illusion.

---

## 💡 The Idea

The **DCA cost basis** `CB = K / U` is the share-weighted average price of all your fixed recurring purchases over a rolling window — a **self-adapting slow moving average** tied to *your real money*, not to some arbitrary historical peak.

- `dev = P / CB − 1` — how far the current price sits relative to your own cost basis
- price falls `d%` below the cost line → **full buy** (market is deeply undervalued vs. your cost)
- rebound `+p%` from the post-buy low → **full exit**

This is an **event-driven** upgrade to the permanent portfolio's *calendar-driven* quarterly rebalancing: it fires on extreme price states, not on the date.

---

## 📊 Results

| Asset | Best (W, d, p) | All-in Calmar | Buy-&-Hold Calmar | All-in CAGR | All-in MaxDD |
|-------|:--------------:|:-------------:|:-----------------:|:-----------:|:------------:|
| **CSI Dividend LowVol 50** | (12m, 8%, 16%) | **0.319** | 0.091 | 6.13% | **−19.2%** |
| Nasdaq 100 | (3m, 12%, 2%) | 1.523 ⚠️ | 0.511 | 6.15% | −4.0% |
| S&P 500 | (3m, 6%, 4%) | 0.258 | 0.158 | 6.32% | −24.5% |
| Shanghai Gold | (1m, 2%, 32%) | 0.327 | 0.221 | 13.84% | −42.3% |

### Honest takeaway

- 🟢 **CSI Dividend LowVol 50 — the clear winner.** All-in **halved MaxDD** (−46.5% → −19.2%) *and* lifted CAGR (4.2% → 6.1%). Calmar **3.5×** buy-and-hold. Low-volatility, slow-moving assets are the natural fit for cost-basis triggering.
- 🟢 **Shanghai Gold — effective.** CAGR 9.9% → 13.8%. But MaxDD barely improves; the best take-profit is high (p=32%) — a "shallow-dip buy, high-rebound exit" profile.
- 🟡 **S&P 500 — tepid.** Calmar 1.6× but CAGR slips; a long bull market gets sold too early.
- 🔴 **Nasdaq 100 — a trap.** The high Calmar is a **mirage**: the best config uses p=2% (barely-gains-and-run), selling constantly to dodge the 2022 bear — but it **crushes CAGR from 18.2% to 6.2%**, trading away 2/3 of the return for a smaller drawdown. Not recommended.

**Heterogeneity (H3) confirmed:** optimal parameters differ sharply across assets — slow low-vol assets reward cost-basis triggers; high-vol long-bull assets do not.

**⚠️ Caveat:** these are **in-sample** best-of-grid results and carry overfitting risk. Out-of-sample validation (D5) is the real test of whether the Hongli/Gold gains are genuine or historical curve-fitting.

---

## 📁 Repository Layout

| Path | Contents |
|------|----------|
| `reports/` | Full research paper (Chinese & English, 11 references) |
| `charts/` | Calmar heatmaps, NAV curves, benchmark comparison |
| `data/` | Cleaned daily price series for the 4 assets |
| `results/` | Full grid-search CSVs (3,200 rows/asset) + benchmark summary |
| `scripts/` | Vectorized backtest engine + grid/graph generators |
| `plan/` | Research plan (v1.1) |
| `summary/` | Stage work summaries (D0 data, D1–D4 grid) |

---

## 🚀 Reproduce

```bash
# 1. Install deps
pip install numpy pandas pymysql matplotlib

# 2. Point the engine at your MySQL copy of china_finance_db (see scripts/backtest_engine.py)
#    or drop CSVs into data/ and patch load_price()

# 3. Run the full 12,800-combo grid on all 4 assets (≈5 s, fully vectorized)
cd scripts && python3 run_all_grids.py

# 4. Regenerate the paper charts
python3 make_paper_charts.py
```

Backtest engine: `scripts/backtest_engine.py` — cost-basis definition, vectorized state machine, metrics.

---

## ⚠️ Known Limitations

- In-sample optimum; out-of-sample validation (D5) pending
- No transaction costs / slippage modeled
- Nasdaq/S&P use price-index (ex-dividend) series
- **"Self-extinguishing" flaw:** ongoing DCA drags the cost basis down, so slow grinds may never trigger deep thresholds

---

## 🧭 Related Work

- [permanent-portfolio-backtest](https://github.com/Miaomao27/permanent-portfolio-backtest) — the parent project: 25% equal-weight permanent portfolio validation + weight grid search
- [finacial_research](https://github.com/Miaomao27/finacial_research) — A-share multi-dimensional database + Ganzhi/Wuxing calendar studies

---

## 📖 Glossary

| Term | Plain-English meaning |
|------|------------------------|
| **DCA cost basis (CB)** | The share-weighted average price of your fixed recurring buys. Fall below it and you're underwater on average. |
| **Deviation (dev)** | How far the current price sits from your cost line: `dev = P/CB − 1`. Negative = price below cost. |
| **Drawdown / MaxDD** | How far price falls from a peak / the worst peak-to-trough drop in your history. −46.5% = you once lost nearly half. |
| **CAGR** | Time-adjusted average annual return. 6% = 6% per year on average. |
| **Calmar** | `= CAGR ÷ MaxDD`. Return you get per unit of pain. Higher is better. The core metric here. |
| **Window W** | How many months of DCA history define the cost basis. 12 = use the last 12 months of buys. |
| **Entry drawdown d** | The red-light threshold — how far below the cost line to buy. 8% = go all-in when 8% underwater. |
| **Take-profit p** | How far the rebound must go before you sell it all. 16% = cash out on a 16% bounce. |
| **Mode A / All-in** | Only two moves: dip deep enough → buy everything; rebound hard enough → sell everything. No middle ground. |
| **Grid search** | Permute the three knobs (window × drawdown × take-profit) into thousands of combos and backtest each to find the most profitable. |
| **Overfitting** | The "best" parameter found by reading history may fail on unseen data. The biggest trap in quant. |

---

**License:** MIT · **Author:** Miaomao27 · **2026**