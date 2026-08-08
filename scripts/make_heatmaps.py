#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Calmar heatmaps for 4 main assets. PURE ASCII labels."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/myproject/suoha_strategy/results"
CHARTS = "/home/myproject/suoha_strategy/charts"
os.makedirs(CHARTS, exist_ok=True)

# CJK font for any CJK chars (keep labels mostly ASCII; title uses CJK)
import matplotlib.font_manager as fm
for fp in ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
           "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf"]:
    if os.path.exists(fp):
        fm.fontManager.addfont(fp)
        plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
        break

ASSET_NAMES = {"hongli": "HongliLowVol50", "ndx": "Nasdaq100",
               "spx": "SP500", "gold": "ShanghaiGold"}
MIN_TRADES = 10  # statistical significance threshold

d_values = np.round(np.arange(0.02, 0.40 + 1e-9, 0.02), 2)
p_values = np.round(np.arange(0.02, 0.40 + 1e-9, 0.02), 2)

for asset, en in ASSET_NAMES.items():
    df = pd.read_csv(os.path.join(OUT, f"grid_{asset}.csv"))
    # Best window by best valid Calmar
    valid = df[df["n_trades"] >= MIN_TRADES]
    if valid.empty:
        print(f"[{asset}] no valid configs, skip heatmap")
        continue
    grp = valid.groupby("W")["calmar"].max().idxmax()
    best_row = valid[valid["W"] == grp].sort_values("calmar", ascending=False).iloc[0]
    sub = valid[valid["W"] == grp]

    # pivot d x p -> calmar
    pt = sub.pivot_table(index="d", columns="p", values="calmar",
                         aggfunc="max").reindex(index=d_values, columns=p_values)

    fig, ax = plt.subplots(figsize=(9, 6.5))
    im = ax.imshow(pt.values, cmap="RdYlGn", aspect="auto", origin="lower")
    ax.set_xticks(range(len(p_values))); ax.set_xticklabels([f"{x:.0%}" for x in p_values])
    ax.set_yticks(range(len(d_values))); ax.set_yticklabels([f"{x:.0%}" for x in d_values])
    ax.set_xlabel("Take-Profit p")
    ax.set_ylabel("Entry Drawdown d")
    ax.set_title(f"{en}  Calmar Heatmap  (W={grp}mo, best Calmar {best_row['calmar']:.2f}, n={best_row['n_trades']})")
    fig.colorbar(im, ax=ax, label="Calmar")
    plt.tight_layout()
    fp = os.path.join(CHARTS, f"heatmap_{asset}_W{grp}.png")
    fig.savefig(fp, dpi=130)
    plt.close(fig)
    print(f"[{asset}] W={grp}  best Calmar={best_row['calmar']:.3f} n={best_row['n_trades']}  -> {fp}")

print("HEATMAPS DONE")