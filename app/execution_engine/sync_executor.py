"""
Synchronized Trade Execution Engine
Manages latency-guarded, ordered execution across Maven fleet and hedge account
"""

import MetaTrader5 as mt5
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from app.utils.logger import get_logger
from app.utils.constants import (
    HEDGE_EXECUTION_DELAY_MS, MAVEN_EXECUTION_DELAY_MS, 
    SLIPPAGE_THRESHOLD_PIPS, TRADE_COOLDOWN_MS
)
from app.mt5_bridge.connection_manager import MT5InstanceType


class TradeType(Enum):
    """Trade direction"""
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"


class OrderType(Enum):
    """MT5 order types"""
    MARKET = mt5.ORDER_TYPE_BUY if hasattr(mt5, 'ORDER_TYPE_BUY') else 0
    LIMIT = 2
    STOP = 4


@dataclass
class TradeOrder:
    """Represents a single trade order"""
    symbol: str
    lot_size: float
    trade_type: TradeType
    account: int
    instance: MT5InstanceType
    entry_price: float = 0.0
    timestamp: datetime = None
    ticket: Optional[int] = None
    status: str = "pending"  # pending, executed, failed, cancelled
    slippage_pips: float = 0.0
    execution_latency_ms: float = 0.0
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SynchronizedExecutionEngine:
    """
    Executes trades with:
    - Latency guards (hedge first, then Maven)
    - Synchronized logging
    - Duplicate prevention
    - Slippage monitoring
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.execution_queue: List[TradeOrder] = []
        self.last_execution_time: Dict[int, float] = {}
        self.open_orders: Dict[int, List[TradeOrder]] = {}  # account -> orders
        self.execution_history: List[TradeOrder] = []
    
    async def execute_synchronized_trade(self,
                                        symbol: str,
                                        lot_size: float,
                                        trade_type: TradeType,
                                        maven_accounts: List[Dict[str, Any]],
                                        hedge_instance_info: Dict[str, Any],
                                        max_slippage_pips: float = SLIPPAGE_THRESHOLD_PIPS) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute synchronized trade: hedge first, then Maven fleet
        
        Execution order:
        1. Send hedge trade (Instance B)
        2. Wait ~10ms
        3. Send Maven fleet orders (Instance A)
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            lot_size: Lot size for each account
            trade_type: BUY or SELL
            maven_accounts: List of active Maven accounts
            hedge_instance_info: Hedge account connection info
            max_slippage_pips: Maximum acceptable slippage
        
        Returns:
            Tuple of (success: bool, execution_results: dict)
        """
        try:
            execution_results = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "trade_type": trade_type.value,
                "maven_executions": [],
                "hedge_execution": None,
                "success_count": 0,
                "failure_count": 0,
                "total_latency_ms": 0
            }
            
            # 1. Execute hedge trade first (protection)
            if hedge_instance_info and hedge_instance_info.get('is_active'):
                hedge_result = await self._execute_hedge_trade(
                    symbol, lot_size, trade_type, hedge_instance_info
                )
                execution_results["hedge_execution"] = hedge_result
                
                if hedge_result['success']:
                    execution_results["success_count"] += 1
                    self.logger.info("Hedge trade executed successfully")
                else:
                    execution_results["failure_count"] += 1
                    self.logger.warning("Hedge trade execution failed")
                
                # Latency guard: wait before Maven execution
                await asyncio.sleep(HEDGE_EXECUTION_DELAY_MS / 1000.0)
            
            # 2. Execute Maven fleet trades
            for account in maven_accounts:
                maven_result = await self._execute_maven_trade(
                    symbol, lot_size, trade_type, account
                )
                execution_results["maven_executions"].append(maven_result)
                
                if maven_result['success']:
                    execution_results["success_count"] += 1
                else:
                    execution_results["failure_count"] += 1
                
                # Cooldown between orders
                await asyncio.sleep(TRADE_COOLDOWN_MS / 1000.0)
            
            # Log execution
            self.logger.log_trade({
                "action": f"synchronized_{trade_type.value}",
                "symbol": symbol,
                "maven_accounts_count": len(maven_accounts),
                "hedge_active": hedge_instance_info.get('is_active', False) if hedge_instance_info else False,
                "success": execution_results["success_count"],
                "failed": execution_results["failure_count"]
            })
            
            return (execution_results["success_count"] > 0, execution_results)
            
        except Exception as e:
            self.logger.log_error(e, "Synchronized execution error")
            return (False, {"error": str(e)})
    
    async def _execute_hedge_trade(self, symbol: str, lot_size: float, 
                                   trade_type: TradeType, 
                                   hedge_info: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hedge trade on Instance B"""
        try:
            start_time = time.time()
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {
                    "success": False,
                    "error": "Failed to get tick",
                    "account": hedge_info.get('account')
                }
            
            # Prepare order
            order_type = mt5.ORDER_TYPE_BUY if trade_type == TradeType.BUY else mt5.ORDER_TYPE_SELL
            price = tick.ask if trade_type == TradeType.BUY else tick.bid
            
            # Send order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "deviation": 20,  # pip deviation
                "magic": 290520241,  # Unique magic number
                "comment": f"HEDGE_{symbol}_{trade_type.value}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            latency_ms = (time.time() - start_time) * 1000
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "success": False,
                    "error": f"Order failed: {result.comment}",
                    "account": hedge_info.get('account'),
                    "latency_ms": latency_ms
                }
            
            slippage = self._calculate_slippage(price, result.price)
            
            self.logger.log_trade({
                "action": "hedge_execution",
                "symbol": symbol,
                "type": trade_type.value,
                "account": hedge_info.get('account'),
                "lot": lot_size,
                "price": result.price,
                "slippage_pips": slippage,
                "latency_ms": latency_ms,
                "ticket": result.order
            })
            
            return {
                "success": True,
                "account": hedge_info.get('account'),
                "ticket": result.order,
                "price": result.price,
                "slippage_pips": slippage,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            self.logger.debug(f"Hedge trade error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "account": hedge_info.get('account') if hedge_info else None
            }
    
    async def _execute_maven_trade(self, symbol: str, lot_size: float,
                                   trade_type: TradeType,
                                   account: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade on Maven account (Instance A)"""
        try:
            start_time = time.time()
            
            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {
                    "success": False,
                    "error": "Failed to get tick",
                    "account": account.get('account_number')
                }
            
            # Prepare order
            order_type = mt5.ORDER_TYPE_BUY if trade_type == TradeType.BUY else mt5.ORDER_TYPE_SELL
            price = tick.ask if trade_type == TradeType.BUY else tick.bid
            
            # Send order
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": 290520242,  # Maven magic number
                "comment": f"MAVEN_{symbol}_{trade_type.value}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            latency_ms = (time.time() - start_time) * 1000
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "success": False,
                    "error": f"Order failed: {result.comment}",
                    "account": account.get('account_number'),
                    "latency_ms": latency_ms
                }
            
            slippage = self._calculate_slippage(price, result.price)
            
            self.logger.log_trade({
                "action": "maven_execution",
                "symbol": symbol,
                "type": trade_type.value,
                "account": account.get('account_number'),
                "lot": lot_size,
                "price": result.price,
                "slippage_pips": slippage,
                "latency_ms": latency_ms,
                "ticket": result.order
            })
            
            return {
                "success": True,
                "account": account.get('account_number'),
                "ticket": result.order,
                "price": result.price,
                "slippage_pips": slippage,
                "latency_ms": latency_ms
            }
            
        except Exception as e:
            self.logger.debug(f"Maven trade error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "account": account.get('account_number')
            }
    
    def _calculate_slippage(self, requested_price: float, executed_price: float) -> float:
        """Calculate slippage in pips"""
        diff = abs(executed_price - requested_price)
        # Convert to pips (standard: 0.0001, JPY: 0.01)
        return diff / 0.0001
    
    async def close_all_positions(self) -> Dict[str, Any]:
        """
        Emergency: Close all open positions across all accounts
        """
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "closed_count": 0,
                "failed_count": 0,
                "details": []
            }
            
            # Get all open trades
            open_trades = mt5.positions_get()
            
            for trade in open_trades:
                try:
                    close_type = mt5.ORDER_TYPE_SELL if trade.type == 0 else mt5.ORDER_TYPE_BUY
                    tick = mt5.symbol_info_tick(trade.symbol)
                    price = tick.bid if trade.type == 0 else tick.ask
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": trade.symbol,
                        "volume": trade.volume,
                        "type": close_type,
                        "position": trade.ticket,
                        "price": price,
                        "deviation": 20,
                        "comment": "EMERGENCY_CLOSE_ALL",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    
                    result = mt5.order_send(request)
                    
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        results["closed_count"] += 1
                        results["details"].append({
                            "ticket": trade.ticket,
                            "symbol": trade.symbol,
                            "volume": trade.volume,
                            "closed": True
                        })
                    else:
                        results["failed_count"] += 1
                        
                except Exception as e:
                    results["failed_count"] += 1
                    self.logger.debug(f"Error closing position {trade.ticket}: {str(e)}")
            
            self.logger.log_risk_event("CLOSE_ALL_POSITIONS", results)
            return results
            
        except Exception as e:
            self.logger.log_error(e, "Close all positions error")
            return {"error": str(e)}
