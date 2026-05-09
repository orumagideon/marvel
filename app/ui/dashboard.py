"""
Main Dashboard UI
Professional SaaS-style trading dashboard with CustomTkinter
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable
import asyncio
import threading
from datetime import datetime
from app.core.orchestrator import get_system
from app.ui.components import (
    MarketFeedWidget, AccountHealthWidget, StatusIndicatorWidget,
    TradingControlsWidget, AccountGridWidget
)


class MarvelDashboard(ctk.CTk):
    """
    Main application window
    Professional trading dashboard for Marvel system
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.title("Marvel Trading Dashboard")
        self.geometry("1600x900")
        self.configure(fg_color="#0a0a0a")
        
        # Initialize system
        self.system = get_system()
        self.logger = self.system.logger
        
        # UI State
        self.update_thread: Optional[threading.Thread] = None
        self.is_running = True
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main layout
        self._create_layout()
        
        # Start background updates
        self._start_update_loop()
        
        self.logger.info("Marvel Dashboard initialized")
    
    def _create_layout(self) -> None:
        """Create main dashboard layout"""
        
        # Main container
        main_container = ctk.CTkFrame(self, fg_color="#0a0a0a")
        main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
        
        # === HEADER ===
        self._create_header(main_container)
        
        # === MAIN CONTENT AREA ===
        content_frame = ctk.CTkFrame(main_container, fg_color="#0a0a0a")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Left Panel: Market & Health
        left_panel = self._create_left_panel(content_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Right Panel: Controls & Accounts
        right_panel = self._create_right_panel(content_frame)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
    
    def _create_header(self, parent) -> None:
        """Create header with title and connection status"""
        header = ctk.CTkFrame(parent, fg_color="#1a1a1a", height=80)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header,
            text="MARVEL TRADING DASHBOARD",
            font=("Arial", 24, "bold"),
            text_color="#00ff88"
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        # Status indicators
        status_frame = ctk.CTkFrame(header, fg_color="#1a1a1a")
        status_frame.pack(side="right", padx=20, pady=20)
        
        # Maven Instance Status
        ctk.CTkLabel(status_frame, text="Maven:", text_color="#888", font=("Arial", 10)).pack(side="left", padx=5)
        self.maven_status = StatusIndicatorWidget(status_frame, "disconnected")
        self.maven_status.pack(side="left", padx=5)
        
        # Hedge Instance Status
        ctk.CTkLabel(status_frame, text="Hedge:", text_color="#888", font=("Arial", 10)).pack(side="left", padx=5)
        self.hedge_status = StatusIndicatorWidget(status_frame, "disconnected")
        self.hedge_status.pack(side="left", padx=5)
        
        # Session ID
        session_label = ctk.CTkLabel(
            header,
            text=f"Session: {self.system.session_id}",
            font=("Arial", 9),
            text_color="#666"
        )
        session_label.pack(side="right", padx=20, pady=20)
    
    def _create_left_panel(self, parent) -> ctk.CTkFrame:
        """Create left panel with market data and health"""
        left_panel = ctk.CTkFrame(parent, fg_color="#0a0a0a")
        left_panel.grid_rowconfigure(1, weight=1)
        
        # Market Feed
        market_label = ctk.CTkLabel(
            left_panel,
            text="MARKET FEED",
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        )
        market_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.market_feed = MarketFeedWidget(left_panel)
        self.market_feed.grid(row=1, column=0, sticky="nsew")
        
        # Account Health
        health_label = ctk.CTkLabel(
            left_panel,
            text="ACCOUNT HEALTH",
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        )
        health_label.grid(row=2, column=0, sticky="ew", pady=(20, 10))
        
        self.account_health = AccountHealthWidget(left_panel)
        self.account_health.grid(row=3, column=0, sticky="nsew")
        
        return left_panel
    
    def _create_right_panel(self, parent) -> ctk.CTkFrame:
        """Create right panel with controls and account grid"""
        right_panel = ctk.CTkFrame(parent, fg_color="#0a0a0a")
        right_panel.grid_rowconfigure(1, weight=1)
        
        # Trading Controls
        controls_label = ctk.CTkLabel(
            right_panel,
            text="TRADING CONTROLS",
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        )
        controls_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.trading_controls = TradingControlsWidget(right_panel, self._on_trade_command)
        self.trading_controls.grid(row=1, column=0, sticky="nsew")
        
        # Account Grid
        accounts_label = ctk.CTkLabel(
            right_panel,
            text="MAVEN FLEET",
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        )
        accounts_label.grid(row=2, column=0, sticky="ew", pady=(20, 10))
        
        self.account_grid = AccountGridWidget(right_panel, self.system.account_manager)
        self.account_grid.grid(row=3, column=0, sticky="nsew")
        
        return right_panel
    
    def _on_trade_command(self, command: str, *args, **kwargs) -> None:
        """Handle trading command from UI"""
        if command == "buy":
            asyncio.run(self._execute_buy())
        elif command == "sell":
            asyncio.run(self._execute_sell())
        elif command == "close_all":
            asyncio.run(self._close_all())
        elif command == "toggle_hedge":
            self.system.hedge_enabled = not self.system.hedge_enabled
        elif command == "toggle_recovery":
            self.system.auto_recovery_enabled = not self.system.auto_recovery_enabled
    
    async def _execute_buy(self) -> None:
        """Execute BUY order"""
        lot_size = self.trading_controls.get_lot_size()
        symbol = "US100"
        
        success, results = await self.system.execute_buy_order(symbol, lot_size)
        
        if success:
            self.logger.info(f"BUY executed: {results.get('success_count')} accounts")
        else:
            self.logger.error(f"BUY failed: {results.get('error', 'Unknown error')}")
    
    async def _execute_sell(self) -> None:
        """Execute SELL order"""
        lot_size = self.trading_controls.get_lot_size()
        symbol = "US100"
        
        success, results = await self.system.execute_sell_order(symbol, lot_size)
        
        if success:
            self.logger.info(f"SELL executed: {results.get('success_count')} accounts")
        else:
            self.logger.error(f"SELL failed: {results.get('error', 'Unknown error')}")
    
    async def _close_all(self) -> None:
        """Emergency close all positions"""
        results = await self.system.close_all_emergency()
        self.logger.info(f"Emergency close: {results.get('closed_count', 0)} positions closed")
    
    def _start_update_loop(self) -> None:
        """Start background update thread"""
        def update_loop():
            while self.is_running:
                try:
                    # Update market data
                    market_data = self.system.get_market_data()
                    if market_data:
                        self.market_feed.update_data(market_data)
                    
                    # Update status indicators
                    maven_connected = self.system.mt5_manager.is_connected(
                        self.system.mt5_manager.MT5InstanceType.MAVEN_FLEET
                        if hasattr(self.system.mt5_manager, 'MT5InstanceType')
                        else "maven_fleet"
                    )
                    # Note: This needs adjustment for proper status
                    
                    # Update account grid
                    self.account_grid.refresh_accounts()
                    
                    threading.Event().wait(0.5)
                except Exception as e:
                    self.logger.debug(f"Update loop error: {str(e)}")
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
    
    def on_closing(self) -> None:
        """Handle window close"""
        self.is_running = False
        self.system.shutdown()
        self.destroy()


def main():
    """Launch Marvel Dashboard"""
    app = MarvelDashboard()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
