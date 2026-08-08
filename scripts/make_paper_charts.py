#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate paper charts: NAV curves + benchmark comparison. PURE ASCII labels."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import backtest_engine as be

OUT = "/home/myproject/suoha_strategy/results"
CHARTS = "/home/myproject/suoha_strategy/charts"
os.makedirs(CHARTS, exist_ok=True)

import matplotlib.font_manager as fm
for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
        plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
        break

ASSETS = {"hongli": "HongliLowVol50", "ndx": "Nasdaq100", "spx": "SP500", "gold": "ShanghaiGold"}
MIN_TRADES = 10

# ---- 1. NAV curves: buy-hold vs best-allin ----
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
axes = axes.flatten()
for idx, (asset, en) in enumerate(ASSETS.items()):
    dates, prices = be.load_price(asset)
    df = pd.read_csv(os.path.join(OUT, f"grid_{asset}.csv"))
    valid = df[df["n_trades"] >= MIN_TRADES].sort_values("calmar", ascending=False)
    ax = axes[idx]
    # buy hold nav
    bh = prices / prices[0]
    ax.plot(dates, bh, label="Buy & Hold", color="#888", lw=1.2, alpha=0.8)
    if not valid.empty:
        t = valid.iloc[0]
        devs = be.precompute_devs(prices)
        nav, _ = be.simulate_compounded(prices, devs[int(t["W"])], t["d"], t["p"])
        ax.plot(dates, nav, label=f"All-in (W={int(t['W'])} d={t['d']:.0%} p={t['p']:.0%})",
                color="#d62728", lw=1.6)
    ax.set_title(f"{en}  NAV (buy-hold vs best all-in)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    ax.set_yscale("log")
plt.tight_layout()
fig.savefig(os.path.join(CHARTS, "nav_compare_4panel.png"), dpi=130)
plt.close(fig)
print("nav_compare_4panel.png done")

# ---- 2. Benchmark comparison bar chart (Calmar) ----
assets_list = []
for asset, en in ASSETS.items():
    dates, prices = be.load_price(asset)
    n = len(prices); years = (n - 1) / 252
    bh_final = prices[-1] / prices[0]
    bh_cagr = bh_final ** (1 / years) - 1
    peak = np.maximum.accumulate(prices); dd = prices / peak - 1
    bh_calmar = bh_cagr / abs(dd.min())
    df = pd.read_csv(os.path.join(OUT, f"grid_{asset}.csv"))
    valid = df[df["n_trades"] >= MIN_TRADES].sort_values("calmar", ascending=False)
    allin_calmar = valid.iloc[0]["calmar"] if not valid.empty else np.nan
    allin_maxdd = valid.iloc[0]["maxdd"] if not valid.empty else np.nan
    allin_cagr = valid.iloc[0]["cagr"] if not valid.empty else np.nan
    assets_list.append(dict(asset=asset, name=en, bh_calmar=bh_calmar, allin_calmar=allin_calmar,
                            bh_cagr=bh_cagr, bh_maxdd=dd.min(), allin_cagr=allin_cagr, allin_maxdd=allin_maxdd))
bench = pd.DataFrame(assets_list)

x = np.arange(len(bench))
w = 0.35
fig, ax = plt.subplots(figsize=(10, 5.5))
ax.bar(x - w/2, bench["bh_calmar"], w, label="Buy & Hold", color="#888")
ax.bar(x + w/2, bench["allin_calmar"], w, label="Best All-in (n>=10)", color="#d62728")
ax.set_xticks(x); ax.set_xticklabels(bench["name"])
ax.set_ylabel("Calmar Ratio")
ax.set_title("Calmar: Buy & Hold vs Best All-in strategy")
ax.legend()
ax.grid(alpha=0.3, axis="y")
plt.tight_layout()
fig.savefig(os.path.join(CHARTS, "calmar_benchmark_compare.png"), dpi=130)
plt.close(fig)
print("calmar_benchmark_compare.png done")

# ---- 3. Summary table CSV for paper ----
bench.to_csv(os.path.join(OUT, "benchmark_summary.csv"), index=False, encoding="utf-8-sig")
print("benchmark_summary.csv done")
print(bench.to_string(index=False))
print("CHARTS2 DONE")