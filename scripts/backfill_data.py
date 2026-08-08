#!/usr/bin/env python3
"""
梭哈策略研究 - 数据补全脚本 (D0)
=================================
把四类资产从库里最后日期增量补到今天(2026-08-07)。
数据源(已验证可用):
  - 红利低波50 H30269.CSI  : tushare index_daily
  - 沪金 AU.SHF           : akshare futures_main_sina (AU0 主力连续)
  - 申万31行业            : akshare index_hist_sw
  - 纳指/标普(^NDXT/^SP500TR): yfinance (可能限流,单独处理)

用法:
  python3 02_脚本/backfill_data.py <asset>    # asset: hongli 沪金 行业 美股 all

依赖: .venv-finance 环境
  .venv-finance/bin/python3 02_脚本/backfill_data.py hongli
"""
import os, sys, time, pandas as pd
import pymysql
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_CONFIG = {
    'host': '127.0.0.1', 'port': 3306, 'user': 'finance_user',
    'password': 'Finance2026!', 'database': 'china_finance_db', 'charset': 'utf8mb4'
}
TUSHARE_TOKEN = '27cdff7ac3cc6f6fd8eccae0907f6567ae86661c2eae57d4684a41c2'

def get_conn():
    return pymysql.connect(**DB_CONFIG)

# ────────────── 红利低波50 (tushare index_daily) ──────────────
def backfill_hongli():
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT MAX(交易日期) FROM daily_quote WHERE 证券代码='H30269.CSI'")
    last = cur.fetchone()[0]
    start = (last + pd.Timedelta(days=1)).strftime('%Y%m%d') if last else '20150101'
    end = '20260808'
    print(f"[红利低波] 当前到 {last}, 补 {start} ~ {end}")
    df = pro.index_daily(ts_code='H30269.CSI', start_date=start, end_date=end)
    if df is None or len(df) == 0:
        print("  无新数据"); return 0
    df = df.sort_values('trade_date')
    rows = []
    for _, r in df.iterrows():
        d = datetime.strptime(str(r['trade_date']), '%Y%m%d').date()
        prev = float(r['pre_close']) if pd.notna(r.get('pre_close')) else None
        chg = float(r['change']) if pd.notna(r.get('change')) else None
        pct = float(r['pct_chg']) if pd.notna(r.get('pct_chg')) else None
        rows.append(('H30269.CSI', d, float(r['open']) if pd.notna(r.get('open')) else None,
                     float(r['high']) if pd.notna(r.get('high')) else None,
                     float(r['low']) if pd.notna(r.get('low')) else None,
                     float(r['close']), prev, chg, pct, None, None, 1, '正常'))
    sql = """INSERT IGNORE INTO daily_quote (证券代码,交易日期,开盘价,最高价,最低价,收盘价,前收盘,涨跌额,涨跌幅,成交量,成交额,是否收盘,交易状态)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    cur.executemany(sql, rows); conn.commit()
    print(f"  ✅ 红利低波补 {len(rows)} 条, 至 {rows[-1][1]}")
    cur.close(); conn.close()
    return len(rows)

# ────────────── 沪金 AU.SHF (akshare futures_main_sina AU0) ──────────────
def backfill_gold():
    import akshare as ak
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT MAX(交易日期) FROM commodity_daily WHERE 商品代码='AU.SHF'")
    last = cur.fetchone()[0]
    print(f"[沪金] 当前到 {last}")
    df = ak.futures_main_sina(symbol='AU0')
    df['日期'] = pd.to_datetime(df['日期']).dt.date
    if last:
        df = df[df['日期'] > last]
    if len(df) == 0:
        print("  无新数据"); return 0
    rows = []
    for _, r in df.iterrows():
        rows.append(('AU.SHF', '沪金主连', '贵金属', r['日期'], '主力合约',
                     float(r['开盘价']), float(r['最高价']), float(r['最低价']),
                     float(r['收盘价']), float(r['动态结算价']) if pd.notna(r.get('动态结算价')) else None,
                     None, None, None, None, None))
    sql = """INSERT IGNORE INTO commodity_daily (商品代码,商品名称,品种分类,交易日期,合约类型,开盘价,最高价,最低价,收盘价,结算价,成交量,持仓量,交易所库存,涨跌幅,月间价差)
             VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    cur.executemany(sql, rows); conn.commit()
    print(f"  ✅ 沪金补 {len(rows)} 条, 至 {rows[-1][3]}")
    cur.close(); conn.close()
    return len(rows)

# ────────────── 申万31行业 (akshare index_hist_sw) ──────────────
SW_CODES = [
    ('801010.SI','农林牧渔'),('801030.SI','基础化工'),('801040.SI','钢铁'),('801050.SI','有色金属'),
    ('801080.SI','电子'),('801110.SI','家用电器'),('801120.SI','食品饮料'),('801130.SI','纺织服饰'),
    ('801140.SI','轻工制造'),('801150.SI','医药生物'),('801160.SI','公用事业'),('801170.SI','交通运输'),
    ('801180.SI','房地产'),('801200.SI','商贸零售'),('801210.SI','社会服务'),('801230.SI','综合'),
    ('801710.SI','建筑材料'),('801720.SI','建筑装饰'),('801730.SI','电力设备'),('801740.SI','国防军工'),
    ('801750.SI','计算机'),('801760.SI','传媒'),('801770.SI','通信'),('801780.SI','银行'),
    ('801790.SI','非银金融'),('801880.SI','汽车'),('801890.SI','机械设备'),('801950.SI','煤炭'),
    ('801960.SI','石油石化'),('801970.SI','环保'),('801980.SI','美容护理'),
]
def backfill_sectors():
    import akshare as ak
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT MAX(交易日期) FROM sector_daily")
    last = cur.fetchone()[0]
    print(f"[申万行业] 当前到 {last}")
    total = 0
    for code6, name in SW_CODES:
        code = code6.split('.')[0]
        try:
            df = ak.index_hist_sw(symbol=code, period='day')
            df['日期'] = pd.to_datetime(df['日期']).dt.date
            if last:
                df = df[df['日期'] > last]
            if len(df) == 0:
                continue
            rows = []
            for _, r in df.iterrows():
                # 17列: 行业代码,行业名称,交易日期,开盘价,最高价,最低价,收盘价,涨跌额,涨跌幅,成交量,成交额,PE,PB,流通市值,总市值,是否收盘,数据来源
                rows.append((code6, name, r['日期'], float(r['开盘']), float(r['最高']),
                             float(r['最低']), float(r['收盘']), None, None, None, None,
                             None, None, None, None, 1, 'tushare'))
            sql = """INSERT IGNORE INTO sector_daily (行业代码,行业名称,交易日期,开盘价,最高价,最低价,收盘价,涨跌额,涨跌幅,成交量,成交额,PE,PB,流通市值,总市值,是否收盘,数据来源)
                     VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cur.executemany(sql, rows); conn.commit()
            total += len(rows)
            print(f"  ✅ {code6} {name}: +{len(rows)}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  WARN {code6} {name}: {str(e)[:80]}")
    print(f"  ✅ 申万行业合计补 {total} 条")
    cur.close(); conn.close()
    return total

# ────────────── 美股指数 (akshare index_us_stock_sina, 价格指数口径) ──────────────
US_INDEXES = [
    ('^NDX', '纳斯达克100', '.NDX'),
    ('^SPX', '标普500', '.INX'),
]
def backfill_us():
    import akshare as ak
    conn = get_conn(); cur = conn.cursor()
    for code, name, sina_sym in US_INDEXES:
        try:
            cur.execute("SELECT MAX(trade_date) FROM us_index_daily WHERE index_code=%s", (code,))
            last = cur.fetchone()[0]
            df = ak.index_us_stock_sina(symbol=sina_sym)
            df['date'] = pd.to_datetime(df['date']).dt.date
            if last:
                df = df[df['date'] > last]
            if len(df) == 0:
                print(f"[美股] {code} {name} 无新数据"); continue
            rows = []
            for _, r in df.iterrows():
                rows.append((code, name, r['date'],
                             float(r['open']) if pd.notna(r['open']) else None,
                             float(r['high']) if pd.notna(r['high']) else None,
                             float(r['low']) if pd.notna(r['low']) else None,
                             float(r['close']), float(r['close']), None))
            sql = "INSERT IGNORE INTO us_index_daily (index_code,index_name,trade_date,open,high,low,close,adj_close,volume) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            cur.executemany(sql, rows); conn.commit()
            print(f"  ✅ 美股 {code} {name}: +{len(rows)}, 至 {rows[-1][2]}")
        except Exception as e:
            print(f"  WARN 美股 {code} {name}: {str(e)[:100]}")
    cur.close(); conn.close()

if __name__ == '__main__':
    asset = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if asset in ('hongli', 'all'): backfill_hongli()
    if asset in ('gold', 'all'): backfill_gold()
    if asset in ('sector', 'all'): backfill_sectors()
    if asset in ('us', 'all'): backfill_us()
    print("\n补全完成")