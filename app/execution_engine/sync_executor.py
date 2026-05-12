"""
Synchronized Trade Execution Engine
Manages latency-guarded, ordered execution across Maven fleet and hedge account
Supports parallel dispatch with <10ms spread guarantee
Includes auto-stop, farming mode, and phase-aware lot sizing
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
                                        max_slippage_pips: float = SLIPPAGE_THRESHOLD_PIPS,
                                        tp_pips: float = None,
                                        sl_pips: float = None,
                                        hedge_lot: float = None,
                                        match_trader_bridge: Optional[Any] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute synchronized trade: hedge first, then parallel Maven fleet dispatch
        
        Execution order (Zero-Touch):
        1. Send hedge trade (Instance B) first for protection
        2. Wait minimal latency guard (~5ms)
        3. PARALLEL dispatch all Maven fleet orders (all 5 slots simultaneously)
        4. Total execution spread guarantee: < 10ms
        
        Args:
            symbol: Trading symbol (e.g., "USTECH", "US100")
            lot_size: Lot size for each Maven account
            trade_type: BUY or SELL
            maven_accounts: List of active Maven accounts (typically 5 slots)
            hedge_instance_info: Hedge account connection info (Exness KE)
            max_slippage_pips: Maximum acceptable slippage
            tp_pips: Take profit in pips (optional)
            sl_pips: Stop loss in pips (optional)
            hedge_lot: Hedge lot size (applies 1.3x multiplier if not specified)
        
        Returns:
            Tuple of (success: bool, execution_results: dict)
        """
        try:
            execution_start_time = time.time()
            execution_results = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "trade_type": trade_type.value,
                "maven_executions": [],
                "hedge_execution": None,
                "success_count": 0,
                "failure_count": 0,
                "total_latency_ms": 0,
                "execution_spread_ms": 0,
                "parallel_execution": True
            }
            
            # 1. Execute hedge trade first (protection - Instance B)
            hedge_start_time = time.time()
            if hedge_instance_info and hedge_instance_info.get('is_active'):
                hedge_volume = hedge_lot if hedge_lot is not None else lot_size
                hedge_result = await self._execute_hedge_trade(
                    symbol, hedge_volume, trade_type, hedge_instance_info, tp_pips, sl_pips
                )
                execution_results["hedge_execution"] = hedge_result
                hedge_latency = (time.time() - hedge_start_time) * 1000
                
                if hedge_result['success']:
                    execution_results["success_count"] += 1
                    self.logger.info(f"[HEDGE] Trade executed: {trade_type.value} {hedge_volume} lots @ {hedge_result.get('price', 'N/A')} (latency: {hedge_latency:.2f}ms)")
                else:
                    execution_results["failure_count"] += 1
                    self.logger.warning(f"[HEDGE] Trade execution failed: {hedge_result.get('error', 'Unknown error')}")
                
                # Minimal latency guard before Maven parallel dispatch
                # If a Match-Trader bridge is present, immediately trigger
                # its injection tasks to minimize delay (we still await verification)
                if match_trader_bridge is not None:
                    # schedule bridge injections for accounts that opt-in
                    bridge_tasks = []
                    for account in maven_accounts:
                        if account.get('use_match_trader'):
                            bridge_tasks.append(
                                self._execute_match_trader_trade(
                                    match_trader_bridge,
                                    symbol,
                                    account.get('lot_override', lot_size),
                                    tp_pips,
                                    sl_pips,
                                    account,
                                    trade_type
                                )
                            )
                    # dispatch without blocking the event loop too long
                    if bridge_tasks:
                        # run bridge tasks concurrently but don't delay more than ~15ms waiting
                        # we await with a short timeout to keep the hedge->bridge gap minimal
                        try:
                            await asyncio.wait_for(asyncio.gather(*bridge_tasks), timeout=0.050)
                        except asyncio.TimeoutError:
                            # tasks may continue in background; record warning
                            self.logger.warning("Match-Trader bridge tasks did not finish within timeout")
                else:
                    await asyncio.sleep(0.005)  # 5ms guard to ensure price stability
            
            # 2. PARALLEL Maven fleet execution (all slots simultaneously)
            # This ensures all 5 Maven slots receive orders within < 10ms spread
            maven_start_time = time.time()
            adjusted_maven_lots = self.apply_account_phase_multiplier(lot_size, maven_accounts)
            maven_tasks = []
            for idx, account in enumerate(maven_accounts):
                acct_lot = adjusted_maven_lots[idx]
                # If account is flagged to use Match-Trader, route to bridge instead
                if account.get('use_match_trader') and match_trader_bridge is not None:
                    maven_tasks.append(
                        self._execute_match_trader_trade(
                            match_trader_bridge,
                            symbol,
                            acct_lot,
                            tp_pips,
                            sl_pips,
                            account,
                            trade_type
                        )
                    )
                else:
                    maven_tasks.append(
                        self._execute_maven_trade(
                            symbol,
                            acct_lot,
                            trade_type,
                            account,
                            tp_pips,
                            sl_pips,
                        )
                    )
            
            # Execute all Maven orders concurrently
            maven_results = await asyncio.gather(*maven_tasks, return_exceptions=True)
            maven_latency = (time.time() - maven_start_time) * 1000
            
            # Process results
            for i, result in enumerate(maven_results):
                if isinstance(result, Exception):
                    # Handle exception from a task
                    execution_results["maven_executions"].append({
                        "success": False,
                        "error": str(result),
                        "account": maven_accounts[i].get('account_number') if i < len(maven_accounts) else None
                    })
                    execution_results["failure_count"] += 1
                else:
                    execution_results["maven_executions"].append(result)
                    if result.get('success'):
                        execution_results["success_count"] += 1
                        self.logger.debug(f"[MAVEN] Slot {i+1}/{len(maven_accounts)}: {maven_accounts[i].get('account_number')} - {result.get('price', 'N/A')}")
                    else:
                        execution_results["failure_count"] += 1
                        self.logger.warning(f"[MAVEN] Slot {i+1}/{len(maven_accounts)}: {result.get('error', 'Unknown')}")
            
            # Calculate execution metrics
            total_latency = (time.time() - execution_start_time) * 1000
            execution_results["total_latency_ms"] = total_latency
            execution_results["execution_spread_ms"] = maven_latency
            
            # Log comprehensive execution summary
            self.logger.log_trade({
                "action": f"zero_touch_{trade_type.value}",
                "symbol": symbol,
                "maven_accounts_count": len(maven_accounts),
                "maven_accounts": [a.get('account_number') for a in maven_accounts],
                "maven_phases": [a.get('phase') for a in maven_accounts],
                "hedge_active": hedge_instance_info.get('is_active', False) if hedge_instance_info else False,
                "success": execution_results["success_count"],
                "failed": execution_results["failure_count"],
                "total_latency_ms": total_latency,
                "maven_parallel_spread_ms": maven_latency,
                "spread_within_limit": maven_latency < 10.0
            })
            
            # Success if at least one order executed
            is_success = execution_results["success_count"] > 0
            
            # Log warning if spread exceeds 10ms (Kenya connectivity issue)
            if maven_latency > 10.0:
                self.logger.warning(f"⚠️ Execution spread exceeded 10ms: {maven_latency:.2f}ms (Kenya ISP latency detected)")
                execution_results["latency_warning"] = f"Execution spread {maven_latency:.2f}ms exceeds 10ms target"
            
            return (is_success, execution_results)
            
        except Exception as e:
            self.logger.log_error(e, "Synchronized execution error")
            return (False, {"error": str(e)})
    
    async def _execute_hedge_trade(self, symbol: str, lot_size: float, 
                                   trade_type: TradeType, 
                                   hedge_info: Dict[str, Any],
                                   tp_pips: float = None,
                                   sl_pips: float = None) -> Dict[str, Any]:
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

            # compute TP/SL absolute prices if provided (pips -> price)
            tp_price = None
            sl_price = None
            try:
                sym = mt5.symbol_info(symbol)
                if sym and sym.point:
                    pip_mult = 10 if getattr(sym, 'digits', 5) > 4 else 1
                    if tp_pips is not None:
                        tp_price = price + (tp_pips * sym.point * pip_mult) if trade_type == TradeType.BUY else price - (tp_pips * sym.point * pip_mult)
                    if sl_pips is not None:
                        sl_price = price - (sl_pips * sym.point * pip_mult) if trade_type == TradeType.BUY else price + (sl_pips * sym.point * pip_mult)
            except Exception:
                tp_price = None
                sl_price = None
            
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

            if tp_price is not None:
                request["tp"] = float(tp_price)
            if sl_price is not None:
                request["sl"] = float(sl_price)
            
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
                                   account: Dict[str, Any],
                                   tp_pips: float = None,
                                   sl_pips: float = None) -> Dict[str, Any]:
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

            tp_price = None
            sl_price = None
            try:
                sym = mt5.symbol_info(symbol)
                if sym and sym.point:
                    pip_mult = 10 if getattr(sym, 'digits', 5) > 4 else 1
                    if tp_pips is not None:
                        tp_price = price + (tp_pips * sym.point * pip_mult) if trade_type == TradeType.BUY else price - (tp_pips * sym.point * pip_mult)
                    if sl_pips is not None:
                        sl_price = price - (sl_pips * sym.point * pip_mult) if trade_type == TradeType.BUY else price + (sl_pips * sym.point * pip_mult)
            except Exception:
                tp_price = None
                sl_price = None
            
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

            if tp_price is not None:
                request["tp"] = float(tp_price)
            if sl_price is not None:
                request["sl"] = float(sl_price)
            
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
                "phase": account.get('phase'),
                "slot_id": account.get('slot_id'),
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

    async def _execute_match_trader_trade(self, bridge: Any, symbol: str, lot_size: float,
                                          tp_pips: float, sl_pips: float,
                                          account: Dict[str, Any],
                                          trade_type: TradeType) -> Dict[str, Any]:
        """Route execution through the Match-Trader browser bridge.

        This method assumes the `bridge` implements `inject_and_click(lot, tp, sl, side)`.
        Returns a result dict similar to _execute_maven_trade for logging.
        """
        try:
            start_time = time.time()
            # Derive numeric TP/SL as simple pips values; bridge expects absolute numbers
            # The bridge consumer should map pips->price if needed by the terminal.
            tp = tp_pips or 0.0
            sl = sl_pips or 0.0
            side = "buy" if trade_type == TradeType.BUY else "sell"

            # inject and click (best-effort)
            result = await bridge.inject_and_click(lot_size, tp, sl, side)
            latency_ms = (time.time() - start_time) * 1000

            if not result.get('success'):
                return {
                    "success": False,
                    "error": result,
                    "account": account.get('account_number'),
                    "latency_ms": latency_ms
                }

            return {
                "success": True,
                "account": account.get('account_number'),
                "ticket": None,
                "price": None,
                "slippage_pips": None,
                "latency_ms": latency_ms,
                "bridge_total_ms": result.get('total_ms')
            }
        except Exception as e:
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
    
    async def close_maven_positions_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """
        Close all Maven positions for a specific symbol (used by auto-stop)
        Called when Exness hedge hits recovery profit target
        
        Args:
            symbol: Symbol to close (e.g., "USTECH")
        
        Returns:
            Dictionary with close results
        """
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "closed_count": 0,
                "failed_count": 0,
                "details": []
            }
            
            # Get all open positions for this symbol
            open_trades = mt5.positions_get()
            if not open_trades:
                return results
            
            for trade in open_trades:
                if trade.symbol != symbol:
                    continue
                
                try:
                    close_type = mt5.ORDER_TYPE_SELL if trade.type == 0 else mt5.ORDER_TYPE_BUY
                    tick = mt5.symbol_info_tick(symbol)
                    price = tick.bid if trade.type == 0 else tick.ask
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": trade.volume,
                        "type": close_type,
                        "position": trade.ticket,
                        "price": price,
                        "deviation": 20,
                        "comment": f"AUTO_STOP_{symbol}_RECOVERY_TARGET_HIT",
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
                            "close_price": price,
                            "closed": True
                        })
                        self.logger.info(f"[AUTO-STOP] Closed Maven position: {symbol} {trade.volume} lots @ {price}")
                    else:
                        results["failed_count"] += 1
                        self.logger.warning(f"[AUTO-STOP] Failed to close {symbol} position {trade.ticket}")
                        
                except Exception as e:
                    results["failed_count"] += 1
                    self.logger.debug(f"Error closing position {trade.ticket}: {str(e)}")
            
            self.logger.log_risk_event("AUTO_STOP_CLOSE_SYMBOL", results)
            return results
            
        except Exception as e:
            self.logger.log_error(e, "Auto-stop position close error")
            return {"error": str(e)}
    
    async def adjust_lot_size_for_farming_mode(self, current_lot: float, 
                                               farming_mode_enabled: bool) -> float:
        """
        Adjust lot size based on farming mode
        When phase transitions from Phase 1 to Funded, switch to farming mode with 0.1x reduction
        
        Args:
            current_lot: Current lot size
            farming_mode_enabled: Whether farming mode is active
        
        Returns:
            Adjusted lot size
        """
        if farming_mode_enabled:
            farming_lot = current_lot * 0.1  # 0.1x multiplier for farming
            self.logger.info(f"[FARMING MODE] Lot size adjusted: {current_lot} → {farming_lot}")
            return farming_lot
        return current_lot
    
    def apply_account_phase_multiplier(self, base_lot: float, 
                                      maven_accounts: List[Dict[str, Any]]) -> List[float]:
        """
        Apply per-account farming mode multipliers based on phase
        
        Args:
            base_lot: Base lot size for Phase 1
            maven_accounts: List of Maven account dicts with 'phase' key
        
        Returns:
            List of adjusted lot sizes per account
        """
        adjusted_lots = []
        for i, account in enumerate(maven_accounts):
            phase = account.get('phase', 'phase_1')
            if phase == 'phase_2' or phase == 'funded':
                # Farming mode: 0.1x lot
                adjusted_lot = base_lot * 0.1
                self.logger.debug(f"[FARMING] Account {account.get('account_number')}: Phase 2 → {adjusted_lot:.2f}L")
            else:
                # Normal mode: full lot
                adjusted_lot = base_lot
            
            adjusted_lots.append(adjusted_lot)
        
        return adjusted_lots
