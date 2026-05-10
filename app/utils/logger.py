"""
Structured logging system for Marvel Trading Dashboard
Provides rotating file logs with console output for diagnostics and audit trails
"""

import logging
import os
import sys
import platform
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict


class StructuredLogger:
    """Structured logging with JSON support for trade execution and diagnostics

    By default logs are written to a user-specific application data folder on
    Windows to avoid placing runtime logs inside the application/distribution
    folder (prevents file-locks during packaging). In development (non-frozen)
    the repository-relative `logs/` directory is used for convenience.
    """
    
    def __init__(self, name: str = "marvel", logs_dir: str = None):
        # Determine default logs directory when none provided
        if logs_dir:
            target = Path(logs_dir)
        else:
            # On Windows prefer %APPDATA%\MarvelTradingDashboard\logs
            if platform.system().lower().startswith("win"):
                appdata = os.getenv("APPDATA") or str(Path.home() / "AppData" / "Roaming")
                target = Path(appdata) / "MarvelTradingDashboard" / "logs"
            else:
                # Use repo-local logs directory during development on non-Windows
                target = Path("logs")

        self.logs_dir = target
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Rotating file handler for main logs
        log_file = self.logs_dir / f"marvel_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_trade(self, trade_data: Dict[str, Any]) -> None:
        """Log trade execution with structured JSON"""
        trade_log_file = self.logs_dir / "trades.jsonl"
        trade_data['timestamp'] = datetime.now().isoformat()
        with open(trade_log_file, 'a') as f:
            f.write(json.dumps(trade_data) + '\n')
        self.logger.info(f"Trade logged: {trade_data.get('action')} - Account: {trade_data.get('account')}")
    
    def log_connection(self, instance: str, status: str, details: str = "") -> None:
        """Log MT5 connection events"""
        msg = f"[{instance}] Connection {status}"
        if details:
            msg += f": {details}"
        self.logger.info(msg)
    
    def log_recovery(self, recovery_data: Dict[str, Any]) -> None:
        """Log recovery engine calculations"""
        recovery_log_file = self.logs_dir / "recovery.jsonl"
        recovery_data['timestamp'] = datetime.now().isoformat()
        with open(recovery_log_file, 'a') as f:
            f.write(json.dumps(recovery_data) + '\n')
        self.logger.info(f"Recovery logged: {recovery_data.get('action')}")
    
    def log_error(self, error: Exception, context: str = "") -> None:
        """Log errors with context"""
        self.logger.error(f"{context}: {str(error)}", exc_info=True)
    
    def log_risk_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log risk management events"""
        risk_log_file = self.logs_dir / "risk_events.jsonl"
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details
        }
        with open(risk_log_file, 'a') as f:
            f.write(json.dumps(event_data) + '\n')
        self.logger.warning(f"Risk event: {event_type} - {details}")
    
    def info(self, message: str) -> None:
        self.logger.info(message)
    
    def debug(self, message: str) -> None:
        self.logger.debug(message)
    
    def warning(self, message: str) -> None:
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        self.logger.error(message)


# Global logger instance
_logger_instance = None


def get_logger(name: str = "marvel", logs_dir: str = None) -> StructuredLogger:
    """Get or create global logger instance

    Pass `logs_dir` to override the default path. When omitted the logger
    chooses a safe OS-specific default that avoids writing into the
    application `dist` folder on Windows.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = StructuredLogger(name, logs_dir)
    return _logger_instance
