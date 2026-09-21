import os
import requests
from config import *

# 读取GitHub Secrets环境变量
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# 告警计数器，用来过滤瞬时假信号
alert_counter_btc = 0
alert_counter_eth = 0

def send_tg_message(text):
    """发送Telegram消息"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"TG消息发送失败: {e}")

def get_crypto_prices():
    """从CoinGecko获取 BTC, WBTC, ETH 现货价格"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,wrapped-bitcoin,ethereum",
        "vs_currencies": "usd"
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    btc = data["bitcoin"]["usd"]
    wbtc = data["wrapped-bitcoin"]["usd"]
    eth = data["ethereum"]["usd"]
    return btc, wbtc, eth

def get_binance_funding(symbol):
    """Binance公开API获取永续合约当前资金费率，symbol: BTCUSDT / ETHUSDT"""
    url = f"https://fapi.binance.com/fapi/v1/fundingRate"
    params = {"symbol": symbol, "limit":1}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    funding_rate = float(data[0]["fundingRate"])
    return funding_rate

def main():
    global alert_counter_btc, alert_counter_eth
    print("===== LP监控程序启动 =====")
    # 获取价格
    btc_price, wbtc_price, eth_price = get_crypto_prices()
    # 获取资金费率
    btc_funding = get_binance_funding("BTCUSDT")
    eth_funding = get_binance_funding("ETHUSDT")

    print(f"BTC: ${btc_price}, WBTC: ${wbtc_price}, ETH: ${eth_price}")
    print(f"BTC Funding: {btc_funding:.4f}, ETH Funding: {eth_funding:.4f}")

    # WBTC/BTC价差检查
    price_diff = abs(wbtc_price - btc_price) / btc_price
    if price_diff >= WBTC_BTC_DEVIATION_ALERT:
        msg = f"⚠️ WBTC脱锚告警！\nBTC: ${btc_price}\nWBTC: ${wbtc_price}\n价差: {price_diff:.2%}"
        send_tg_message(msg)

    # ========== BTC/WBTC LP 判断逻辑 ==========
    near_upper_btc = btc_price >= WBTC_LP_HIGH * (1 - WBTC_PRICE_ALERT_PCT)
    funding_hot_btc = btc_funding >= FUNDING_RATE_THRESHOLD
    btc_trigger_count = sum([near_upper_btc, funding_hot_btc])

    if btc_trigger_count >= 2:
        alert_counter_btc += 1
        if alert_counter_btc >= ALERT_CONFIRM_TIMES:
            msg = f"""🚨 BTC/WBTC LP告警触发！
BTC现价：${btc_price}
资金费率：{btc_funding:.4f}
你的LP区间：${WBTC_LP_LOW} ~ ${WBTC_LP_HIGH}
多个过热指标触发，请评估是否移除流动性。"""
            send_tg_message(msg)
            alert_counter_btc = 0
    else:
        alert_counter_btc = 0

    # ========== ETH LP 判断逻辑 ==========
    near_upper_eth = eth_price >= ETH_LP_HIGH * (1 - ETH_PRICE_ALERT_PCT)
    funding_hot_eth = eth_funding >= FUNDING_RATE_THRESHOLD
    eth_trigger_count = sum([near_upper_eth, funding_hot_eth])

    if eth_trigger_count >= 2:
        alert_counter_eth +=1
        if alert_counter_eth >= ALERT_CONFIRM_TIMES:
            msg = f"""🚨 ETH LP告警触发！
ETH现价：${eth_price}
资金费率：{eth_funding:.4f}
你的LP区间：${ETH_LP_LOW} ~ ${ETH_LP_HIGH}
多个过热指标触发，请评估是否移除流动性。"""
            send_tg_message(msg)
            alert_counter_eth =0
    else:
        alert_counter_eth =0

if __name__ == "__main__":
    main()
