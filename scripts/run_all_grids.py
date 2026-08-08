#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run all 4 main-asset grids. PURE ASCII (no CJK anywhere)."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import backtest_engine as be

OUT = "/home/myproject/suoha_strategy/results"
os.makedirs(OUT, exist_ok=True)

for asset in ["hongli", "ndx", "spx", "gold"]:
    t0 = time.time()
    dates, prices = be.load_price(asset)
    devs = be.precompute_devs(prices)
    df = be.run_grid(prices, devs)
    df.insert(0, "asset", asset)
    fp = os.path.join(OUT, "grid_" + asset + ".csv")
    df.to_csv(fp, index=False, encoding="utf-8-sig")
    top = df.sort_values("calmar", ascending=False).head(3)[["W","d","p","cagr","maxdd","calmar","n_trades","total_return"]]
    print("[" + asset + "] " + str(len(df)) + " groups " + "%.1fs" % (time.time()-t0) + " -> " + fp)
    print(top.to_string(index=False))
    print()
print("ALL DONE")