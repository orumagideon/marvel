"""
UI Components for Marvel Dashboard
Reusable widgets for market data, health, status, controls, and account grid
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime


class MarketFeedWidget(ctk.CTkFrame):
    """Real-time market data display"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#1a1a1a", **kwargs)
        
        # Symbol ticker
        self.symbol_label = ctk.CTkLabel(
            self,
            text="US100/USD",
            font=("Arial", 20, "bold"),
            text_color="#00ff88"
        )
        self.symbol_label.pack(pady=10)
        
        # Price display
        price_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        price_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(price_frame, text="Bid:", font=("Arial", 11), text_color="#888").pack(side="left")
        self.bid_label = ctk.CTkLabel(price_frame, text="---", font=("Arial", 11, "bold"), text_color="#00ff88")
        self.bid_label.pack(side="left", padx=5)
        
        ctk.CTkLabel(price_frame, text="Ask:", font=("Arial", 11), text_color="#888").pack(side="left", padx=(20, 0))
        self.ask_label = ctk.CTkLabel(price_frame, text="---", font=("Arial", 11, "bold"), text_color="#00ff88")
        self.ask_label.pack(side="left", padx=5)
        
        # Spread
        spread_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        spread_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(spread_frame, text="Spread:", font=("Arial", 10), text_color="#888").pack(side="left")
        self.spread_label = ctk.CTkLabel(spread_frame, text="--- pips", font=("Arial", 10), text_color="#ffaa00")
        self.spread_label.pack(side="left", padx=5)
    
    def update_data(self, data: Dict[str, Any]) -> None:
        """Update market data display"""
        if data:
            self.bid_label.configure(text=f"{data.get('bid', 0):.4f}")
            self.ask_label.configure(text=f"{data.get('ask', 0):.4f}")
            self.spread_label.configure(text=f"{data.get('spread_pips', 0):.2f} pips")

    def set_symbol(self, symbol: str) -> None:
        """Update the displayed symbol label."""
        display_symbol = symbol.strip().upper() or "US100"
        self.symbol_label.configure(text=display_symbol)


class AccountHealthWidget(ctk.CTkFrame):
    """Account health and risk visualization"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="#1a1a1a", **kwargs)
        
        # Drawdown gauge
        gauge_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        gauge_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(gauge_frame, text="Daily Drawdown:", font=("Arial", 11), text_color="#888").pack(side="left")
        
        self.gauge = ctk.CTkProgressBar(gauge_frame, fg_color="#2a2a2a", progress_color="#ff0000")
        self.gauge.pack(side="left", fill="x", expand=True, padx=10)
        self.gauge.set(0)
        
        self.drawdown_label = ctk.CTkLabel(gauge_frame, text="0%", font=("Arial", 11), text_color="#00ff88")
        self.drawdown_label.pack(side="left")
        
        # Equity display
        equity_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        equity_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(equity_frame, text="Equity:", font=("Arial", 10), text_color="#888").pack(side="left")
        self.equity_label = ctk.CTkLabel(equity_frame, text="$---", font=("Arial", 10, "bold"), text_color="#00ff88")
        self.equity_label.pack(side="left", padx=20)
        
        ctk.CTkLabel(equity_frame, text="Margin Level:", font=("Arial", 10), text_color="#888").pack(side="left")
        self.margin_label = ctk.CTkLabel(equity_frame, text="---", font=("Arial", 10, "bold"), text_color="#00ff88")
        self.margin_label.pack(side="left", padx=20)
    
    def update_health(self, health_data: Dict[str, Any]) -> None:
        """Update health display"""
        if health_data:
            drawdown_pct = health_data.get('drawdown_percentage', 0)
            self.gauge.set(min(drawdown_pct / 100, 1.0))
            self.drawdown_label.configure(text=f"{drawdown_pct:.1f}%")
            
            # Update colors based on criticality
            if health_data.get('is_critical'):
                color = "#ff0000"
            elif drawdown_pct > 50:
                color = "#ffaa00"
            else:
                color = "#00ff88"
            
            self.drawdown_label.configure(text_color=color)
            self.gauge.configure(progress_color=color)
            
            self.equity_label.configure(text=f"${health_data.get('equity', 0):.2f}")
            self.margin_label.configure(text=f"{health_data.get('margin_level', 0):.1f}%")


class StatusIndicatorWidget(ctk.CTkLabel):
    """Connection status indicator light"""
    
    def __init__(self, parent, initial_status: str = "disconnected", **kwargs):
        super().__init__(parent, text="●", font=("Arial", 12), **kwargs)
        self.status = initial_status
        self._update_color()
    
    def set_status(self, status: str) -> None:
        """Update status: connected, disconnected, reconnecting, error"""
        self.status = status
        self._update_color()
    
    def _update_color(self) -> None:
        """Update indicator color based on status"""
        colors = {
            "connected": "#00ff88",
            "disconnected": "#666666",
            "reconnecting": "#ffaa00",
            "error": "#ff0000"
        }
        self.configure(text_color=colors.get(self.status, "#666666"))


class TradingControlsWidget(ctk.CTkFrame):
    """Main trading controls"""
    
    def __init__(self, parent, command_callback: Callable, **kwargs):
        super().__init__(parent, fg_color="#1a1a1a", **kwargs)

        self.command_callback = command_callback
        self.grid_columnconfigure(0, weight=1)

        # Execution mode selector
        mode_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        mode_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(8, 4))
        mode_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(mode_frame, text="Execution Mode:", font=("Arial", 11), text_color="#888").grid(row=0, column=0, sticky="w")
        self.execution_mode_var = ctk.StringVar(value="Hedge + Funded")
        self.execution_mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=["Hedge + Funded", "Funded Only", "Hedge Only"],
            variable=self.execution_mode_var,
        )
        self.execution_mode_menu.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        # Phase selection (slot + phase)
        phase_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        phase_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(6, 6))
        phase_frame.grid_columnconfigure(1, weight=1)
        phase_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(phase_frame, text="Slot:", font=("Arial", 11), text_color="#888").grid(row=0, column=0, sticky="w")
        self.phase_slot_var = ctk.StringVar(value="1")
        self.phase_slot_menu = ctk.CTkOptionMenu(
            phase_frame,
            values=["1", "2", "3", "4", "5"],
            variable=self.phase_slot_var,
            command=lambda _value: self._on_phase_selection_changed(),
        )
        self.phase_slot_menu.grid(row=0, column=1, sticky="ew", padx=(10, 12))

        ctk.CTkLabel(phase_frame, text="Phase:", font=("Arial", 11), text_color="#888").grid(row=0, column=2, sticky="w")
        self.phase_var = ctk.StringVar(value="Phase 1")
        self.phase_menu = ctk.CTkOptionMenu(
            phase_frame,
            values=["Phase 1", "Phase 2"],
            variable=self.phase_var,
            command=lambda _value: self._on_phase_selection_changed(),
        )
        self.phase_menu.grid(row=0, column=3, sticky="ew", padx=(10, 0))

        self.phase_badge = ctk.CTkLabel(
            phase_frame,
            text="PHASE 1 ACTIVE",
            font=("Arial", 10, "bold"),
            fg_color="#1e3a8a",
            text_color="#dbeafe",
            corner_radius=6,
            padx=10,
            pady=4,
        )
        self.phase_badge.grid(row=1, column=0, columnspan=4, sticky="w", pady=(8, 0))
        self._refresh_phase_badge()

        # Symbol input
        symbol_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        symbol_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(6, 6))
        symbol_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(symbol_frame, text="Symbol:", font=("Arial", 11), text_color="#888").grid(row=0, column=0, sticky="w")
        self.symbol_var = ctk.StringVar(value="US100")
        self.symbol_input = ctk.CTkEntry(symbol_frame, textvariable=self.symbol_var)
        self.symbol_input.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # Lot size input
        lot_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        lot_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(6, 10))
        lot_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(lot_frame, text="Lot Size:", font=("Arial", 11), text_color="#888").grid(row=0, column=0, sticky="w")
        self.lot_var = ctk.StringVar(value="0.1")
        self.lot_input = ctk.CTkEntry(lot_frame, textvariable=self.lot_var)
        self.lot_input.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        
        # BUY / SELL buttons
        button_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        button_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        self.buy_btn = ctk.CTkButton(
            button_frame,
            text="BUY",
            font=("Arial", 14, "bold"),
            fg_color="#00aa00",
            hover_color="#00ff00",
            command=lambda: self.command_callback("buy")
        )
        self.buy_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        
        self.sell_btn = ctk.CTkButton(
            button_frame,
            text="SELL",
            font=("Arial", 14, "bold"),
            fg_color="#aa0000",
            hover_color="#ff0000",
            command=lambda: self.command_callback("sell")
        )
        self.sell_btn.grid(row=0, column=1, sticky="ew", padx=6)
        
        # Emergency close
        self.close_btn = ctk.CTkButton(
            button_frame,
            text="CLOSE ALL",
            font=("Arial", 12, "bold"),
            fg_color="#555555",
            hover_color="#888888",
            command=lambda: self.command_callback("close_all")
        )
        self.close_btn.grid(row=0, column=2, sticky="ew", padx=(6, 0))
        
        # Feature toggles
        toggle_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        toggle_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=10)
        toggle_frame.grid_columnconfigure(0, weight=1)
        toggle_frame.grid_columnconfigure(1, weight=1)
        
        self.hedge_var = ctk.BooleanVar(value=True)
        hedge_check = ctk.CTkCheckBox(
            toggle_frame,
            text="Hedge Enabled",
            variable=self.hedge_var,
            font=("Arial", 11, "bold"),
            command=lambda: self.command_callback("toggle_hedge")
        )
        hedge_check.grid(row=0, column=0, sticky="w", padx=(0, 8))
        
        self.recovery_var = ctk.BooleanVar(value=True)
        recovery_check = ctk.CTkCheckBox(
            toggle_frame,
            text="Auto Recovery",
            variable=self.recovery_var,
            font=("Arial", 11, "bold"),
            command=lambda: self.command_callback("toggle_recovery")
        )
        recovery_check.grid(row=0, column=1, sticky="w", padx=(8, 0))

        # Recovery / TP/SL controls
        recovery_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        recovery_frame.grid(row=6, column=0, sticky="ew", padx=20, pady=(6, 12))
        recovery_frame.grid_columnconfigure(1, weight=1)
        recovery_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(recovery_frame, text="TP (pips):", font=("Arial", 10), text_color="#888").grid(row=0, column=0, sticky="w")
        self.tp_var = ctk.StringVar(value="10")
        self.tp_input = ctk.CTkEntry(recovery_frame, textvariable=self.tp_var)
        self.tp_input.grid(row=0, column=1, sticky="ew", padx=(6, 12))

        ctk.CTkLabel(recovery_frame, text="SL (pips):", font=("Arial", 10), text_color="#888").grid(row=0, column=2, sticky="w")
        self.sl_var = ctk.StringVar(value="20")
        self.sl_input = ctk.CTkEntry(recovery_frame, textvariable=self.sl_var)
        self.sl_input.grid(row=0, column=3, sticky="ew", padx=(6, 12))

        calc_btn = ctk.CTkButton(recovery_frame, text="Calculate Recovery", command=lambda: self.command_callback("calc_recovery"))
        calc_btn.grid(row=0, column=4, sticky="e")

        # Recovery estimate display
        estimate_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        estimate_frame.grid(row=7, column=0, sticky="ew", padx=20, pady=(0, 10))
        estimate_frame.grid_columnconfigure(0, weight=1)
        self.estimate_label = ctk.CTkLabel(estimate_frame, text="Est Hedge Lot: - | Target: $-", font=("Arial", 10), text_color="#00ff88")
        self.estimate_label.grid(row=0, column=0, sticky="w")
        # Injection / execution overlay status (updated during bridge operations)
        self.inject_status_label = ctk.CTkLabel(estimate_frame, text="", font=("Arial", 10, "bold"), text_color="#00ff88")
        self.inject_status_label.grid(row=1, column=0, sticky="w", pady=(4,0))
    
    def get_lot_size(self) -> float:
        """Get current lot size"""
        try:
            return float(self.lot_var.get())
        except ValueError:
            return 0.1

    def get_symbol(self) -> str:
        """Get the trade symbol entered by the user."""
        symbol = self.symbol_var.get().strip().upper().replace(" ", "")
        return symbol or "US100"

    def get_tp_sl(self) -> tuple:
        """Return TP and SL in pips as floats."""
        try:
            tp = float(self.tp_var.get())
        except Exception:
            tp = 10.0
        try:
            sl = float(self.sl_var.get())
        except Exception:
            sl = 20.0
        return tp, sl

    def get_execution_mode(self) -> str:
        """Return selected execution mode."""
        mode = self.execution_mode_var.get().strip()
        return mode or "Hedge + Funded"

    def get_selected_slot(self) -> int:
        """Return selected Maven slot from the phase selector."""
        try:
            return max(1, min(5, int(self.phase_slot_var.get())))
        except Exception:
            return 1

    def get_selected_phase(self) -> str:
        """Return selected challenge phase."""
        value = self.phase_var.get().strip()
        return value if value in ("Phase 1", "Phase 2") else "Phase 1"

    def set_selected_phase(self, slot_id: int, phase: str) -> None:
        """Update the UI phase selector from persisted account state."""
        try:
            self.phase_slot_var.set(str(max(1, min(5, int(slot_id)))))
        except Exception:
            self.phase_slot_var.set("1")
        self.phase_var.set("Phase 2" if str(phase).strip().lower() == "phase 2" else "Phase 1")
        self._refresh_phase_badge()

    def _on_phase_selection_changed(self) -> None:
        self._refresh_phase_badge()
        self.command_callback(
            "phase_changed",
            slot_id=self.get_selected_slot(),
            phase=self.get_selected_phase(),
        )

    def _refresh_phase_badge(self) -> None:
        phase = self.get_selected_phase()
        if phase == "Phase 2":
            self.phase_badge.configure(text="PHASE 2 ACTIVE", fg_color="#166534", text_color="#dcfce7")
        else:
            self.phase_badge.configure(text="PHASE 1 ACTIVE", fg_color="#1e3a8a", text_color="#dbeafe")

    def set_recovery_estimate(self, lot: float, target: float) -> None:
        """Update the UI with recovery estimate values."""
        try:
            self.estimate_label.configure(text=f"Est Hedge Lot: {lot:.2f}L | Target: ${target:.2f}")
        except Exception:
            pass

    def set_trading_enabled(self, enabled: bool) -> None:
        """Enable/disable new entries while keeping emergency close available."""
        state = "normal" if enabled else "disabled"
        try:
            self.buy_btn.configure(state=state)
            self.sell_btn.configure(state=state)
            self.phase_slot_menu.configure(state=state)
            self.phase_menu.configure(state=state)
            self.symbol_input.configure(state=state)
            self.lot_input.configure(state=state)
            self.tp_input.configure(state=state)
            self.sl_input.configure(state=state)
        except Exception:
            pass

    def set_overlay_status(self, text: str) -> None:
        """Display a short overlay/status message (e.g., 'Injecting 8.4 Lots...')."""
        try:
            if not text:
                self.inject_status_label.configure(text="")
            else:
                self.inject_status_label.configure(text=text)
        except Exception:
            pass


class ChallengeConfigWidget(ctk.CTkFrame):
    """Challenge configuration and hedge intelligence panel."""

    ACCOUNT_SIZE_OPTIONS = ["2K", "5K", "10K", "25K", "50K", "Custom"]
    INSTRUMENT_OPTIONS = [
        "USTECH", "US100", "NAS100", "US30", "SPX500",
        "XAUUSD", "XAGUSD",
        "EURUSD", "GBPUSD", "USDJPY", "GBPJPY", "EURJPY",
    ]
    RECOVERY_MODES = ["conservative", "balanced", "aggressive"]

    def __init__(self, parent, action_callback: Callable[[str, Dict[str, Any]], None], **kwargs):
        super().__init__(parent, fg_color="#121826", **kwargs)
        self.action_callback = action_callback
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.account_size_option = ctk.StringVar(value="5K")
        self.custom_account_size = ctk.StringVar(value="5000")
        self.purchase_fee = ctk.StringVar(value="59")
        self.profit_target_pct = ctk.StringVar(value="8")
        self.daily_dd_pct = ctk.StringVar(value="5")
        self.overall_dd_pct = ctk.StringVar(value="10")
        self.max_lots_allowed = ctk.StringVar(value="5")
        self.profit_split_pct = ctk.StringVar(value="80")
        self.stop_loss_pips = ctk.StringVar(value="20")
        self.take_profit_pips = ctk.StringVar(value="10")
        self.recovery_deficit = ctk.StringVar(value="0")
        self.desired_surplus = ctk.StringVar(value="100")
        self.risk_per_trade_pct = ctk.StringVar(value="0.50")
        self.realized_hedge_loss = ctk.StringVar(value="0")
        self.symbol = ctk.StringVar(value="US100")
        self.recovery_mode = ctk.StringVar(value="balanced")
        self.template_name = ctk.StringVar(value="Maven 5K")

        title = ctk.CTkLabel(self, text="CHALLENGE CONFIGURATION", font=("Arial", 12, "bold"), text_color="#00ffcc")
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(10, 8))

        self._add_option_menu(1, "Account Size", self.account_size_option, self.ACCOUNT_SIZE_OPTIONS)
        self._add_entry(2, "Custom Size", self.custom_account_size)
        self._add_entry(3, "Purchase Fee", self.purchase_fee)
        self._add_entry(4, "Profit Target %", self.profit_target_pct)
        self._add_entry(5, "Daily DD %", self.daily_dd_pct)
        self._add_entry(6, "Overall DD %", self.overall_dd_pct)
        self._add_entry(7, "Max Lots", self.max_lots_allowed)
        self._add_entry(8, "Profit Split %", self.profit_split_pct)
        self._add_option_menu(9, "Instrument", self.symbol, self.INSTRUMENT_OPTIONS)
        self._add_entry(10, "Stop Loss (pips)", self.stop_loss_pips)
        self._add_entry(11, "Take Profit (pips)", self.take_profit_pips)
        self._add_option_menu(12, "Recovery Mode", self.recovery_mode, self.RECOVERY_MODES)
        self._add_entry(13, "Recovery Deficit", self.recovery_deficit)
        self._add_entry(14, "Desired Surplus", self.desired_surplus)
        self._add_entry(15, "Risk/Trade %", self.risk_per_trade_pct)
        self._add_entry(16, "Realized Hedge Loss", self.realized_hedge_loss)

        template_row = ctk.CTkFrame(self, fg_color="#121826")
        template_row.grid(row=17, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 6))
        template_row.grid_columnconfigure(0, weight=1)
        template_entry = ctk.CTkEntry(template_row, textvariable=self.template_name)
        template_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(template_row, text="Save Template", command=self._save_template).grid(row=0, column=1, padx=3)

        action_row = ctk.CTkFrame(self, fg_color="#121826")
        action_row.grid(row=18, column=0, columnspan=2, sticky="ew", padx=12, pady=(4, 10))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)
        action_row.grid_columnconfigure(2, weight=1)

        ctk.CTkButton(action_row, text="Apply Rules", fg_color="#005f87", hover_color="#007fb4", command=self._apply_rules).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkButton(action_row, text="Compute Hedge Plan", fg_color="#0b7d3b", hover_color="#0ea94f", command=self._compute_plan).grid(row=0, column=1, sticky="ew", padx=(6, 6))
        ctk.CTkButton(action_row, text="Auto-Fill Hedge P/L", fg_color="#7a3e00", hover_color="#a85400", command=self._auto_fill_loss).grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=(6, 0))
        ctk.CTkButton(action_row, text="Record Hedge Loss", fg_color="#9c4f00", hover_color="#bf6500", command=self._record_hedge_loss).grid(row=1, column=1, columnspan=2, sticky="ew", padx=(6, 0), pady=(6, 0))

        self.output_label = ctk.CTkLabel(
            self,
            text="Funded Lot: - | Hedge Lot: - | Recovery Target: $-",
            font=("Arial", 10, "bold"),
            text_color="#00ff88",
            justify="left",
            wraplength=560,
        )
        self.output_label.grid(row=19, column=0, columnspan=2, sticky="w", padx=12, pady=(2, 10))

    def _add_entry(self, row: int, label: str, variable: ctk.StringVar) -> None:
        ctk.CTkLabel(self, text=label, font=("Arial", 10), text_color="#a9b4cf").grid(
            row=row, column=0, sticky="w", padx=12, pady=4
        )
        ctk.CTkEntry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", padx=12, pady=4)

    def _add_option_menu(self, row: int, label: str, variable: ctk.StringVar, values: List[str]) -> None:
        ctk.CTkLabel(self, text=label, font=("Arial", 10), text_color="#a9b4cf").grid(
            row=row, column=0, sticky="w", padx=12, pady=4
        )
        ctk.CTkOptionMenu(self, variable=variable, values=values).grid(row=row, column=1, sticky="ew", padx=12, pady=4)

    def _to_float(self, value: str, fallback: float) -> float:
        try:
            return float(str(value).strip())
        except Exception:
            return fallback

    def _resolve_account_size(self) -> float:
        selected = self.account_size_option.get().strip().upper()
        preset_map = {
            "2K": 2000.0,
            "5K": 5000.0,
            "10K": 10000.0,
            "25K": 25000.0,
            "50K": 50000.0,
        }
        if selected in preset_map:
            return preset_map[selected]
        return max(500.0, self._to_float(self.custom_account_size.get(), 5000.0))

    def _collect_payload(self) -> Dict[str, Any]:
        return {
            "account_size": self._resolve_account_size(),
            "purchase_fee": self._to_float(self.purchase_fee.get(), 59.0),
            "profit_target_pct": self._to_float(self.profit_target_pct.get(), 8.0),
            "daily_drawdown_pct": self._to_float(self.daily_dd_pct.get(), 5.0),
            "overall_drawdown_pct": self._to_float(self.overall_dd_pct.get(), 10.0),
            "max_lots_allowed": self._to_float(self.max_lots_allowed.get(), 5.0),
            "profit_split_pct": self._to_float(self.profit_split_pct.get(), 80.0),
            "symbol": self.symbol.get().strip().upper(),
            "stop_loss_pips": self._to_float(self.stop_loss_pips.get(), 20.0),
            "take_profit_pips": self._to_float(self.take_profit_pips.get(), 10.0),
            "recovery_deficit": self._to_float(self.recovery_deficit.get(), 0.0),
            "desired_surplus": self._to_float(self.desired_surplus.get(), 100.0),
            "risk_per_trade_pct": self._to_float(self.risk_per_trade_pct.get(), 0.5),
            "recovery_mode": self.recovery_mode.get().strip().lower(),
        }

    def _apply_rules(self) -> None:
        self.action_callback("apply_challenge_rules", self._collect_payload())

    def _compute_plan(self) -> None:
        self.action_callback("compute_dynamic_plan", self._collect_payload())

    def _save_template(self) -> None:
        payload = self._collect_payload()
        payload["template_name"] = self.template_name.get().strip()
        self.action_callback("save_template", payload)

    def _record_hedge_loss(self) -> None:
        payload = self._collect_payload()
        payload["realized_hedge_loss"] = self._to_float(self.realized_hedge_loss.get(), 0.0)
        self.action_callback("record_hedge_loss", payload)

    def _auto_fill_loss(self) -> None:
        self.action_callback("auto_fill_latest_hedge_loss", self._collect_payload())

    def update_output(self, result: Dict[str, Any]) -> None:
        if not result:
            return
        text = (
            f"Funded Lot: {result.get('funded_lot_size', 0.0):.2f} | "
            f"Hedge Lot: {result.get('hedge_lot_size', 0.0):.2f} | "
            f"Recovery Target: ${result.get('recovery_target', 0.0):.2f} | "
            f"Max Loss: ${result.get('max_loss_projection', 0.0):.2f} | "
            f"Recovery Efficiency: {result.get('recovery_efficiency_pct', 0.0):.1f}%"
        )
        self.output_label.configure(text=text)


class AccountGridWidget(ctk.CTkFrame):
    """Maven account fleet grid"""
    
    def __init__(self, parent, account_manager, **kwargs):
        super().__init__(parent, fg_color="#1a1a1a", **kwargs)
        
        self.account_manager = account_manager
        self.account_widgets: Dict[int, ctk.CTkFrame] = {}
        
        # Create slots
        for slot_id in range(1, 6):
            self._create_account_slot(slot_id)
    
    def _create_account_slot(self, slot_id: int) -> None:
        """Create individual account slot widget"""
        slot_frame = ctk.CTkFrame(self, fg_color="#0f0f0f", corner_radius=5)
        slot_frame.pack(fill="x", padx=10, pady=5)
        
        # Account info
        info_frame = ctk.CTkFrame(slot_frame, fg_color="#0f0f0f")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Active checkbox
        active_var = ctk.BooleanVar()
        active_check = ctk.CTkCheckBox(
            info_frame,
            text=f"Slot {slot_id}",
            variable=active_var,
            font=("Arial", 10),
            command=lambda: self.account_manager.set_account_active(slot_id, active_var.get())
        )
        active_check.pack(side="left", padx=5)
        
        # Account number
        account = self.account_manager.get_account(slot_id)
        if account:
            acc_text = f"Account: {account.account_number}"
            phase_text = f"({account.phase.value})"
            phase_color = "#166534" if account.phase.value == "Phase 2" else "#1e3a8a"
            phase_label_text = account.phase.value.upper()
        else:
            acc_text = "Not configured"
            phase_text = ""
            phase_color = "#444444"
            phase_label_text = "UNSET"
        
        acc_label = ctk.CTkLabel(
            info_frame,
            text=f"{acc_text} {phase_text}",
            font=("Arial", 9),
            text_color="#888"
        )
        acc_label.pack(side="left", padx=10)

        phase_badge = ctk.CTkLabel(
            info_frame,
            text=phase_label_text,
            font=("Arial", 9, "bold"),
            fg_color=phase_color,
            text_color="#e5e7eb",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        phase_badge.pack(side="right", padx=6)

        # keep references for updates
        slot_frame._acc_label = acc_label
        slot_frame._phase_badge = phase_badge
        slot_frame._active_var = active_var
        slot_frame._active_check = active_check

        self.account_widgets[slot_id] = slot_frame
    
    def refresh_accounts(self, mt5_manager=None) -> None:
        """Refresh account display"""
        try:
            for slot_id, slot_frame in sorted(self.account_widgets.items()):
                account = self.account_manager.get_account(slot_id)
                if account:
                    acc_text = f"Account: {account.account_number}"
                    phase_text = f"({account.phase.value})"
                    # Attempt to fetch live balance if MT5 is available via account manager vault proxy
                    balance_text = ""
                    try:
                        # If the vault stored credentials we can try to fetch a quick balance via account manager vault key
                        creds = self.account_manager.get_account_credentials(slot_id)
                        if creds:
                            # The actual balance fetch requires MT5 manager; leave balance blank here
                            balance_text = ""
                    except Exception:
                        balance_text = ""

                    display = f"{acc_text} {phase_text} {balance_text}".strip()
                    try:
                        slot_frame._acc_label.configure(text=display)
                        is_phase_2 = account.phase.value == "Phase 2"
                        slot_frame._phase_badge.configure(
                            text=account.phase.value.upper(),
                            fg_color="#166534" if is_phase_2 else "#1e3a8a",
                        )
                    except Exception:
                        pass
                else:
                    try:
                        slot_frame._acc_label.configure(text="Not configured")
                        slot_frame._phase_badge.configure(text="UNSET", fg_color="#444444")
                    except Exception:
                        pass
        except Exception:
            pass
