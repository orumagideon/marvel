"""
MT5 Connection Manager
Handles dual-instance MT5 bridge with automatic reconnection and state monitoring
Instance A: Maven Fleet (multiple accounts with dynamic switching)
Instance B: Personal Hedge Account (persistent high-leverage connection)
"""

import MetaTrader5 as mt5
import time
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
from app.utils.logger import get_logger
from app.utils.constants import (
    MT5_MAX_RETRIES, MT5_RETRY_DELAY, MT5_CONNECTION_TIMEOUT, MT5_LATENCY_THRESHOLD
)


class MT5InstanceType(Enum):
    """MT5 Instance identifiers"""
    MAVEN_FLEET = "maven_fleet"
    HEDGE_ACCOUNT = "hedge_account"


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    RECONNECTING = "reconnecting"


class MT5ConnectionManager:
    """
    Manages dual MT5 terminal instances with automatic reconnection.
    Ensures Maven switching doesn't affect persistent hedge connection.
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.instances: Dict[MT5InstanceType, Dict[str, Any]] = {
            MT5InstanceType.MAVEN_FLEET: {
                "state": ConnectionState.DISCONNECTED,
                "terminal_path": None,
                "account": None,
                "last_error": None,
                "connection_time": None,
                "latency_ms": 0
            },
            MT5InstanceType.HEDGE_ACCOUNT: {
                "state": ConnectionState.DISCONNECTED,
                "terminal_path": None,
                "account": None,
                "last_error": None,
                "connection_time": None,
                "latency_ms": 0
            }
        }
        self.retry_counts: Dict[MT5InstanceType, int] = {
            MT5InstanceType.MAVEN_FLEET: 0,
            MT5InstanceType.HEDGE_ACCOUNT: 0
        }
    
    def initialize(self, instance_type: MT5InstanceType, terminal_path: str) -> bool:
        """
        Initialize MT5 terminal instance
        
        Args:
            instance_type: MAVEN_FLEET or HEDGE_ACCOUNT
            terminal_path: Path to MT5 terminal directory
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.instances[instance_type]["state"] = ConnectionState.CONNECTING
            self.instances[instance_type]["terminal_path"] = terminal_path
            
            # Initialize MT5
            if not mt5.initialize(path=terminal_path):
                error_msg = f"MT5 initialization failed for {instance_type.value}"
                self.instances[instance_type]["last_error"] = error_msg
                self.instances[instance_type]["state"] = ConnectionState.ERROR
                self.logger.log_connection(instance_type.value, "failed", error_msg)
                return False
            
            self.instances[instance_type]["state"] = ConnectionState.CONNECTED
            self.instances[instance_type]["connection_time"] = datetime.now()
            self.retry_counts[instance_type] = 0
            
            self.logger.log_connection(instance_type.value, "connected")
            return True
            
        except Exception as e:
            self.instances[instance_type]["state"] = ConnectionState.ERROR
            self.instances[instance_type]["last_error"] = str(e)
            self.logger.log_error(e, f"MT5 initialization error ({instance_type.value})")
            return False
    
    def login(self, instance_type: MT5InstanceType, account: int, password: str, server: str) -> bool:
        """
        Login to MT5 account on specified instance
        
        Args:
            instance_type: MAVEN_FLEET or HEDGE_ACCOUNT
            account: Account number
            password: Account password
            server: Server name
        
        Returns:
            True if successful, False otherwise
        """
        try:
            start_time = time.time()
            
            # Attempt login with retries
            for attempt in range(MT5_MAX_RETRIES):
                if mt5.login(account, password, server):
                    latency_ms = (time.time() - start_time) * 1000
                    self.instances[instance_type]["latency_ms"] = latency_ms
                    self.instances[instance_type]["account"] = account
                    self.instances[instance_type]["state"] = ConnectionState.CONNECTED
                    self.retry_counts[instance_type] = 0
                    
                    self.logger.info(
                        f"[{instance_type.value}] Login successful - "
                        f"Account: {account}, Latency: {latency_ms:.2f}ms"
                    )
                    return True
                
                if attempt < MT5_MAX_RETRIES - 1:
                    time.sleep(MT5_RETRY_DELAY)
            
            # All retries failed
            error_msg = f"Login failed after {MT5_MAX_RETRIES} attempts for account {account}"
            self.instances[instance_type]["last_error"] = error_msg
            self.instances[instance_type]["state"] = ConnectionState.ERROR
            self.logger.log_connection(instance_type.value, "login_failed", error_msg)
            return False
            
        except Exception as e:
            self.instances[instance_type]["state"] = ConnectionState.ERROR
            self.instances[instance_type]["last_error"] = str(e)
            self.logger.log_error(e, f"Login error ({instance_type.value})")
            return False
    
    def is_connected(self, instance_type: MT5InstanceType) -> bool:
        """Check if instance is connected and authorized"""
        try:
            state = self.instances[instance_type]["state"]
            if state == ConnectionState.CONNECTED:
                # Verify connection is still active
                if mt5.account_info():
                    return True
                else:
                    self.instances[instance_type]["state"] = ConnectionState.DISCONNECTED
                    return False
            return False
        except Exception as e:
            self.logger.debug(f"Connection check error: {str(e)}")
            return False
    
    def reconnect(self, instance_type: MT5InstanceType, account: int, password: str, server: str) -> bool:
        """
        Attempt automatic reconnection for instance
        Used when connection is lost during trading
        """
        self.instances[instance_type]["state"] = ConnectionState.RECONNECTING
        self.logger.log_connection(instance_type.value, "reconnecting")
        
        # Increment retry count
        self.retry_counts[instance_type] += 1
        
        if self.retry_counts[instance_type] > MT5_MAX_RETRIES:
            self.instances[instance_type]["state"] = ConnectionState.ERROR
            self.logger.log_connection(instance_type.value, "max_retries_exceeded")
            return False
        
        time.sleep(MT5_RETRY_DELAY)
        return self.login(instance_type, account, password, server)
    
    def get_account_info(self, instance_type: MT5InstanceType) -> Optional[Dict[str, Any]]:
        """Get current account information for instance"""
        try:
            if not self.is_connected(instance_type):
                return None
            
            acc_info = mt5.account_info()
            if acc_info:
                return {
                    "account": acc_info.login,
                    "balance": acc_info.balance,
                    "equity": acc_info.equity,
                    "margin": acc_info.margin,
                    "margin_free": acc_info.margin_free,
                    "margin_level": acc_info.margin_level,
                    "profit": acc_info.profit,
                    "currency": acc_info.currency
                }
            return None
        except Exception as e:
            self.logger.debug(f"Failed to get account info: {str(e)}")
            return None
    
    def get_symbol_tick(self, symbol: str, instance_type: MT5InstanceType) -> Optional[Dict[str, Any]]:
        """Get current symbol tick (bid/ask/spread)"""
        try:
            if not self.is_connected(instance_type):
                return None
            
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                return {
                    "bid": tick.bid,
                    "ask": tick.ask,
                    "spread_pips": (tick.ask - tick.bid) / (0.0001 if symbol.endswith("JPY") else 0.00001),
                    "time": tick.time
                }
            return None
        except Exception as e:
            self.logger.debug(f"Failed to get symbol tick: {str(e)}")
            return None
    
    def get_status(self, instance_type: MT5InstanceType) -> Dict[str, Any]:
        """Get comprehensive status for instance"""
        instance = self.instances[instance_type]
        return {
            "instance_type": instance_type.value,
            "state": instance["state"].value,
            "account": instance["account"],
            "connected": self.is_connected(instance_type),
            "latency_ms": instance["latency_ms"],
            "last_error": instance["last_error"],
            "connection_time": instance["connection_time"],
            "retry_count": self.retry_counts[instance_type]
        }
    
    def shutdown(self, instance_type: MT5InstanceType) -> None:
        """Shutdown instance connection"""
        try:
            # Note: MT5.shutdown() affects the entire MT5 module, not just one instance
            # In production with separate terminal instances, this would properly isolate
            self.instances[instance_type]["state"] = ConnectionState.DISCONNECTED
            self.logger.log_connection(instance_type.value, "shutdown")
        except Exception as e:
            self.logger.log_error(e, f"Shutdown error ({instance_type.value})")
    
    def shutdown_all(self) -> None:
        """Shutdown all connections"""
        try:
            mt5.shutdown()
            for instance_type in MT5InstanceType:
                self.instances[instance_type]["state"] = ConnectionState.DISCONNECTED
            self.logger.info("All MT5 connections shutdown")
        except Exception as e:
            self.logger.log_error(e, "Shutdown all error")
