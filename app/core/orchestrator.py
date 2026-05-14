"""
Marvel Core Orchestrator - Enhanced Edition
Central system coordinator managing all trading components with multi-asset support
Features: Dynamic asset registry, session management, enhanced execution, latency monitoring
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
from app.execution_engine.enhanced_sync_executor import EnhancedSynchronizedExecutionEngine, ParallelExecutionResult
from app.risk_management.safety_monitor import RiskManagementSystem
from app.utils.config import get_config
from app.market_data.asset_registry import AssetRegistry, AssetCategory
from app.session_manager.session_manager import SessionManager, ChallengePhase
from app.monitoring.latency_monitor import LatencyMonitor, ConnectionQuality


class MavelCoreSystem:
    """
    Main trading system orchestrator
    Coordinates MT5 connections, account management, recovery, execution, and risk management
    Features:
    - Multi-asset symbol support (USTECH, NAS100, XAUUSD, US30, GER40)
    - Dynamic symbol selector with pip/margin auto-mapping
    - cTrader DOM automation with parallel execution
    - Session-based account auto-detection
    - Kenya-optimized latency monitoring
    """
    
    def __init__(self):
        self.logger = get_logger()
        self.config = get_config()
        
        # === NEW: Asset Registry ===
        self.asset_registry = AssetRegistry()
        
        # === NEW: Session Manager ===
        self.session_manager: Optional[SessionManager] = None
        
        # === NEW: Enhanced Execution Engine ===
        self.enhanced_execution_engine = EnhancedSynchronizedExecutionEngine()
        
        # === NEW: Latency Monitor (Kenya-optimized) ===
        self.latency_monitor = LatencyMonitor()
        
        # === EXISTING: Initialize all subsystems ===
        self.mt5_manager = MT5ConnectionManager()
        self.market_data = MarketDataProvider()
        self.account_manager = AccountManager()
        self.recovery_engine = HedgeRecoveryEngine()
        self.prop_risk_engine = PropFirmRiskEngine()
        self.execution_engine = SynchronizedExecutionEngine()
        self.risk_manager = RiskManagementSystem()
        
        # Optional cTrader bridge (lazy started by UI or system operator)
        self.ctrader_bridge: Optional[Any] = None
        try:
            from app.browser_bridge.ctrader_bridge import CTraderBridge
            self.ctrader_bridge = CTraderBridge()
        except Exception:
            # Bridge optional; Playwright may not be installed in some environments
            self.ctrader_bridge = None
        
        # State
        self.is_running = False
        self.hedge_enabled = True
        self.auto_recovery_enabled = True
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_recovery_mode = "balanced"
        self.current_symbol: Optional[str] = None

        # Restore saved prop-firm templates from config
        try:
            saved_templates = self.config.get("prop_firm.saved_templates", {})
            if isinstance(saved_templates, dict):
                self.prop_risk_engine.saved_templates = saved_templates
        except Exception:
            pass
        
        # Initialize session manager with bridges
        self._init_session_manager()
        
        self.logger.info("Marvel Core System initialized with multi-asset support")
    
    def _init_session_manager(self) -> None:
        """Initialize session manager with available bridges"""
        self.session_manager = SessionManager(
            browser_bridge=self.ctrader_bridge,
            mt5_manager=self.mt5_manager
        )
    
    # ===== ASSET REGISTRY & SYMBOL SELECTION =====
    
    def get_asset_registry(self) -> AssetRegistry:
        """Get the asset registry for symbol management"""
        return self.asset_registry
    
    def get_primary_symbols(self) -> List[str]:
        """Get list of primary trading symbols (Kenya-optimized)"""
        return self.asset_registry.get_primary_symbols()
    
    def select_symbol(self, symbol: str) -> bool:
        """
        Select active trading symbol
        Auto-maps pip value and margin requirement
        """
        success = self.asset_registry.select_symbol(symbol)
        if success:
            self.current_symbol = symbol
            if self.session_manager:
                self.session_manager.set_selected_symbol(symbol)
            self.logger.info(f"Symbol selected: {symbol}")
        return success
    
    def get_selected_symbol(self) -> Optional[str]:
        """Get currently selected symbol"""
        return self.current_symbol or self.asset_registry.get_selected_symbol()
    
    def get_symbol_profile(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive profile for symbol (pip value, margin, etc.)"""
        return self.asset_registry.get_asset_info_display(symbol)
    
    # ===== SESSION MANAGEMENT =====
    
    async def initialize_ctrader_session(self, account_id: int) -> bool:
        """
        Initialize cTrader session with auto-detection
        - Reads account balance
        - Detects challenge phase
        - Sets up session context
        """
        if not self.session_manager:
            return False
        
        session = self.session_manager.create_session(account_id, platform="ctrader")
        
        # Auto-detect balance
        balance_detected = await self.session_manager.auto_detect_account_balance(session)
        if not balance_detected:
            self.logger.warning(f"Failed to detect balance for account {account_id}")
            return False
        
        # Auto-detect challenge phase
        phase = await self.session_manager.detect_challenge_phase(session)
        self.logger.info(f"Session initialized: {account_id} | Phase: {phase.value} | Balance: ${session.account_balance:.2f}")
        
        return True
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get current session context summary"""
        if not self.session_manager:
            return {"status": "session_manager_unavailable"}
        
        return self.session_manager.get_session_summary()
    
    def validate_symbol_match(self, expected_symbol: str) -> Tuple[bool, str]:
        """
        Validate that selected symbol matches chart symbol
        Returns (is_valid, message)
        """
        if not self.session_manager or not self.ctrader_bridge:
            return (True, "Validation skipped (no bridge)")
        
        selected = self.session_manager.get_selected_symbol()
        if selected and selected != expected_symbol:
            return (False, f"Symbol mismatch: {selected} != {expected_symbol}")
        
        return (True, "Symbol match validated")
    
    # ===== LATENCY MONITORING (Kenya-optimized) =====
    
    async def start_latency_monitoring(self) -> None:
        """Start background latency monitoring"""
        await self.latency_monitor.start_monitoring()
        self.logger.info("Latency monitoring started")
    
    async def stop_latency_monitoring(self) -> None:
        """Stop latency monitoring"""
        await self.latency_monitor.stop_monitoring()
        self.logger.info("Latency monitoring stopped")
    
    def get_latency_stats(self) -> Dict[str, Any]:
        """Get current latency statistics"""
        stats = self.latency_monitor.get_current_stats()
        return {
            server: {
                "avg_latency_ms": stat.avg_latency_ms,
                "min_latency_ms": stat.min_latency_ms,
                "max_latency_ms": stat.max_latency_ms,
                "quality": stat.quality.value,
                "vps_recommended": stat.vps_recommended,
            }
            for server, stat in stats.items()
        }
    
    def should_use_vps_mode(self) -> bool:
        """Check if VPS mode should be recommended (Kenya-optimized)"""
        return self.latency_monitor.should_use_vps_mode()
    
    def get_latency_recommendations(self) -> Dict[str, str]:
        """Get actionable recommendations based on latency"""
        return self.latency_monitor.get_recommendations()
    
    # ===== EXISTING MT5 METHODS =====
    
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
    
    async def execute_buy_order_enhanced(self, 
                                        symbol: str, 
                                        lot_size: float,
                                        use_hedge: bool = True, 
                                        use_maven: bool = True,
                                        tp_pips: float = None, 
                                        sl_pips: float = None) -> ParallelExecutionResult:
        """
        Execute synchronized BUY with symbol validation and parallel dispatch
        
        Features:
        - Symbol matching validation (prevents mismatched trades)
        - Parallel execution (Hedge + Maven + cTrader < 10ms spread)
        - Dynamic asset support (pip value, margin auto-mapping)
        - Session-aware execution
        """
        # Validate symbol selection
        if self.session_manager:
            selected = self.session_manager.get_selected_symbol()
            if selected and selected != symbol:
                result = ParallelExecutionResult(success=False)
                result.symbol_mismatch = True
                result.error_message = f"Symbol mismatch: selected={selected}, requested={symbol}"
                return result
        
            active_accounts = self.account_manager.get_active_accounts() if use_maven else []
        
        # Get hedge info
        hedge_info = None
        if use_hedge and self.hedge_enabled:
            if self.mt5_manager.is_connected(MT5InstanceType.HEDGE_ACCOUNT):
                hedge_info = {
                    "account_id": self.mt5_manager.instances[MT5InstanceType.HEDGE_ACCOUNT].get("account"),
                    "is_active": True,
                }
        
        # Execute with enhanced engine
        result = await self.enhanced_execution_engine.execute_synchronized_trade(
            symbol=symbol,
            lot_size=lot_size,
            trade_type=TradeType.BUY,
            maven_accounts=[
                {
                    "account_id": acc.account_number,
                    "slot_id": acc.slot_id,
                    "phase": acc.phase.value
                }
                for acc in active_accounts
            ],
            hedge_instance_info=hedge_info,
            tp_pips=tp_pips,
            sl_pips=sl_pips,
            match_trader_bridge=self.ctrader_bridge,
            session_manager=self.session_manager,
        )
        
        return result
    
    async def execute_sell_order_enhanced(self,
                                         symbol: str,
                                         lot_size: float,
                                         use_hedge: bool = True,
                                         use_maven: bool = True,
                                         tp_pips: float = None,
                                         sl_pips: float = None) -> ParallelExecutionResult:
        """Execute synchronized SELL with symbol validation and parallel dispatch"""
        # Validate symbol selection
        if self.session_manager:
            selected = self.session_manager.get_selected_symbol()
            if selected and selected != symbol:
                result = ParallelExecutionResult(success=False)
                result.symbol_mismatch = True
                result.error_message = f"Symbol mismatch: selected={selected}, requested={symbol}"
                return result
        
            active_accounts = self.account_manager.get_active_accounts() if use_maven else []
        
        # Get hedge info
        hedge_info = None
        if use_hedge and self.hedge_enabled:
            if self.mt5_manager.is_connected(MT5InstanceType.HEDGE_ACCOUNT):
                hedge_info = {
                    "account_id": self.mt5_manager.instances[MT5InstanceType.HEDGE_ACCOUNT].get("account"),
                    "is_active": True,
                }
        
        # Execute with enhanced engine
        result = await self.enhanced_execution_engine.execute_synchronized_trade(
            symbol=symbol,
            lot_size=lot_size,
            trade_type=TradeType.SELL,
            maven_accounts=[
                {
                    "account_id": acc.account_number,
                    "slot_id": acc.slot_id,
                    "phase": acc.phase.value
                }
                for acc in active_accounts
            ],
            hedge_instance_info=hedge_info,
            tp_pips=tp_pips,
            sl_pips=sl_pips,
            match_trader_bridge=self.ctrader_bridge,
            session_manager=self.session_manager,
        )
        
        return result
    
    
    async def _execute_order(self, symbol: str, lot_size: float, 
                            trade_type: TradeType, use_hedge: bool, use_maven: bool,
                            tp_pips: float = None, sl_pips: float = None,
                            selected_slot_id: Optional[int] = None,
                            selected_phase: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Internal order execution with validation"""
        try:
            # Pre-execution validation
            active_accounts = self.account_manager.get_active_accounts() if use_maven else []
            if not active_accounts and not (use_hedge and self.hedge_enabled):
                return (False, {"error": "No active accounts selected and hedge disabled"})

            slot_id = selected_slot_id or self.account_manager.selected_account_slot or (active_accounts[0].slot_id if active_accounts else 1)
            phase_enum = self.resolve_phase_for_slot(slot_id, selected_phase)
            active_phase = phase_enum.value
            
            # Validate spread
            if not self.risk_manager.validate_spread(symbol):
                return (False, {"error": "Spread too wide"})
            
            # Build execution parameters
            hedge_info = None
            hedge_lot_override = None
            if use_hedge and self.hedge_enabled:
                if self.mt5_manager.is_connected(MT5InstanceType.HEDGE_ACCOUNT):
                    # If auto-recovery enabled, compute phase-aware hedge lot and target
                    if self.auto_recovery_enabled:
                        try:
                            plan = self.calculate_dynamic_hedge_plan(
                                {
                                    "symbol": symbol,
                                    "stop_loss_pips": float(sl_pips) if sl_pips is not None else 20.0,
                                    "take_profit_pips": float(tp_pips) if tp_pips is not None else 10.0,
                                    "desired_surplus": 0.0,
                                    "risk_per_trade_pct": 0.5,
                                    "recovery_mode": self.current_recovery_mode,
                                    "phase": active_phase,
                                    "selected_slot_id": slot_id,
                                    "profit_target_pct": self.account_manager.get_phase_profit_target_pct(phase_enum),
                                    "account_size": float(self.prop_risk_engine.current_config.account_size),
                                    "purchase_fee": float(self.prop_risk_engine.current_config.purchase_fee),
                                    "daily_drawdown_pct": float(self.prop_risk_engine.current_config.daily_drawdown_pct),
                                    "overall_drawdown_pct": float(self.prop_risk_engine.current_config.overall_drawdown_pct),
                                    "max_lots_allowed": float(self.prop_risk_engine.current_config.max_lots_allowed),
                                    "profit_split_pct": float(self.prop_risk_engine.current_config.profit_split_pct),
                                }
                            )
                            hedge_lot_override = float(plan.get("hedge_lot_size", 0.0))
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
                    "slot_id": acc.slot_id,
                    "phase": acc.phase.value
                }
                for acc in active_accounts
            ]

            self.logger.log_trade(
                {
                    "action": "phase_aware_dispatch",
                    "symbol": symbol,
                    "direction": trade_type.value,
                    "selected_slot": slot_id,
                    "active_phase": active_phase,
                    "lot_size": lot_size,
                    "hedge_lot": hedge_lot_override,
                    "maven_slots": [a.get("slot_id") for a in maven_accounts],
                    "maven_phases": [a.get("phase") for a in maven_accounts],
                }
            )
            
            # Execute synchronized trade
            success, results = await self.execution_engine.execute_synchronized_trade(
                symbol=symbol,
                lot_size=lot_size,
                trade_type=trade_type,
                maven_accounts=maven_accounts,
                hedge_instance_info=hedge_info,
                tp_pips=tp_pips,
                sl_pips=sl_pips,
                hedge_lot=hedge_lot_override,
                match_trader_bridge=self.ctrader_bridge
            )

            if isinstance(results, dict):
                results["active_phase"] = active_phase
                results["selected_slot"] = slot_id
            
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

    def start_ctrader_bridge(self, url: str, headless: bool = True) -> Dict[str, Any]:
        """Start the cTrader browser bridge synchronously.

        This is a convenience wrapper callable from the UI.
        """
        if not self.ctrader_bridge:
            return {"success": False, "error": "bridge_unavailable"}
        try:
            # Use asyncio.run to start the async bridge
            return asyncio.run(self.ctrader_bridge.start(url=url, headless=headless))
        except Exception as e:
            return {"success": False, "error": str(e)}

    def login_maven_via_ctrader_browser(self, account: int, password: str, server: str, url: str = None, headless: bool = True) -> Dict[str, Any]:
        """Start the cTrader bridge and inject Maven login credentials via browser automation."""
        if not self.ctrader_bridge:
            return {"success": False, "error": "bridge_unavailable"}
        try:
            target = url or self.config.get("ctrader.maven_url", "https://app.ctrader.com")

            # Start browser and navigate
            start_res = asyncio.run(self.ctrader_bridge.start(url=target, headless=headless))
            if not start_res.get("success"):
                return {"success": False, "error": "bridge_start_failed", "detail": start_res}

            # Inject credentials and attempt login
            inject_res = asyncio.run(self.ctrader_bridge.inject_login_credentials(str(account), password, server))
            if not inject_res.get("success"):
                return {"success": False, "error": "login_inject_failed", "detail": inject_res}

            # Initialize session (auto-detect balance and phase)
            initialized = asyncio.run(self.initialize_ctrader_session(account))
            return {"success": bool(initialized), "initialized": initialized, "inject_detail": inject_res}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def calculate_dynamic_hedge_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate funded + hedge lot sizes and risk projections."""
        symbol = str(payload.get("symbol", "US100")).strip().upper()
        stop_loss = float(payload.get("stop_loss_pips", 20.0))
        take_profit = float(payload.get("take_profit_pips", 10.0))
        selected_slot = int(payload.get("selected_slot_id", self.account_manager.selected_account_slot or 1))
        phase_enum = self.resolve_phase_for_slot(selected_slot, payload.get("phase"))
        phase_profit_target = self.account_manager.get_phase_profit_target_pct(phase_enum)
        phase_default_surplus = self.account_manager.get_phase_recovery_surplus(phase_enum)
        desired_surplus = float(payload.get("desired_surplus", phase_default_surplus))
        if desired_surplus <= 0:
            desired_surplus = phase_default_surplus
        risk_per_trade = float(payload.get("risk_per_trade_pct", 0.5))

        config = PropFirmChallengeConfig(
            account_size=float(payload.get("account_size", self.prop_risk_engine.current_config.account_size)),
            purchase_fee=float(payload.get("purchase_fee", self.prop_risk_engine.current_config.purchase_fee)),
            profit_target_pct=float(payload.get("profit_target_pct", phase_profit_target)),
            daily_drawdown_pct=float(payload.get("daily_drawdown_pct", self.prop_risk_engine.current_config.daily_drawdown_pct)),
            overall_drawdown_pct=float(payload.get("overall_drawdown_pct", self.prop_risk_engine.current_config.overall_drawdown_pct)),
            max_lots_allowed=float(payload.get("max_lots_allowed", self.prop_risk_engine.current_config.max_lots_allowed)),
            profit_split_pct=float(payload.get("profit_split_pct", self.prop_risk_engine.current_config.profit_split_pct)),
            leverage=float(payload.get("leverage", self.prop_risk_engine.current_config.leverage)),
        )

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
            config=config,
        )
        out = result.to_dict()

        # Phase 2 requires less target distance; reduce hedge exposure time accordingly.
        if phase_enum == TradingPhase.PHASE_2:
            out["hedge_lot_size"] = round(max(0.01, float(out.get("hedge_lot_size", 0.0)) * 0.90), 2)

        out["phase"] = phase_enum.value
        out["selected_slot"] = selected_slot
        out["phase_profit_target_pct"] = phase_profit_target
        out["phase_recovery_surplus"] = desired_surplus
        return out

    def resolve_phase_for_slot(self, slot_id: int, phase_text: Optional[str] = None) -> TradingPhase:
        """Resolve effective phase from optional UI override or persisted slot state."""
        if phase_text:
            normalized = str(phase_text).strip().lower()
            if normalized == "phase 2":
                return TradingPhase.PHASE_2
            if normalized == "phase 1":
                return TradingPhase.PHASE_1
        return self.account_manager.get_account_phase(slot_id)

    def pre_trade_phase_check(self, slot_id: int, selected_phase: Optional[str]) -> Dict[str, Any]:
        """Check whether live balance suggests a phase transition not reflected in UI."""
        phase_enum = self.resolve_phase_for_slot(slot_id, selected_phase)
        acct = self.mt5_manager.get_account_info(MT5InstanceType.MAVEN_FLEET) or {}
        balance = float(acct.get("balance", 0.0) or 0.0)
        base_size = float(self.prop_risk_engine.current_config.account_size)
        gain_pct = ((balance - base_size) / max(base_size, 1.0)) * 100.0 if balance > 0 else 0.0

        warning = False
        reason = ""
        if phase_enum == TradingPhase.PHASE_1 and gain_pct >= 8.0:
            warning = True
            reason = (
                f"Slot {slot_id} balance indicates >=8% progress ({gain_pct:.2f}%). "
                "Consider switching to Phase 2 before placing this trade."
            )

        return {
            "slot_id": slot_id,
            "selected_phase": phase_enum.value,
            "balance": balance,
            "gain_pct": round(gain_pct, 2),
            "warning": warning,
            "message": reason,
        }

    def set_slot_phase(self, slot_id: int, phase_text: str) -> Dict[str, Any]:
        """Persist slot phase and return phase-aware hedge refresh values."""
        self.account_manager.select_account(slot_id)
        updated = self.account_manager.set_account_phase_by_text(slot_id, phase_text)
        phase_enum = self.resolve_phase_for_slot(slot_id, phase_text)
        plan = self.calculate_dynamic_hedge_plan(
            {
                "selected_slot_id": slot_id,
                "phase": phase_enum.value,
                "symbol": "US100",
                "stop_loss_pips": 20.0,
                "take_profit_pips": 10.0,
                "risk_per_trade_pct": 0.5,
                "recovery_mode": self.current_recovery_mode,
                "desired_surplus": self.account_manager.get_phase_recovery_surplus(phase_enum),
            }
        )
        return {
            "updated": updated,
            "slot_id": slot_id,
            "phase": phase_enum.value,
            "profit_target_pct": self.account_manager.get_phase_profit_target_pct(phase_enum),
            "hedge_lot_size": plan.get("hedge_lot_size", 0.0),
            "recovery_target": plan.get("recovery_target", 0.0),
        }

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
    
    async def check_and_trigger_auto_stop(self, 
                                         symbol: str = "USTECH",
                                         recovery_target: float = 110.0) -> Dict[str, Any]:
        """
        Check if Exness hedge account has reached recovery profit target.
        If target is hit, automatically close all corresponding Maven positions.
        
        This is the AUTO-STOP mechanism for the Mirror Protocol:
        - When hedge side hits recovery target (covers fee + surplus + drawdown)
        - Immediately close all Maven positions for that symbol
        - "Lock in" the profitable cycle
        
        Args:
            symbol: Trading symbol to check/close (default: USTECH)
            recovery_target: Profit target for hedge to trigger auto-stop (default: $110)
        
        Returns:
            Dictionary with auto-stop status and results
        """
        try:
            result = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "recovery_target": recovery_target,
                "auto_stop_triggered": False,
                "hedge_profit": None,
                "maven_positions_closed": 0,
                "details": None
            }
            
            # Get hedge account info
            hedge_status = self.mt5_manager.get_status(MT5InstanceType.HEDGE_ACCOUNT)
            if not hedge_status.get("is_connected"):
                result["details"] = "Hedge account not connected"
                self.logger.warning("[AUTO-STOP] Hedge account not connected")
                return result
            
            # Import MT5 to get positions
            import MetaTrader5 as mt5
            
            # Get hedge account's positions for the symbol
            hedge_positions = mt5.positions_get(symbol=symbol)
            if not hedge_positions:
                result["details"] = f"No hedge positions found for {symbol}"
                return result
            
            # Calculate total hedge P/L for the symbol
            total_hedge_profit = 0.0
            for position in hedge_positions:
                total_hedge_profit += position.profit
            
            result["hedge_profit"] = round(total_hedge_profit, 2)
            
            # Check if recovery target is hit
            if total_hedge_profit >= recovery_target:
                result["auto_stop_triggered"] = True
                self.logger.info(f"[AUTO-STOP] Recovery target HIT! Hedge profit: ${total_hedge_profit:.2f} >= ${recovery_target:.2f}")
                
                # Close all Maven positions for this symbol
                close_results = await self.execution_engine.close_maven_positions_by_symbol(symbol)
                result["maven_positions_closed"] = close_results.get("closed_count", 0)
                result["details"] = f"Auto-stop triggered: Closed {close_results.get('closed_count', 0)} Maven positions"
                
                # Log the event
                self.logger.log_risk_event("AUTO_STOP_TRIGGERED", {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol,
                    "hedge_profit": total_hedge_profit,
                    "recovery_target": recovery_target,
                    "maven_closed": close_results.get("closed_count", 0)
                })
            else:
                result["details"] = f"Target not reached: ${total_hedge_profit:.2f} < ${recovery_target:.2f}"
                self.logger.debug(f"[AUTO-STOP] Target check: ${total_hedge_profit:.2f} < ${recovery_target:.2f}")
            
            return result
            
        except Exception as e:
            self.logger.log_error(e, "Auto-stop check error")
            return {
                "error": str(e),
                "auto_stop_triggered": False
            }
    
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
