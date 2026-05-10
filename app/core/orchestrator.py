"""
Marvel Core Orchestrator
Central system coordinator that manages all trading components
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from app.utils.logger import get_logger
from app.mt5_bridge.connection_manager import MT5ConnectionManager, MT5InstanceType
from app.mt5_bridge.market_data import MarketDataProvider
from app.account_manager.fleet_manager import AccountManager, TradingPhase
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
from app.execution_engine.sync_executor import SynchronizedExecutionEngine, TradeType
from app.risk_management.safety_monitor import RiskManagementSystem


class MavelCoreSystem:
    """
    Main trading system orchestrator
    Coordinates MT5 connections, account management, recovery, execution, and risk management
    """
    
    def __init__(self):
        self.logger = get_logger()
        
        # Initialize all subsystems
        self.mt5_manager = MT5ConnectionManager()
        self.market_data = MarketDataProvider()
        self.account_manager = AccountManager()
        self.recovery_engine = HedgeRecoveryEngine()
        self.execution_engine = SynchronizedExecutionEngine()
        self.risk_manager = RiskManagementSystem()
        
        # State
        self.is_running = False
        self.hedge_enabled = True
        self.auto_recovery_enabled = True
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.logger.info("Marvel Core System initialized")
    
    def initialize_maven_instance(self, maven_terminal_path: str) -> bool:
        """Initialize Maven fleet MT5 instance"""
        return self.mt5_manager.initialize(MT5InstanceType.MAVEN_FLEET, maven_terminal_path)
    
    def initialize_hedge_instance(self, hedge_terminal_path: str) -> bool:
        """Initialize personal hedge MT5 instance"""
        return self.mt5_manager.initialize(MT5InstanceType.HEDGE_ACCOUNT, hedge_terminal_path)
    
    def login_maven_account(self, account: int, password: str, server: str) -> bool:
        """Login to Maven account"""
        return self.mt5_manager.login(MT5InstanceType.MAVEN_FLEET, account, password, server)
    
    def login_hedge_account(self, account: int, password: str, server: str) -> bool:
        """Login to hedge account"""
        return self.mt5_manager.login(MT5InstanceType.HEDGE_ACCOUNT, account, password, server)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "session_id": self.session_id,
            "is_running": self.is_running,
            "timestamp": datetime.now().isoformat(),
            "mt5_instances": {
                "maven_fleet": self.mt5_manager.get_status(MT5InstanceType.MAVEN_FLEET),
                "hedge_account": self.mt5_manager.get_status(MT5InstanceType.HEDGE_ACCOUNT)
            },
            "features": {
                "hedge_enabled": self.hedge_enabled,
                "auto_recovery_enabled": self.auto_recovery_enabled
            },
            "accounts": {
                "total_configured": len([a for a in self.account_manager.accounts.values() if a]),
                "active": len(self.account_manager.get_active_accounts()),
                "phase_1": len(self.account_manager.get_accounts_by_phase(TradingPhase.PHASE_1)),
                "phase_2": len(self.account_manager.get_accounts_by_phase(TradingPhase.PHASE_2))
            }
        }
    
    def get_market_data(self, symbol: str = "US100") -> Optional[Dict[str, Any]]:
        """Get live market data for symbol"""
        return self.market_data.get_live_tick(symbol)
    
    def get_account_health(self, account: int) -> Dict[str, Any]:
        """Get account health and risk status"""
        return self.risk_manager.get_status(account)
    
    async def execute_buy_order(self, symbol: str, lot_size: float, 
                               use_hedge: bool = True, tp_pips: float = None, sl_pips: float = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute synchronized BUY across active Maven accounts and hedge
        
        Args:
            symbol: Trading symbol
            lot_size: Lot size per account
            use_hedge: Whether to include hedge execution
        
        Returns:
            Tuple of (success, execution_results)
        """
        return await self._execute_order(symbol, lot_size, TradeType.BUY, use_hedge)
    
    async def execute_sell_order(self, symbol: str, lot_size: float,
                                use_hedge: bool = True, tp_pips: float = None, sl_pips: float = None) -> Tuple[bool, Dict[str, Any]]:
        """Execute synchronized SELL across active Maven accounts and hedge"""
        return await self._execute_order(symbol, lot_size, TradeType.SELL, use_hedge, tp_pips=tp_pips, sl_pips=sl_pips)
    
    async def _execute_order(self, symbol: str, lot_size: float, 
                            trade_type: TradeType, use_hedge: bool, tp_pips: float = None, sl_pips: float = None) -> Tuple[bool, Dict[str, Any]]:
        """Internal order execution with validation"""
        try:
            # Pre-execution validation
            active_accounts = self.account_manager.get_active_accounts()
            if not active_accounts and not (use_hedge and self.hedge_enabled):
                return (False, {"error": "No active accounts selected and hedge disabled"})
            
            # Validate spread
            if not self.risk_manager.validate_spread(symbol):
                return (False, {"error": "Spread too wide"})
            
            # Build execution parameters
            hedge_info = None
            hedge_lot_override = None
            if use_hedge and self.hedge_enabled:
                if self.mt5_manager.is_connected(MT5InstanceType.HEDGE_ACCOUNT):
                    # If auto-recovery enabled, compute suggested hedge lot and target
                    if self.auto_recovery_enabled:
                        try:
                            est_lot, est_target = self.get_recovery_target()
                            hedge_lot_override = float(est_lot)
                        except Exception:
                            hedge_lot_override = None

                    hedge_info = {
                        "account": self.mt5_manager.instances[MT5InstanceType.HEDGE_ACCOUNT]["account"],
                        "is_active": True,
                        "lot_override": hedge_lot_override
                    }
            
            maven_accounts = [
                {
                    "account_number": acc.account_number,
                    "phase": acc.phase.value
                }
                for acc in active_accounts
            ]
            
            # Execute synchronized trade
            success, results = await self.execution_engine.execute_synchronized_trade(
                symbol=symbol,
                lot_size=lot_size,
                trade_type=trade_type,
                maven_accounts=maven_accounts,
                hedge_instance_info=hedge_info,
                tp_pips=tp_pips,
                sl_pips=sl_pips,
                hedge_lot=hedge_lot_override
            )
            
            return (success, results)
            
        except Exception as e:
            self.logger.log_error(e, "Order execution error")
            return (False, {"error": str(e)})
    
    async def close_all_emergency(self) -> Dict[str, Any]:
        """Emergency: Close all positions and stop trading"""
        try:
            results = await self.execution_engine.close_all_positions()
            self.is_running = False
            
            self.logger.log_risk_event("EMERGENCY_CLOSE", {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "closed_positions": results.get("closed_count", 0)
            })
            
            return results
        except Exception as e:
            self.logger.log_error(e, "Emergency close error")
            return {"error": str(e)}
    
    def add_maven_account(self, slot_id: int, account_number: int, password: str,
                         server: str, phase: TradingPhase) -> bool:
        """Register Maven account"""
        return self.account_manager.add_account(
            slot_id=slot_id,
            account_number=account_number,
            password=password,
            server=server,
            phase=phase
        )
    
    def set_account_active(self, slot_id: int, active: bool) -> bool:
        """Toggle account active for next trade"""
        return self.account_manager.set_account_active(slot_id, active)
    
    def get_recovery_target(self, account_ids: Optional[List[int]] = None) -> Tuple[float, float]:
        """Get current recovery target and estimated hedge lot"""
        active_accounts = self.account_manager.get_active_accounts()
        
        # Use actual challenge fees if available
        fees = []
        for acc in active_accounts:
            # In real system, fetch from Maven API
            fees.append(0.0)  # Placeholder
        
        return self.recovery_engine.estimate_next_recovery_lot(
            [{"challenge_fee": f} for f in fees]
        )
    
    def record_hedge_loss(self, cycle_id: str, account_number: int, 
                         hedge_loss: float, fee: float = 0.0) -> bool:
        """Record hedge loss for future recovery"""
        return self.recovery_engine.record_hedge_loss(
            cycle_id=cycle_id,
            account_number=account_number,
            hedge_loss=hedge_loss,
            challenge_fee=fee
        )
    
    def record_recovery_execution(self, cycle_id: str, account_number: int,
                                 hedge_lot: float, target: float, 
                                 profit: float) -> bool:
        """Record recovery execution result"""
        return self.recovery_engine.record_recovery_execution(
            cycle_id=cycle_id,
            account_number=account_number,
            hedge_lot_executed=hedge_lot,
            target_amount=target,
            profit_achieved=profit
        )
    
    def shutdown(self) -> None:
        """Shutdown system and disconnect all MT5 instances"""
        try:
            self.is_running = False
            self.mt5_manager.shutdown_all()
            self.logger.info("Marvel Core System shutdown complete")
        except Exception as e:
            self.logger.log_error(e, "Shutdown error")


# Global system instance
_system_instance = None


def get_system() -> MavelCoreSystem:
    """Get or create global system instance"""
    global _system_instance
    if _system_instance is None:
        _system_instance = MavelCoreSystem()
    return _system_instance
