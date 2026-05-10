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

        # Symbol input
        symbol_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        symbol_frame.pack(fill="x", padx=20, pady=(10, 6))

        ctk.CTkLabel(symbol_frame, text="Symbol:", font=("Arial", 11), text_color="#888").pack(side="left")
        self.symbol_var = ctk.StringVar(value="US100")
        self.symbol_input = ctk.CTkEntry(symbol_frame, textvariable=self.symbol_var, width=130)
        self.symbol_input.pack(side="left", padx=10)
        
        # Lot size input
        lot_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        lot_frame.pack(fill="x", padx=20, pady=(6, 10))
        
        ctk.CTkLabel(lot_frame, text="Lot Size:", font=("Arial", 11), text_color="#888").pack(side="left")
        self.lot_var = ctk.StringVar(value="0.1")
        self.lot_input = ctk.CTkEntry(lot_frame, textvariable=self.lot_var, width=100)
        self.lot_input.pack(side="left", padx=10)
        
        # BUY / SELL buttons
        button_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        buy_btn = ctk.CTkButton(
            button_frame,
            text="BUY",
            font=("Arial", 14, "bold"),
            fg_color="#00aa00",
            hover_color="#00ff00",
            command=lambda: self.command_callback("buy")
        )
        buy_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        sell_btn = ctk.CTkButton(
            button_frame,
            text="SELL",
            font=("Arial", 14, "bold"),
            fg_color="#aa0000",
            hover_color="#ff0000",
            command=lambda: self.command_callback("sell")
        )
        sell_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Emergency close
        close_btn = ctk.CTkButton(
            button_frame,
            text="CLOSE ALL",
            font=("Arial", 12, "bold"),
            fg_color="#555555",
            hover_color="#888888",
            command=lambda: self.command_callback("close_all")
        )
        close_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        # Feature toggles
        toggle_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        toggle_frame.pack(fill="x", padx=20, pady=10)
        
        self.hedge_var = ctk.BooleanVar(value=True)
        hedge_check = ctk.CTkCheckBox(
            toggle_frame,
            text="Hedge Enabled",
            variable=self.hedge_var,
            font=("Arial", 11, "bold"),
            command=lambda: self.command_callback("toggle_hedge")
        )
        hedge_check.pack(side="left", padx=8)
        
        self.recovery_var = ctk.BooleanVar(value=True)
        recovery_check = ctk.CTkCheckBox(
            toggle_frame,
            text="Auto Recovery",
            variable=self.recovery_var,
            font=("Arial", 11, "bold"),
            command=lambda: self.command_callback("toggle_recovery")
        )
        recovery_check.pack(side="left", padx=8)

        # Recovery / TP/SL controls
        recovery_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        recovery_frame.pack(fill="x", padx=20, pady=(6, 12))

        ctk.CTkLabel(recovery_frame, text="TP (pips):", font=("Arial", 10), text_color="#888").pack(side="left")
        self.tp_var = ctk.StringVar(value="10")
        self.tp_input = ctk.CTkEntry(recovery_frame, textvariable=self.tp_var, width=70)
        self.tp_input.pack(side="left", padx=6)

        ctk.CTkLabel(recovery_frame, text="SL (pips):", font=("Arial", 10), text_color="#888").pack(side="left", padx=(10,0))
        self.sl_var = ctk.StringVar(value="20")
        self.sl_input = ctk.CTkEntry(recovery_frame, textvariable=self.sl_var, width=70)
        self.sl_input.pack(side="left", padx=6)

        calc_btn = ctk.CTkButton(recovery_frame, text="Calculate Recovery", command=lambda: self.command_callback("calc_recovery"))
        calc_btn.pack(side="right")

        # Recovery estimate display
        estimate_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        estimate_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.estimate_label = ctk.CTkLabel(estimate_frame, text="Est Hedge Lot: - | Target: $-", font=("Arial", 10), text_color="#00ff88")
        self.estimate_label.pack(side="left")
    
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

    def set_recovery_estimate(self, lot: float, target: float) -> None:
        """Update the UI with recovery estimate values."""
        try:
            self.estimate_label.configure(text=f"Est Hedge Lot: {lot:.2f}L | Target: ${target:.2f}")
        except Exception:
            pass


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
        else:
            acc_text = "Not configured"
            phase_text = ""
        
        acc_label = ctk.CTkLabel(
            info_frame,
            text=f"{acc_text} {phase_text}",
            font=("Arial", 9),
            text_color="#888"
        )
        acc_label.pack(side="left", padx=10)

        # keep references for updates
        slot_frame._acc_label = acc_label
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
                    except Exception:
                        pass
                else:
                    try:
                        slot_frame._acc_label.configure(text="Not configured")
                    except Exception:
                        pass
        except Exception:
            pass
