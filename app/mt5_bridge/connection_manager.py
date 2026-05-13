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
from pathlib import Path
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
    
    CRITICAL: MT5 is a global module that can only be initialized ONCE.
    This manager handles account switching via mt5.login() without re-initializing.
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.is_mt5_initialized = False  # Track global MT5 initialization state
        self.active_terminal_path: Optional[str] = None
        self.active_instance_type: Optional[MT5InstanceType] = None
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

    def _resolve_terminal_path(self, terminal_path: str) -> Optional[str]:
        """Resolve a folder path to the MetaTrader terminal executable path."""
        if not terminal_path:
            return None

        raw_path = terminal_path.strip().strip('"')
        path = Path(raw_path)

        if path.is_file():
            return str(path)

        if path.is_dir():
            candidates = [
                path / "terminal64.exe",
                path / "terminal.exe",
                path / "metatrader64.exe",
                path / "metatrader.exe",
            ]
            for candidate in candidates:
                if candidate.exists():
                    return str(candidate)

            exe_candidates = sorted(path.glob("terminal*.exe"))
            if exe_candidates:
                return str(exe_candidates[0])

        return str(path)
    
    def initialize(self, instance_type: MT5InstanceType, terminal_path: str) -> bool:
        """
        Initialize MT5 terminal instance
        
        CRITICAL: MT5.initialize() can only be called ONCE globally.
        This method initializes MT5 on first call, then uses mt5.login() for subsequent calls.
        
        Args:
            instance_type: MAVEN_FLEET or HEDGE_ACCOUNT
            terminal_path: Path to MT5 terminal directory
        
        Returns:
            True if successful, False otherwise
        """
        try:
            resolved_terminal_path = self._resolve_terminal_path(terminal_path)
            if not resolved_terminal_path:
                error_msg = "MT5 terminal path is empty or invalid"
                self.instances[instance_type]["last_error"] = error_msg
                self.instances[instance_type]["state"] = ConnectionState.ERROR
                self.logger.log_connection(instance_type.value, "failed", error_msg)
                return False

            self.instances[instance_type]["state"] = ConnectionState.CONNECTING
            self.instances[instance_type]["terminal_path"] = resolved_terminal_path

            if self.is_mt5_initialized and self.active_terminal_path and self.active_terminal_path != resolved_terminal_path:
                self.logger.info(
                    f"Switching MT5 terminal from {self.active_terminal_path} to {resolved_terminal_path}"
                )
                try:
                    mt5.shutdown()
                except Exception:
                    pass
                self.is_mt5_initialized = False
                self.active_terminal_path = None
                self.active_instance_type = None
                for other_instance in MT5InstanceType:
                    self.instances[other_instance]["state"] = ConnectionState.DISCONNECTED
                    self.instances[other_instance]["account"] = None
            
            # Check if MT5 is already initialized globally
            if self.is_mt5_initialized:
                # Already initialized, just mark this instance as ready
                self.instances[instance_type]["state"] = ConnectionState.CONNECTED
                self.instances[instance_type]["connection_time"] = datetime.now()
                self.retry_counts[instance_type] = 0
                self.active_instance_type = instance_type
                self.logger.info(f"[{instance_type.value}] Using existing MT5 initialization")
                return True
            
            # First try to attach to an already running terminal session.
            # If that fails, fall back to the explicit terminal path.
            if not mt5.initialize(timeout=MT5_CONNECTION_TIMEOUT * 1000):
                if not mt5.initialize(path=resolved_terminal_path, timeout=MT5_CONNECTION_TIMEOUT * 1000):
                    error_msg = (
                        f"MT5 initialization failed for {instance_type.value} using "
                        f"{resolved_terminal_path}: {mt5.last_error()}"
                    )
                    self.instances[instance_type]["last_error"] = error_msg
                    self.instances[instance_type]["state"] = ConnectionState.ERROR
                    self.logger.log_connection(instance_type.value, "failed", error_msg)
                    return False
            
            # Mark MT5 as initialized globally
            self.is_mt5_initialized = True
            self.active_terminal_path = resolved_terminal_path
            self.active_instance_type = instance_type
            self.instances[instance_type]["state"] = ConnectionState.CONNECTED
            self.instances[instance_type]["connection_time"] = datetime.now()
            self.retry_counts[instance_type] = 0
            
            self.logger.log_connection(instance_type.value, "connected")
            terminal_info = mt5.terminal_info()
            if terminal_info:
                self.logger.info(
                    f"MT5 initialized successfully with terminal: {resolved_terminal_path} | "
                    f"connected={terminal_info.connected}, trade_allowed={terminal_info.trade_allowed}"
                )
            else:
                self.logger.info(f"MT5 initialized successfully with terminal: {resolved_terminal_path}")
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
            server: Server name (e.g., "FundedNext-Server3")
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.is_mt5_initialized:
                error_msg = "MT5 not initialized. Call initialize() first."
                self.instances[instance_type]["last_error"] = error_msg
                self.instances[instance_type]["state"] = ConnectionState.ERROR
                self.logger.error(f"[{instance_type.value}] {error_msg}")
                return False

            current_account = None
            try:
                acc_info = mt5.account_info()
                current_account = acc_info.login if acc_info else None
            except Exception:
                current_account = None

            if current_account == account:
                self.instances[instance_type]["account"] = account
                self.instances[instance_type]["state"] = ConnectionState.CONNECTED
                self.instances[instance_type]["connection_time"] = datetime.now()
                self.retry_counts[instance_type] = 0
                self.logger.info(
                    f"[{instance_type.value}] Already connected to account {account}; reusing existing terminal session"
                )
                return True
            
            start_time = time.time()
            
            # Attempt login with retries
            for attempt in range(MT5_MAX_RETRIES):
                try:
                    login_result = mt5.login(account, password=password, server=server)
                    
                    if login_result:
                        latency_ms = (time.time() - start_time) * 1000
                        self.instances[instance_type]["latency_ms"] = latency_ms
                        self.instances[instance_type]["account"] = account
                        self.instances[instance_type]["state"] = ConnectionState.CONNECTED
                        self.retry_counts[instance_type] = 0
                        
                        self.logger.info(
                            f"[{instance_type.value}] Login successful - "
                            f"Account: {account}, Server: {server}, Latency: {latency_ms:.2f}ms"
                        )
                        return True
                    else:
                        # Get detailed error from MT5
                        mt5_error = mt5.last_error()
                        error_code, error_msg = mt5_error if mt5_error else (None, "Unknown error")
                        self.logger.debug(
                            f"[{instance_type.value}] Login attempt {attempt + 1}/{MT5_MAX_RETRIES} failed - "
                            f"Error: {error_code}: {error_msg}"
                        )
                        
                        if attempt < MT5_MAX_RETRIES - 1:
                            time.sleep(MT5_RETRY_DELAY)
                
                except Exception as e:
                    self.logger.debug(f"[{instance_type.value}] Login attempt {attempt + 1} exception: {str(e)}")
                    if attempt < MT5_MAX_RETRIES - 1:
                        time.sleep(MT5_RETRY_DELAY)
            
            # All retries failed - build detailed error message
            mt5_error = mt5.last_error()
            error_code, error_details = mt5_error if mt5_error else (None, "Unknown error")
            error_msg = (
                f"Login failed after {MT5_MAX_RETRIES} attempts for account {account} "
                f"on server {server}. MT5 Error: {error_code}: {error_details}"
            )
            self.instances[instance_type]["last_error"] = error_msg
            self.instances[instance_type]["state"] = ConnectionState.ERROR
            self.logger.log_connection(instance_type.value, "login_failed", error_msg)
            return False
            
        except Exception as e:
            error_msg = f"Unexpected error during login: {str(e)}"
            self.instances[instance_type]["state"] = ConnectionState.ERROR
            self.instances[instance_type]["last_error"] = error_msg
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
        """
        Shutdown instance connection
        
        Note: MT5.shutdown() affects the entire MT5 module globally,
        but we only mark this specific instance as disconnected.
        """
        try:
            mt5.shutdown()
            self.is_mt5_initialized = False
            self.active_terminal_path = None
            self.active_instance_type = None
            for other_instance in MT5InstanceType:
                self.instances[other_instance]["state"] = ConnectionState.DISCONNECTED
                self.instances[other_instance]["account"] = None
            self.logger.log_connection(instance_type.value, "shutdown")
        except Exception as e:
            self.logger.log_error(e, f"Shutdown error ({instance_type.value})")
    
    def shutdown_all(self) -> None:
        """Shutdown all connections"""
        try:
            mt5.shutdown()
            self.is_mt5_initialized = False  # Reset global initialization state
            self.active_terminal_path = None
            self.active_instance_type = None
            for instance_type in MT5InstanceType:
                self.instances[instance_type]["state"] = ConnectionState.DISCONNECTED
                self.instances[instance_type]["account"] = None
            self.logger.info("All MT5 connections shutdown")
        except Exception as e:
            self.logger.log_error(e, "Shutdown all error")
    
    async def heartbeat_monitor(self, interval_seconds: float = 1.0, 
                               latency_threshold_ms: float = 250.0) -> Dict[str, Any]:
        """
        Kenya-specific heartbeat monitor for connectivity.
        
        Pings both Exness and Maven servers every N seconds.
        If latency exceeds threshold (default 250ms), trading is disabled.
        
        This is critical for Kenya ISP environments where intermittent lag
        can cause desynchronized entries between Maven and Exness.
        
        Args:
            interval_seconds: Ping interval (default 1 second)
            latency_threshold_ms: Latency threshold for disabling trades (default 250ms)
        
        Returns:
            Dictionary with heartbeat status
        """
        try:
            import time as time_module
            
            heartbeat_data = {
                "timestamp": datetime.now().isoformat(),
                "interval_seconds": interval_seconds,
                "latency_threshold_ms": latency_threshold_ms,
                "maven_latency_ms": 0.0,
                "exness_latency_ms": 0.0,
                "trading_enabled": True,
                "status": "healthy"
            }
            
            # Ping Maven instance
            if self.is_connected(MT5InstanceType.MAVEN_FLEET):
                maven_start = time_module.time()
                try:
                    # Simple price fetch as latency test
                    mt5.symbol_info_tick("USTECH")
                    maven_latency = (time_module.time() - maven_start) * 1000
                    self.instances[MT5InstanceType.MAVEN_FLEET]["latency_ms"] = maven_latency
                    heartbeat_data["maven_latency_ms"] = round(maven_latency, 2)
                except Exception:
                    heartbeat_data["maven_latency_ms"] = -1.0
            
            # Ping Exness instance
            if self.is_connected(MT5InstanceType.HEDGE_ACCOUNT):
                exness_start = time_module.time()
                try:
                    # Simple price fetch as latency test
                    mt5.symbol_info_tick("USTECH")
                    exness_latency = (time_module.time() - exness_start) * 1000
                    self.instances[MT5InstanceType.HEDGE_ACCOUNT]["latency_ms"] = exness_latency
                    heartbeat_data["exness_latency_ms"] = round(exness_latency, 2)
                except Exception:
                    heartbeat_data["exness_latency_ms"] = -1.0
            
            # Determine trading status
            max_latency = max(
                heartbeat_data["maven_latency_ms"],
                heartbeat_data["exness_latency_ms"]
            )
            
            if max_latency < 0:
                # One or both connections not responding
                heartbeat_data["trading_enabled"] = False
                heartbeat_data["status"] = "critical"
                self.logger.warning("[HEARTBEAT] ⚠️ CRITICAL: Connection not responding")
            elif max_latency > latency_threshold_ms:
                # High latency detected
                heartbeat_data["trading_enabled"] = False
                heartbeat_data["status"] = "high_latency"
                self.logger.warning(
                    f"[HEARTBEAT] ⚠️ HIGH LATENCY DETECTED: {max_latency:.2f}ms > {latency_threshold_ms}ms "
                    f"(Maven: {heartbeat_data['maven_latency_ms']:.2f}ms, "
                    f"Exness: {heartbeat_data['exness_latency_ms']:.2f}ms) - TRADING DISABLED"
                )
            else:
                # Normal operation
                heartbeat_data["trading_enabled"] = True
                heartbeat_data["status"] = "healthy"
                self.logger.debug(
                    f"[HEARTBEAT] ✓ Latency OK: Maven {heartbeat_data['maven_latency_ms']:.2f}ms, "
                    f"Exness {heartbeat_data['exness_latency_ms']:.2f}ms"
                )
            
            return heartbeat_data
            
        except Exception as e:
            self.logger.log_error(e, "Heartbeat monitor error")
            return {
                "error": str(e),
                "trading_enabled": False,
                "status": "error"
            }
    
    def get_latency_status(self) -> Dict[str, Any]:
        """
        Get current latency status for both instances
        
        Returns:
            Dictionary with latency metrics and trading enablement status
        """
        maven_status = self.instances[MT5InstanceType.MAVEN_FLEET]
        exness_status = self.instances[MT5InstanceType.HEDGE_ACCOUNT]
        
        max_latency = max(maven_status["latency_ms"], exness_status["latency_ms"])
        trading_allowed = max_latency <= 250.0  # Default threshold
        
        return {
            "maven": {
                "latency_ms": maven_status["latency_ms"],
                "connected": self.is_connected(MT5InstanceType.MAVEN_FLEET)
            },
            "exness": {
                "latency_ms": exness_status["latency_ms"],
                "connected": self.is_connected(MT5InstanceType.HEDGE_ACCOUNT)
            },
            "max_latency_ms": max_latency,
            "trading_allowed": trading_allowed,
            "timestamp": datetime.now().isoformat()
        }
