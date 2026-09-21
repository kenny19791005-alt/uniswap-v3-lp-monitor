# ===================== 配置项 =====================
# WBTC/USDC LP
WBTC_LP_LOW = 76000
WBTC_LP_HIGH = 90000
# 距离区间上限剩余多少百分比触发告警
WBTC_PRICE_ALERT_PCT = 0.10

# ETH/USDC LP
ETH_LP_LOW = 2100
ETH_LP_HIGH = 3000
ETH_PRICE_ALERT_PCT = 0.10

# 资金费率告警阈值（8小时费率）
FUNDING_RATE_THRESHOLD = 0.0005

# WBTC和BTC最大允许价差，超过就告警（0.01 = 1%）
WBTC_BTC_DEVIATION_ALERT = 0.01

# 连续多少次满足条件才推送TG消息，过滤瞬时假信号
ALERT_CONFIRM_TIMES = 2
