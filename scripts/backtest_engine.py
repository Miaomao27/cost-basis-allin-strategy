#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D1 回测引擎：定投成本线梭哈策略
=================================
核心优化：全程 numpy 向量化，不做逐日 Python 循环。
- 定投成本线 CB_W 用 'cumsum 差分' 一步算完 8 个窗口的滚动和
- 状态机用 argmax/搜索向量化跳转（找触发点、找止盈点），而非逐日 for
- 网格按参数组合分片，配合多进程/多批次调度

策略（模式A）：dev_W <= -d% 全额梭哈买入；从买入后低点反弹 +p% 全额离场。
"""
import os
import sys
import json
import time
import numpy as np
import pandas as pd
import pymysql

# ---------- 配置 ----------
DB = dict(host="127.0.0.1", port=3306, user="finance_user",
          password="Finance2026!", database="china_finance_db", charset="utf8mb4")

WINDOWS_MONTH = [1, 3, 6, 9, 12, 18, 24, 36]   # 窗口(月)
D_GRID = np.arange(0.02, 0.40 + 1e-9, 0.02)   # 入场回撤 2%~40%, 20档
P_GRID = np.arange(0.02, 0.40 + 1e-9, 0.02)   # 止盈 2%~40%, 20档
TRADING_DAYS_PER_MONTH = 21

# ---------- 数据加载 ----------

def asset_code(asset):
    """中英文资产名统一映射为内部代码。"""
    m = {
        "红利低波50": "hongli",
        "hongli": "hongli",
        "纳指100": "ndx",
        "ndx": "ndx",
        "nasdaq100": "ndx",
        "标普500": "spx",
        "spx": "spx",
        "sp500": "spx",
        "沪金": "gold",
        "gold": "gold",
        "au": "gold",
    }
    return m.get(asset, asset)


def load_price(asset):
    """按资产从 MySQL 加载对齐后的日收盘价序列(升序)。返回 (dates, prices)。"""
    code = asset_code(asset)
    conn = pymysql.connect(**DB)
    if code == "hongli":
        sql = "SELECT 交易日期, 收盘价 FROM daily_quote WHERE 证券代码='000922.SH' ORDER BY 交易日期"
    elif code == "ndx":
        sql = "SELECT trade_date, close FROM us_index_daily WHERE index_code='^NDX' ORDER BY trade_date"
    elif code == "spx":
        sql = "SELECT trade_date, close FROM us_index_daily WHERE index_code='^SPX' ORDER BY trade_date"
    elif code == "gold":
        sql = "SELECT 交易日期, 收盘价 FROM commodity_daily WHERE 商品代码='AU.SHF' ORDER BY 交易日期"
    else:
        conn.close(); raise ValueError(f"未知资产: {asset}")
    df = pd.read_sql(sql, conn)
    conn.close()
    df.columns = ["date", "price"]
    df = df.dropna()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    # 去重(极端情况)
    df = df.drop_duplicates(subset="date", keep="last").reset_index(drop=True)
    prices = df["price"].to_numpy(dtype=np.float64)
    dates = df["date"].to_numpy()
    return dates, prices


def compute_cost_basis(prices, window_days):
    """
    向量化计算定投成本线 CB_W(t) = K/U（滑动窗口，每交易日投1元）。
    U = Σ_{窗口内} 1/P_t,  K = 窗口内交易日数 = window_days。
    用 cumsum 差分，把 8 个窗口一次算完。
    返回与 prices 等长的 dev 序列: dev = P/CB - 1。
    """
    n = len(prices)
    inv_p = 1.0 / prices
    # 用 cumsum 差分实现滚动求和(cumsum 是 O(n)，比 rolling 内部循环快，且一次算多窗口)
    cs = np.concatenate([[0.0], np.cumsum(inv_p)])
    # CB 需要窗口内实际天数，前 window_days-1 天数据不足，置 NaN(不触发)
    dev = np.full(n, np.nan)
    if window_days >= n:
        return dev
    # 滚动窗口和: U[i] = cs[i+1] - cs[i+1-window_days]
    U = cs[window_days : n + 1] - cs[0 : n + 1 - window_days]
    K = window_days
    CB = K / U
    dev[window_days - 1 :] = prices[window_days - 1 :] / CB - 1.0
    return dev


def precompute_devs(prices):
    """预计算所有窗口的 dev 序列, 返回 dict{window_month: dev_array}。"""
    devs = {}
    for wm in WINDOWS_MONTH:
        wd = wm * TRADING_DAYS_PER_MONTH
        devs[wm] = compute_cost_basis(prices, wd)
    return devs


# ---------- 状态机(向量化跳转) ----------

def simulate_one(prices, dev, d, p):
    """
    单参数组 (d,p) 的完整回溯。向量化找触发/止盈点。
    规则: 空仓时若 dev<=-d 则全额梭哈买入; 持仓时从买入日后最低点反弹 +p 则全额离场。
    返回 dict: 收益序列/交易列表/指标。
    用 prices 长度 n, 索引跳跃扫描。
    """
    n = len(prices)
    nan_start = int(np.argmax(~np.isnan(dev)))  # 第一个有效 dev 索引(或 0)
    if nan_start == 0 and np.isnan(dev[0]):
        # 全 NaN 情况
        return None

    # 触发条件掩码
    trigger = (~np.isnan(dev)) & (dev <= -d)

    trades = []        # (买入idx, 卖出idx, 买入价, 卖出价)
    i = nan_start
    while i < n:
        # 找下一个触发点
        seg = trigger[i:]
        if not seg.any():
            break
        buy_idx = i + int(np.argmax(seg))
        buy_price = prices[buy_idx]
        # 从买入后的低点找止盈: 需要从 buy_idx 起累计最低价
        # 向量化: 对 buy_idx 之后, 计算 running min, 找第一个 price >= min*(1+p)
        tail = prices[buy_idx + 1 :]
        if tail.size == 0:
            trades.append((buy_idx, None, buy_price, None))
            break
        run_min = np.minimum.accumulate(np.concatenate([[buy_price], tail]))
        # 找第一个满足 price >= run_min*(1+p) 的点
        cond = tail >= run_min[1:] * (1 + p)
        hit = np.argmax(cond) if cond.any() else -1
        if hit < 0:
            # 持仓到结束未止盈
            trades.append((buy_idx, None, buy_price, None))
            break
        sell_idx = buy_idx + 1 + int(hit)
        sell_price = prices[sell_idx]
        trades.append((buy_idx, sell_idx, buy_price, sell_price))
        i = sell_idx + 1

    return trades


def trades_to_metrics(prices, trades):
    """
    从交易列表计算组合(初始资金1, 每次全额梭哈, 空仓期持现金)的收益表现。
    模式A是"抄底逃顶": 空仓持现金(收益0), 持仓吃涨跌。
    """
    n = len(prices)
    # 资产净值曲线: 空仓=1(现金不变), 持仓=从买入价到当前价的倍数
    nav = np.ones(n)
    for buy_idx, sell_idx, bp, sp in trades:
        if sell_idx is None:
            # 持仓到结束
            nav[buy_idx:] = prices[buy_idx:] / bp
        else:
            nav[buy_idx : sell_idx + 1] = prices[buy_idx : sell_idx + 1] / bp
    # 注: 空仓期(两次交易之间) nav 保持上一段末尾值(即卖出后现金 = 离场时的1倍)
    # 修正: 每次离场后现金回到卖出时的倍数, 但这里简化为每段独立(从1开始)
    # —— 更精确"滚雪球"模型见 simulate_compounded, 这里先给单段口径
    return nav


# ---------- 精确复利模型(卖出的钱再投入) ----------

def simulate_compounded(prices, dev, d, p):
    """
    精确模型: 本金1。空仓持现金(不涨), 买入全仓, 离场后现金=离场时净值, 再触发再全仓。
    返回 (dates对齐的nav, 交易次数, 买卖明细)。
    """
    n = len(prices)
    nan_start = int(np.argmax(~np.isnan(dev)))
    trigger = (~np.isnan(dev)) & (dev <= -d)

    cash_val = 1.0          # 当前现金(离场后总值)
    nav = np.ones(n)
    trades = []
    i = nan_start
    last_processed = nan_start  # 已写入nav的位置(空仓段现金)
    while i < n:
        seg = trigger[i:]
        if not seg.any():
            # 后面全是空仓(现金), 从 last_processed 到最后填现金
            nav[last_processed:] = cash_val
            break
        buy_idx = i + int(np.argmax(seg))
        buy_price = prices[buy_idx]
        entry_value = cash_val
        # 买入前空仓段: last_processed..buy_idx-1 填现金
        nav[last_processed:buy_idx] = cash_val
        tail = prices[buy_idx + 1 :]
        if tail.size == 0:
            # 买入后无后续, 持仓到结束
            nav[buy_idx:] = entry_value * (prices[buy_idx:] / buy_price)
            trades.append((buy_idx, None, buy_price, None, entry_value))
            break
        run_min = np.minimum.accumulate(np.concatenate([[buy_price], tail]))
        cond = tail >= run_min[1:] * (1 + p)
        hit = np.argmax(cond) if cond.any() else -1
        if hit < 0:
            nav[buy_idx:] = entry_value * (prices[buy_idx:] / buy_price)
            trades.append((buy_idx, None, buy_price, None, entry_value))
            break
        sell_idx = buy_idx + 1 + int(hit)
        sell_price = prices[sell_idx]
        nav[buy_idx : sell_idx + 1] = entry_value * (prices[buy_idx : sell_idx + 1] / buy_price)
        cash_val = entry_value * (sell_price / buy_price)
        trades.append((buy_idx, sell_idx, buy_price, sell_price, entry_value))
        i = sell_idx + 1
        last_processed = sell_idx + 1
    return nav, trades


# ---------- 指标 ----------

def holding_days(mid_trades):
    """平均持有期(交易日)。"""
    ds = [s - b for b, s, *_ in mid_trades if s is not None]
    return float(np.mean(ds)) if ds else 0.0


def compute_metrics(prices, nav):
    """从净值曲线算指标。返回 dict。"""
    n = len(prices)
    rets = np.diff(nav) / nav[:-1]
    final = nav[-1]
    total_return = final - 1.0
    years = (n - 1) / 252.0
    cagr = (final ** (1.0 / years) - 1.0) if (years > 0 and final > 0) else 0.0
    # 最大回撤
    peak = np.maximum.accumulate(nav)
    dd = nav / peak - 1.0
    maxdd = float(dd.min())
    calmar = (cagr / abs(maxdd)) if maxdd < 0 else float("nan")
    # 夏普(考虑空仓现金=0收益, 无风险0)
    if len(rets) > 1 and rets.std() > 0:
        sharpe = float(rets.mean() / rets.std() * np.sqrt(252))
    else:
        sharpe = 0.0
    return dict(
        total_return=float(total_return),
        cagr=float(cagr),
        maxdd=maxdd,
        calmar=calmar,
        sharpe=sharpe,
        n_trades=0,
    )


# ---------- 网格驱动 ----------

def run_grid(prices, devs, d_grid=None, p_grid=None, progress=None):
    """
    跑一个资产的全网格(或子网格)。返回 DataFrame[W,d,p,指标...]。
    向量化内层: 每个 (W,d,p) 调 simulate_compounded。
    """
    d_grid = D_GRID if d_grid is None else d_grid
    p_grid = P_GRID if p_grid is None else p_grid
    rows = []
    t0 = time.time()
    for W in WINDOWS_MONTH:
        dev = devs[W]
        for d in d_grid:
            for p in p_grid:
                nav, trades = simulate_compounded(prices, dev, float(d), float(p))
                mid = compute_metrics(prices, nav)
                mid.update(W=W, d=float(d), p=float(p),
                           n_trades=len(trades),
                           avg_hold=holding_days(trades))
                rows.append(mid)
    return pd.DataFrame(rows)


def main():
    pass


if __name__ == "__main__":
    main()