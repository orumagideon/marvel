"""
Marvel System Configuration
Central configuration management for the trading system
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.logger import get_logger


class SystemConfig:
    """Central configuration manager"""
    
    DEFAULT_CONFIG = {
        "mt5": {
            "maven_terminal_path": "",
            "hedge_terminal_path": "",
            "max_retries": 5,
            "retry_delay_seconds": 2,
            "connection_timeout_seconds": 30
        },
        "accounts": {
            "default_slots": 5,
            "max_slots": 20
        },
        "trading": {
            "primary_symbol": "US100",
            "timeframe_minutes": 1,
            "default_lot_size": 0.1,
            "hedge_symbols": ["USDJPY", "EURUSD", "GBPUSD"]
        },
        "recovery": {
            "desired_surplus": 100.0,
            "recovery_log_path": "data/recovery_log.csv",
            "enabled": True
        },
        "prop_firm": {
            "default_account_size": 5000.0,
            "default_purchase_fee": 59.0,
            "default_profit_target_pct": 8.0,
            "default_daily_drawdown_pct": 5.0,
            "default_overall_drawdown_pct": 10.0,
            "default_max_lots": 5.0,
            "default_profit_split_pct": 80.0,
            "default_risk_mode": "balanced",
            "saved_templates": {}
        },
        "risk_management": {
            "daily_drawdown_limit": 400.0,
            "min_free_margin_ratio": 0.15,
            "max_spread_pips": 0.5,
            "critical_equity_threshold": 10.0,
            "auto_stop_enabled": True
        },
        "execution": {
            "hedge_execution_delay_ms": 10,
            "maven_execution_delay_ms": 20,
            "trade_cooldown_ms": 50,
            "max_slippage_pips": 1.0
        },
        "ui": {
            "theme": "dark",
            "refresh_rate_ms": 100,
            "market_feed_refresh_ms": 150,
            "window_width": 1600,
            "window_height": 900,
            "auto_connect_on_startup": True
        },
        "logging": {
            "log_directory": "logs",
            "max_file_size_mb": 10,
            "backup_count": 10,
            "console_level": "INFO",
            "file_level": "DEBUG"
        }
    }
    
    def __init__(self, config_file: str = "data/config.json"):
        self.logger = get_logger()
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load config from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                # Merge with defaults (in case new keys added)
                config = self.DEFAULT_CONFIG.copy()
                config.update(loaded)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return config
            else:
                self._save_config(self.DEFAULT_CONFIG)
                self.logger.info(f"Default configuration created at {self.config_file}")
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            self.logger.log_error(e, "Failed to load config")
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            self.logger.log_error(e, "Failed to save config")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation (e.g., 'mt5.maven_terminal_path')"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot notation"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def get_mt5_config(self) -> Dict[str, Any]:
        """Get MT5 configuration"""
        return self.config.get('mt5', {})
    
    def get_trading_config(self) -> Dict[str, Any]:
        """Get trading configuration"""
        return self.config.get('trading', {})
    
    def get_risk_config(self) -> Dict[str, Any]:
        """Get risk management configuration"""
        return self.config.get('risk_management', {})
    
    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration"""
        return self.config.get('execution', {})
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config(self.config)
        self.logger.info("Configuration reset to defaults")


# Global config instance
_config_instance = None


def get_config() -> SystemConfig:
    """Get or create global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SystemConfig()
    return _config_instance
