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
from app.recovery_engine.prop_risk_engine import (
    PropFirmRiskEngine,
    PropFirmChallengeConfig,
)
from app.execution_engine.sync_executor import SynchronizedExecutionEngine, TradeType
from app.risk_management.safety_monitor import RiskManagementSystem
from app.utils.config import get_config


class MavelCoreSystem:
    """
    Main trading system orchestrator
    Coordinates MT5 connections, account management, recovery, execution, and risk management
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.config = get_config()
        
        # Initialize all subsystems
        self.mt5_manager = MT5ConnectionManager()
        self.market_data = MarketDataProvider()
        self.account_manager = AccountManager()
        self.recovery_engine = HedgeRecoveryEngine()
        self.prop_risk_engine = PropFirmRiskEngine()
        self.execution_engine = SynchronizedExecutionEngine()
        self.risk_manager = RiskManagementSystem()
        
        # State
        self.is_running = False
        self.hedge_enabled = True
        self.auto_recovery_enabled = True
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_recovery_mode = "balanced"

        # Restore saved prop-firm templates from config
        try:
            saved_templates = self.config.get("prop_firm.saved_templates", {})
            if isinstance(saved_templates, dict):
                self.prop_risk_engine.saved_templates = saved_templates
        except Exception:
            pass
        
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
                               use_hedge: bool = True, use_maven: bool = True,
                               tp_pips: float = None, sl_pips: float = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Execute synchronized BUY across active Maven accounts and hedge
        
        Args:
            symbol: Trading symbol
            lot_size: Lot size per account
            use_hedge: Whether to include hedge execution
        
        Returns:
            Tuple of (success, execution_results)
        """
        return await self._execute_order(symbol, lot_size, TradeType.BUY, use_hedge, use_maven, tp_pips=tp_pips, sl_pips=sl_pips)
    
    async def execute_sell_order(self, symbol: str, lot_size: float,
                                use_hedge: bool = True, use_maven: bool = True,
                                tp_pips: float = None, sl_pips: float = None) -> Tuple[bool, Dict[str, Any]]:
        """Execute synchronized SELL across active Maven accounts and hedge"""
        return await self._execute_order(symbol, lot_size, TradeType.SELL, use_hedge, use_maven, tp_pips=tp_pips, sl_pips=sl_pips)
    
    async def _execute_order(self, symbol: str, lot_size: float, 
                            trade_type: TradeType, use_hedge: bool, use_maven: bool,
                            tp_pips: float = None, sl_pips: float = None) -> Tuple[bool, Dict[str, Any]]:
        """Internal order execution with validation"""
        try:
            # Pre-execution validation
            active_accounts = self.account_manager.get_active_accounts() if use_maven else []
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

        if not fees:
            fees.append(float(self.prop_risk_engine.current_config.purchase_fee))
        
        return self.recovery_engine.estimate_next_recovery_lot(
            [{"challenge_fee": f} for f in fees]
        )

    def get_latest_hedge_loss(self) -> Optional[float]:
        """Get the latest recorded hedge loss for dashboard auto-fill."""
        return self.recovery_engine.get_latest_recorded_hedge_loss()

    def get_latest_hedge_trade_pnl(self) -> Optional[float]:
        """Get the latest realized hedge trade P/L as a signed value."""
        return self.recovery_engine.get_latest_hedge_trade_pnl()

    def get_latest_hedge_trade_context(self) -> Optional[Dict[str, Any]]:
        """Get the latest hedge trade context for auto-recording and UI hints."""
        return self.recovery_engine.get_latest_hedge_trade_context()

    def auto_record_latest_hedge_loss(self) -> Dict[str, Any]:
        """Automatically record the latest hedge loss if it is realized and not yet logged."""
        context = self.get_latest_hedge_trade_context()
        if not context:
            return {"recorded": False, "reason": "no_hedge_trade_found"}

        ticket = context.get("ticket")
        account_number = context.get("account") or 0
        symbol = context.get("symbol")
        realized_pnl = context.get("realized_pnl")

        if ticket is None or account_number in (None, 0) or realized_pnl is None:
            return {"recorded": False, "reason": "incomplete_trade_context", "context": context}

        if float(realized_pnl) >= 0:
            return {"recorded": False, "reason": "non_negative_pnl", "context": context}

        if self.recovery_engine.has_recorded_trade_ticket(int(ticket)):
            return {"recorded": False, "reason": "already_recorded", "ticket": int(ticket)}

        cycle_id = f"HEDGE_TICKET_{int(ticket)}"
        hedge_loss = abs(float(realized_pnl))
        fee = float(self.prop_risk_engine.current_config.purchase_fee)
        recorded = self.record_hedge_loss(
            cycle_id=cycle_id,
            account_number=int(account_number),
            hedge_loss=hedge_loss,
            fee=fee,
            source="auto",
        )
        if recorded:
            self.logger.info(
                f"Auto-recorded hedge loss from ticket {ticket} on {symbol}: ${hedge_loss:.2f}"
            )
            return {"recorded": True, "ticket": int(ticket), "account_number": int(account_number), "hedge_loss": hedge_loss, "symbol": symbol}

        return {"recorded": False, "reason": "record_failed", "ticket": int(ticket), "account_number": int(account_number)}

    def configure_prop_challenge(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Set challenge configuration and return derived dollar limits."""
        config = PropFirmChallengeConfig(
            account_size=float(payload.get("account_size", 5000.0)),
            purchase_fee=float(payload.get("purchase_fee", 59.0)),
            profit_target_pct=float(payload.get("profit_target_pct", 8.0)),
            daily_drawdown_pct=float(payload.get("daily_drawdown_pct", 5.0)),
            overall_drawdown_pct=float(payload.get("overall_drawdown_pct", 10.0)),
            max_lots_allowed=float(payload.get("max_lots_allowed", 5.0)),
            profit_split_pct=float(payload.get("profit_split_pct", 80.0)),
            leverage=float(payload.get("leverage", 100.0)),
        )
        self.prop_risk_engine.set_challenge_config(config)

        mode = str(payload.get("recovery_mode", "balanced")).strip().lower()
        self.current_recovery_mode = mode if mode else "balanced"

        return self.prop_risk_engine.get_challenge_summary(config)

    def save_challenge_template(self, template_name: str) -> bool:
        """Persist in-memory challenge template in the quant engine."""
        if not template_name or not template_name.strip():
            return False
        self.prop_risk_engine.save_template(template_name.strip())
        self.config.set("prop_firm.saved_templates", self.prop_risk_engine.saved_templates)
        return True

    def calculate_dynamic_hedge_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate funded + hedge lot sizes and risk projections."""
        symbol = str(payload.get("symbol", "US100")).strip().upper()
        stop_loss = float(payload.get("stop_loss_pips", 20.0))
        take_profit = float(payload.get("take_profit_pips", 10.0))
        desired_surplus = float(payload.get("desired_surplus", 100.0))
        risk_per_trade = float(payload.get("risk_per_trade_pct", 0.5))

        active_fees = [
            float(acc.get("challenge_fee", 0.0))
            for acc in payload.get("active_accounts", [])
            if isinstance(acc, dict)
        ]
        recovery_deficit = float(payload.get("recovery_deficit", 0.0))
        if recovery_deficit <= 0:
            recovery_deficit = self.recovery_engine.calculate_recovery_target(
                active_fees=active_fees,
                desired_surplus=0.0,
            )

        mode = str(payload.get("recovery_mode", self.current_recovery_mode)).strip().lower()
        result = self.prop_risk_engine.compute_dynamic_hedge(
            symbol=symbol,
            stop_loss_pips=stop_loss,
            take_profit_pips=take_profit,
            recovery_deficit=recovery_deficit,
            desired_surplus=desired_surplus,
            risk_per_trade_pct=risk_per_trade,
            recovery_mode=mode,
        )
        return result.to_dict()

    def get_drawdown_guardrail(self, account: int) -> Dict[str, Any]:
        """Return drawdown usage and whether auto-protection should engage."""
        metrics = self.risk_manager.get_current_metrics(account)
        if not metrics:
            return {
                "is_available": False,
                "protection_triggered": False,
                "drawdown_usage_pct": 0.0,
            }

        max_daily = max(self.risk_manager.max_daily_drawdown, 1.0)
        usage_pct = max(0.0, min((metrics.daily_drawdown_used / max_daily) * 100.0, 999.0))
        return {
            "is_available": True,
            "protection_triggered": usage_pct >= 90.0,
            "drawdown_usage_pct": round(usage_pct, 2),
            "daily_drawdown_used": round(metrics.daily_drawdown_used, 2),
            "max_daily_drawdown": round(max_daily, 2),
        }
    
    def record_hedge_loss(self, cycle_id: str, account_number: int, 
                         hedge_loss: float, fee: float = 0.0, source: str = "manual") -> bool:
        """Record hedge loss for future recovery"""
        return self.recovery_engine.record_hedge_loss(
            cycle_id=cycle_id,
            account_number=account_number,
            hedge_loss=hedge_loss,
            challenge_fee=fee
            ,source=source
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
