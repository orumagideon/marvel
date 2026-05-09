"""
Global constants and configuration for Marvel Trading Dashboard
"""

# MT5 Configuration
MT5_SYMBOL_PRIMARY = "US100"
MT5_TIMEFRAME = 1  # M1
MT5_MAX_RETRIES = 5
MT5_RETRY_DELAY = 2  # seconds
MT5_CONNECTION_TIMEOUT = 30  # seconds
MT5_LATENCY_THRESHOLD = 100  # ms

# Maven Prop Firm Configuration
MAVEN_ACCOUNT_SLOTS = 5
MAVEN_MAX_ACCOUNTS = 20  # Future scaling
MAVEN_PHASE_1 = "Phase 1"
MAVEN_PHASE_2 = "Phase 2"

# Risk Management
DEFAULT_DAILY_DRAWDOWN = 400.0  # USD
MIN_FREE_MARGIN_RATIO = 0.15  # 15%
MAX_SPREAD_PIPS = 0.5
SLIPPAGE_THRESHOLD_PIPS = 1.0
TRADE_COOLDOWN_MS = 50

# Recovery Engine
DEFAULT_DESIRED_SURPLUS = 100.0  # USD
RECOVERY_LOSS_PERSISTENCE = "data/recovery_log.csv"
ACCOUNTS_DB = "data/accounts.json"

# UI Configuration
UI_THEME = "dark"
UI_REFRESH_RATE_MS = 100
UI_MARKET_FEED_REFRESH_MS = 150
UI_CHART_UPDATE_MS = 500

# Logging
LOG_DIR = "logs"
LOG_MAX_SIZE_MB = 10
LOG_BACKUP_COUNT = 10

# Latency Guards
HEDGE_EXECUTION_DELAY_MS = 10
MAVEN_EXECUTION_DELAY_MS = 20

# Trading Symbols
HEDGE_SYMBOLS = ["USDJPY", "EURUSD", "GBPUSD"]
VOLUME_UNIT_PRECISION = 0.01  # 0.01 lot increments

# Emergency Protection
EQUITY_CRITICAL_THRESHOLD = 10.0  # USD away from drawdown limit
