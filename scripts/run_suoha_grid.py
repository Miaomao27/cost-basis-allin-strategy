#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
梭哈策略网格回测 CLI —— D2/D3 数据生成脚本
用法:
  python3 run_suoha_grid.py <资产> [--out 结果.csv] [--windows "1,3,6"] [--d-start 0.02] [--d-end 0.40] [--p-start 0.02] [--p-end 0.40]
资产: 红利低波50 | 纳指100 | 标普500 | 沪金
"""
import sys, os, time, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import backtest_engine as be

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset")
    ap.add_argument("--out", default=None)
    ap.add_argument("--windows", default=None, help="逗号分隔窗口月，如 '1,3,6'")
    ap.add_argument("--d-start", type=float, default=0.02)
    ap.add_argument("--d-end", type=float, default=0.40)
    ap.add_argument("--p-start", type=float, default=0.02)
    ap.add_argument("--p-end", type=float, default=0.40)
    ap.add_argument("--step", type=float, default=0.02)
    args = ap.parse_args()

    t0 = time.time()
    dates, prices = be.load_price(args.asset)
    devs = be.precompute_devs(prices)

    d_grid = np.arange(args.d_start, args.d_end + 1e-9, args.step)
    p_grid = np.arange(args.p_start, args.p_end + 1e-9, args.step)
    windows = [int(x) for x in args.windows.split(",")] if args.windows else be.WINDOWS_MONTH

    # 用 windows 过滤 devs
    devs_sub = {w: devs[w] for w in windows}

    df = be.run_grid(prices, devs_sub, d_grid=d_grid, p_grid=p_grid)
    df.insert(0, "asset", args.asset)
    dt = time.time() - t0

    out = args.out or f"/home/myproject/suoha_strategy/results/grid_{args.asset}.csv"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"[{args.asset}] {len(df)} 组, {dt:.2f}s → {out}")
    print(df.sort_values("calmar", ascending=False).head(5).to_string(index=False))

if __name__ == "__main__":
    main()