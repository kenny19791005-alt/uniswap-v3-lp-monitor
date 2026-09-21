import os
import requests
import pandas as pd
from datetime import datetime

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"TG发送失败: {e}")

def get_btc_price_200ma():
    # CoinGecko获取BTC历史30天日线，计算200MA偏离（简化：30日窗口演示分位）
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30"
    res = requests.get(url, timeout=15).json()
    prices = [p[1] for p in res["prices"]]
    ser = pd.Series(prices)
    ma200 = ser.rolling(window=20, min_periods=1).mean().iloc[-1]
    spot = ser.iloc[-1]
    dev = (spot - ma200) / ma200
    pct = ser.rank(pct=True).iloc[-1] * 100
    return spot, dev, pct

def get_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta>0,0)
    loss = -delta.where(delta<0,0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100/(1+rs))
    return rsi.iloc[-1]

def get_ethbtc():
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=btc&days=30"
    res = requests.get(url, timeout=15).json()
    vals = [p[1] for p in res["prices"]]
    ser = pd.Series(vals)
    current = ser.iloc[-1]
    pct = ser.rank(pct=True).iloc[-1] * 100
    return current, pct

def get_binance_funding(symbol):
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    params = {"symbol":symbol}
    r = requests.get(url, params=params, timeout=15).json()
    return float(r["lastFundingRate"])

def get_btc_oi():
    # Binance公开OI
    url = "https://fapi.binance.com/fapi/v1/openInterest?symbol=BTCUSDT"
    r = requests.get(url, timeout=15).json()
    oi_val = float(r["openInterest"])
    # 简化：固定30日区间做演示分位；生产可保存历史数据
    return oi_val

def get_fear_greed():
    url = "https://api.alternative.me/fng/"
    res = requests.get(url, timeout=15).json()
    val = int(res["data"][0]["value"])
    return val

def main():
    report = "===== 📊 加密市场半天快照 =====\n"
    report += f"更新时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
    try:
        btc_spot, btc_dev, btc_dev_pct = get_btc_price_200ma()
        report += f"【BTC 现货】\n价格: ${btc_spot:.0f}\n相对均线偏离: {btc_dev:.2%} | 30日分位: {btc_dev_pct:.1f}%\n\n"

        ethbtc, ethbtc_pct = get_ethbtc()
        report += f"【ETH/BTC】\n比值: {ethbtc:.4f} | 30日分位: {ethbtc_pct:.1f}%\n\n"

        btc_fund = get_binance_funding("BTCUSDT")
        eth_fund = get_binance_funding("ETHUSDT")
        report += f"【永续资金费率】\nBTC: {btc_fund:.4f}\nETH: {eth_fund:.4f}\n\n"

        fg = get_fear_greed()
        report += f"【恐慌贪婪指数】{fg}\n\n"

        report += "📖 参考判断\n>80%：过热拥挤，减仓LP\n<20%：低迷超卖，加仓\n20~80%：观望持有\n"
    except Exception as e:
        report += f"❌ 数据获取异常：{str(e)}"
    print(report)
    send_tg_message(report)

if __name__ == "__main__":
    main()
