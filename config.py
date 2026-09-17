import os

# Telegram Bot Credentials (Get from @BotFather)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "YOUR_CHANNEL_OR_GROUP_ID")

# Quotex Real WebSocket Session (Optional - for direct real broker stream)
# Get 'ssid' from browser: Inspect > Application > Cookies > qxbroker.com > ssid
QUOTEX_SSID = os.getenv("QUOTEX_SSID", "")

# Bot Branding & Settings
BOT_NAME = "XT AI PRO V5"
ADMIN_USER_IDS = [123456789]

# Supported Quotex OTC & Forex Pairs
PAIRS = [
    "USDMXN-OTC",
    "AUDCAD-OTC",
    "XRPUSD-OTC",
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDJPY-OTC",
    "NZDUSD-OTC",
    "BTCUSD-OTC"
]

# Signal Frequency & Expiry Settings
TIMEFRAME = "1M"           # 1 Minute candles
EXPIRY_SECONDS = 60        # 60s for 1M binary expiry
AUTO_SIGNAL_INTERVAL = 180 # Check for new signal every 3 minutes (in seconds)
MIN_ACCURACY_THRESHOLD = 82 # Only send signals with >= 82% confidence
