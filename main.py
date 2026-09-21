import os
import requests
import pandas as pd
from datetime import datetime

TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")
COINGLASS_API_KEY = os.getenv("COINGLASS_API_KEY")

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"TG发送失败: {e}")

def get_btc_price_ma():
    # 90天K线，缓解分位虚高
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=90"
    res = requests.get(url, timeout=15).json()
    prices = [p[1] for p in res["prices"]]
    ser = pd.Series(prices)
    ma50 = ser.rolling(window=50, min_periods=1).mean().iloc[-1]
    spot = ser.iloc[-1]
    dev = (spot - ma50) / ma50
    pct = ser.rank(pct=True).iloc[-1] * 100
    return spot, dev, pct

def get_ethbtc():
    url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=btc&days=90"
    res = requests.get(url, timeout=15).json()
    vals = [p[1] for p in res["prices"]]
    ser = pd.Series(vals)
    current = ser.iloc[-1]
    pct = ser.rank(pct=True).iloc[-1] * 100
    return current, pct

def get_coinglass_funding():
    """CoinGlass V4 API，获取币安BTCUSDT、ETHUSDT最新资金费率"""
    try:
        headers = {"CG-API-KEY": COINGLASS_API_KEY}
        base_url = "https://open-api-v4.coinglass.com/api/futures/funding-rate/history"
        # BTCUSDT Binance
        btc_params = {"exchange":"Binance","symbol":"BTCUSDT","interval":"8h","limit":1}
        btc_r = requests.get(base_url, headers=headers, params=btc_params, timeout=15)
        btc_data = btc_r.json()
        btc_f = float(btc_data["data"]["list"][0]["close"])

        # ETHUSDT Binance
        eth_params = {"exchange":"Binance","symbol":"ETHUSDT","interval":"8h","limit":1}
        eth_r = requests.get(base_url, headers=headers, params=eth_params, timeout=15)
        eth_data = eth_r.json()
        eth_f = float(eth_data["data"]["list"][0]["close"])
        return btc_f, eth_f
    except Exception as e:
        print(f"CoinGlass 资金费率读取异常: {e}")
        return None, None

def get_fear_greed():
    url = "https://api.alternative.me/fng/"
    res = requests.get(url, timeout=15).json()
    val = int(res["data"][0]["value"])
    return val

def main():
    report = "===== 📊 加密市场6小时快照 =====\n"
    report += f"更新时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"

    # BTC现货指标
    try:
        btc_spot, btc_dev, btc_dev_pct = get_btc_price_ma()
        report += f"【BTC 现货】\n价格: ${btc_spot:.0f}\n相对50日均线偏离: {btc_dev:.2%} | 90日分位: {btc_dev_pct:.1f}%\n\n"
    except Exception as e:
        report += f"【BTC现货】获取异常：{str(e)}\n\n"

    # ETH/BTC比值
    try:
        ethbtc, ethbtc_pct = get_ethbtc()
        report += f"【ETH/BTC】\n比值: {ethbtc:.4f} | 90日分位: {ethbtc_pct:.1f}%\n\n"
    except Exception as e:
        report += f"【ETH/BTC】获取异常：{str(e)}\n\n"

    # CoinGlass资金费率
    try:
        btc_fund, eth_fund = get_coinglass_funding()
        report += "【永续资金费率 CoinGlass(Binance)】\n"
        if btc_fund is not None:
            report += f"BTC: {btc_fund:.4f}\n"
        else:
            report += "BTC: 获取失败\n"
        if eth_fund is not None:
            report += f"ETH: {eth_fund:.4f}\n"
        else:
            report += "ETH: 获取失败\n"
        report += "\n"
    except Exception as e:
        report += f"【资金费率】获取异常：{str(e)}\n\n"

    # 恐慌贪婪指数
    try:
        fg = get_fear_greed()
        report += f"【恐慌贪婪指数】{fg}\n\n"
    except Exception as e:
        report += f"【恐慌贪婪】获取异常：{str(e)}\n\n"

    report += "📖 参考判断\n>80%：过热拥挤，减仓LP\n<20%：低迷超卖，加仓\n20~80%：观望持有\n"
    print(report)
    send_tg_message(report)

if __name__ == "__main__":
    main()
