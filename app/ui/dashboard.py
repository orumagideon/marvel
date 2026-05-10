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
from app.mt5_bridge.connection_manager import MT5InstanceType, ConnectionState
from app.utils.config import get_config
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
        self.config = get_config()
        self.credentials_vault = self.system.account_manager.vault
        
        # UI State
        self.update_thread: Optional[threading.Thread] = None
        self.is_running = True

        self.maven_terminal_var = ctk.StringVar(value=self.config.get("mt5.maven_terminal_path", ""))
        self.maven_account_var = ctk.StringVar(value="")
        self.maven_password_var = ctk.StringVar(value="")
        self.maven_server_var = ctk.StringVar(value="")
        self.maven_remember_var = ctk.BooleanVar(value=True)

        self.hedge_terminal_var = ctk.StringVar(value=self.config.get("mt5.hedge_terminal_path", ""))
        self.hedge_account_var = ctk.StringVar(value="")
        self.hedge_password_var = ctk.StringVar(value="")
        self.hedge_server_var = ctk.StringVar(value="")
        self.hedge_remember_var = ctk.BooleanVar(value=True)

        self.auto_connect_var = ctk.BooleanVar(value=self.config.get("ui.auto_connect_on_startup", True))
        self._resize_after_id = None
        self._layout_mode = None
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Create main layout
        self._create_layout()
        
        # Start background updates
        self._start_update_loop()

        # Keep the dashboard responsive as the window resizes
        self.bind("<Configure>", self._on_window_configure)

        # Attempt auto-connect after the UI is visible
        self.after(750, self._auto_connect_saved_instances)
        
        self.logger.info("Marvel Dashboard initialized")
    
    def _create_layout(self) -> None:
        """Create main dashboard layout"""
        
        # Main container
        self.main_container = ctk.CTkFrame(self, fg_color="#0a0a0a")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.main_container.grid_rowconfigure(2, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # === HEADER ===
        self._create_header(self.main_container)

        # === LOGIN PANEL ===
        self._create_login_panel(self.main_container)
        
        # === MAIN CONTENT AREA ===
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="#0a0a0a")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        
        # Left Panel: Market & Health
        self.left_panel = self._create_left_panel(self.content_frame)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Right Panel: Controls & Accounts
        self.right_panel = self._create_right_panel(self.content_frame)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self._apply_responsive_layout()

    def _on_window_configure(self, event) -> None:
        """Debounce layout recalculation on resize."""
        try:
            if event.widget is not self:
                return
            if self._resize_after_id is not None:
                self.after_cancel(self._resize_after_id)
            self._resize_after_id = self.after(100, self._apply_responsive_layout)
        except Exception:
            pass

    def _apply_responsive_layout(self) -> None:
        """Switch between wide and compact dashboard layouts."""
        try:
            width = self.winfo_width() or self.winfo_reqwidth() or 1600
            compact = width < 1400
            layout_mode = "compact" if compact else "wide"

            if layout_mode == self._layout_mode:
                return

            self._layout_mode = layout_mode

            # Login panel layout
            self.main_container.grid_rowconfigure(1, weight=0)
            if compact:
                self.main_container.grid_rowconfigure(2, weight=1)
                self.main_container.grid_columnconfigure(0, weight=1)
                self.login_panel.grid_columnconfigure(0, weight=1)
                self.login_panel.grid_columnconfigure(1, weight=0)
                self.maven_login_card.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 8))
                self.hedge_login_card.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 12))

                # Stack the main panels vertically
                self.content_frame.grid_rowconfigure(0, weight=1)
                self.content_frame.grid_rowconfigure(1, weight=1)
                self.content_frame.grid_columnconfigure(0, weight=1)
                self.content_frame.grid_columnconfigure(1, weight=0)
                self.left_panel.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 10))
                self.right_panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
            else:
                self.main_container.grid_rowconfigure(2, weight=1)
                self.main_container.grid_columnconfigure(0, weight=1)
                self.login_panel.grid_columnconfigure(0, weight=1)
                self.login_panel.grid_columnconfigure(1, weight=1)
                self.maven_login_card.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 12))
                self.hedge_login_card.grid(row=1, column=1, sticky="nsew", padx=10, pady=(0, 12))

                # Restore side-by-side main panels
                self.content_frame.grid_rowconfigure(0, weight=1)
                self.content_frame.grid_rowconfigure(1, weight=0)
                self.content_frame.grid_columnconfigure(0, weight=1)
                self.content_frame.grid_columnconfigure(1, weight=1)
                self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=0)
                self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=0)
        except Exception as e:
            self.logger.debug(f"Responsive layout update failed: {str(e)}")
    
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

    def _create_login_panel(self, parent) -> None:
        """Create MT5 login panel for Maven and hedge accounts"""
        self.login_panel = ctk.CTkFrame(parent, fg_color="#111111")
        self.login_panel.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.login_panel.grid_columnconfigure(0, weight=1)
        self.login_panel.grid_columnconfigure(1, weight=1)
        self.login_panel.grid_rowconfigure(1, weight=1)
        self.login_panel.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self.login_panel,
            text="MT5 LOGIN",
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(10, 6))

        self.maven_login_status_label = ctk.CTkLabel(
            self.login_panel,
            text="Maven: disconnected",
            font=("Arial", 10),
            text_color="#888888"
        )
        self.maven_login_status_label.grid(row=0, column=1, sticky="e", padx=15, pady=(10, 6))

        self.hedge_login_status_label = ctk.CTkLabel(
            self.login_panel,
            text="Hedge: disconnected",
            font=("Arial", 10),
            text_color="#888888"
        )
        self.hedge_login_status_label.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 6))

        self.maven_login_card = self._create_login_card(
            self.login_panel,
            title_text="MAVEN FLEET LOGIN",
            row=1,
            column=0,
            terminal_var=self.maven_terminal_var,
            account_var=self.maven_account_var,
            password_var=self.maven_password_var,
            server_var=self.maven_server_var,
            remember_var=self.maven_remember_var,
            connect_callback=self._connect_maven
        )

        self.hedge_login_card = self._create_login_card(
            self.login_panel,
            title_text="PERSONAL HEDGE LOGIN",
            row=1,
            column=1,
            terminal_var=self.hedge_terminal_var,
            account_var=self.hedge_account_var,
            password_var=self.hedge_password_var,
            server_var=self.hedge_server_var,
            remember_var=self.hedge_remember_var,
            connect_callback=self._connect_hedge
        )

        self._load_saved_credentials()

        ctk.CTkCheckBox(
            self.login_panel,
            text="Auto-connect on startup",
            variable=self.auto_connect_var,
            font=("Arial", 10)
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            self.login_panel,
            text="Saved credentials are stored in the encrypted vault and can auto-connect on startup.",
            font=("Arial", 9),
            text_color="#666666"
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=15, pady=(0, 10))

    def _create_login_card(
        self,
        parent,
        title_text: str,
        row: int,
        column: int,
        terminal_var: ctk.StringVar,
        account_var: ctk.StringVar,
        password_var: ctk.StringVar,
        server_var: ctk.StringVar,
        remember_var: ctk.BooleanVar,
        connect_callback: Callable[[], None]
    ) -> ctk.CTkFrame:
        """Create one MT5 login card."""
        card = ctk.CTkFrame(parent, fg_color="#1a1a1a")
        card.grid(row=row, column=column, sticky="nsew", padx=10, pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card,
            text=title_text,
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=15, pady=(12, 10))

        row_index = 1
        self._add_login_field(card, row_index, "Terminal Path", terminal_var)
        row_index += 1
        self._add_login_field(card, row_index, "Account", account_var)
        row_index += 1
        self._add_login_field(card, row_index, "Password", password_var, show="*")
        row_index += 1
        self._add_login_field(card, row_index, "Server", server_var)
        row_index += 1

        options_frame = ctk.CTkFrame(card, fg_color="#1a1a1a")
        options_frame.grid(row=row_index, column=0, columnspan=2, sticky="ew", padx=15, pady=(4, 8))
        options_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkCheckBox(
            options_frame,
            text="Remember credentials",
            variable=remember_var,
            font=("Arial", 10)
        ).grid(row=0, column=0, sticky="w")

        status_label = ctk.CTkLabel(
            options_frame,
            text="Disconnected",
            font=("Arial", 10, "bold"),
            text_color="#888888"
        )
        status_label.grid(row=0, column=1, sticky="e")

        button = ctk.CTkButton(
            card,
            text="Connect & Login",
            font=("Arial", 12, "bold"),
            fg_color="#0066cc",
            hover_color="#0080ff",
            command=connect_callback
        )
        button.grid(row=row_index + 1, column=0, columnspan=2, sticky="ew", padx=15, pady=(4, 14))

        card._status_label = status_label  # type: ignore[attr-defined]
        return card

    def _add_login_field(self, parent, row: int, label: str, variable: ctk.StringVar, show: str = "") -> None:
        """Helper for login form fields."""
        ctk.CTkLabel(
            parent,
            text=label,
            font=("Arial", 10),
            text_color="#888"
        ).grid(row=row, column=0, sticky="w", padx=15, pady=4)

        entry = ctk.CTkEntry(parent, textvariable=variable, show=show)
        entry.grid(row=row, column=1, sticky="ew", padx=15, pady=4)

    def _load_saved_credentials(self) -> None:
        """Load saved login credentials and terminal paths into the form."""
        try:
            maven_saved = self.credentials_vault.get_account("dashboard_maven_login") or {}
            hedge_saved = self.credentials_vault.get_account("dashboard_hedge_login") or {}

            if maven_saved:
                self.maven_account_var.set(str(maven_saved.get("account_number", "")))
                self.maven_password_var.set(maven_saved.get("password", ""))
                self.maven_server_var.set(maven_saved.get("server", ""))
                self.maven_terminal_var.set(maven_saved.get("terminal_path", self.maven_terminal_var.get()))

            if hedge_saved:
                self.hedge_account_var.set(str(hedge_saved.get("account_number", "")))
                self.hedge_password_var.set(hedge_saved.get("password", ""))
                self.hedge_server_var.set(hedge_saved.get("server", ""))
                self.hedge_terminal_var.set(hedge_saved.get("terminal_path", self.hedge_terminal_var.get()))
        except Exception as e:
            self.logger.debug(f"Failed to load saved credentials: {str(e)}")

    def _auto_connect_saved_instances(self) -> None:
        """Automatically connect saved MT5 instances after startup if enabled."""
        try:
            self.config.set("ui.auto_connect_on_startup", self.auto_connect_var.get())

            if not self.auto_connect_var.get():
                return

            maven_saved = self.credentials_vault.get_account("dashboard_maven_login") or {}
            hedge_saved = self.credentials_vault.get_account("dashboard_hedge_login") or {}

            if maven_saved.get("account_number") and maven_saved.get("password") and maven_saved.get("server"):
                self._connect_instance(
                    instance_type=MT5InstanceType.MAVEN_FLEET,
                    terminal_path=maven_saved.get("terminal_path", self.maven_terminal_var.get()).strip(),
                    account_text=str(maven_saved.get("account_number", "")).strip(),
                    password=maven_saved.get("password", ""),
                    server=maven_saved.get("server", "").strip(),
                    status_label=self.maven_login_card._status_label,  # type: ignore[attr-defined]
                    success_prefix="Maven",
                    remember=True,
                    credential_id="dashboard_maven_login"
                )

            if hedge_saved.get("account_number") and hedge_saved.get("password") and hedge_saved.get("server"):
                self._connect_instance(
                    instance_type=MT5InstanceType.HEDGE_ACCOUNT,
                    terminal_path=hedge_saved.get("terminal_path", self.hedge_terminal_var.get()).strip(),
                    account_text=str(hedge_saved.get("account_number", "")).strip(),
                    password=hedge_saved.get("password", ""),
                    server=hedge_saved.get("server", "").strip(),
                    status_label=self.hedge_login_card._status_label,  # type: ignore[attr-defined]
                    success_prefix="Hedge",
                    remember=True,
                    credential_id="dashboard_hedge_login"
                )
        except Exception as e:
            self.logger.debug(f"Auto-connect failed: {str(e)}")

    def _persist_credentials(
        self,
        account_id: str,
        account: int,
        password: str,
        server: str,
        terminal_path: str,
        remember: bool
    ) -> None:
        """Persist login credentials and terminal path when requested."""
        if not remember:
            return

        try:
            self.credentials_vault.add_account(
                account_id,
                {
                    "account_number": account,
                    "password": password,
                    "server": server,
                    "terminal_path": terminal_path
                }
            )
        except Exception as e:
            self.logger.debug(f"Failed to persist credentials for {account_id}: {str(e)}")

    def _connect_maven(self) -> None:
        """Connect and log in the Maven MT5 instance."""
        self._connect_instance(
            instance_type=MT5InstanceType.MAVEN_FLEET,
            terminal_path=self.maven_terminal_var.get().strip(),
            account_text=self.maven_account_var.get().strip(),
            password=self.maven_password_var.get(),
            server=self.maven_server_var.get().strip(),
            status_label=self.maven_login_card._status_label,  # type: ignore[attr-defined]
            success_prefix="Maven",
            remember=self.maven_remember_var.get(),
            credential_id="dashboard_maven_login"
        )

    def _connect_hedge(self) -> None:
        """Connect and log in the hedge MT5 instance."""
        self._connect_instance(
            instance_type=MT5InstanceType.HEDGE_ACCOUNT,
            terminal_path=self.hedge_terminal_var.get().strip(),
            account_text=self.hedge_account_var.get().strip(),
            password=self.hedge_password_var.get(),
            server=self.hedge_server_var.get().strip(),
            status_label=self.hedge_login_card._status_label,  # type: ignore[attr-defined]
            success_prefix="Hedge",
            remember=self.hedge_remember_var.get(),
            credential_id="dashboard_hedge_login"
        )

    def _connect_instance(
        self,
        instance_type: MT5InstanceType,
        terminal_path: str,
        account_text: str,
        password: str,
        server: str,
        status_label,
        success_prefix: str,
        remember: bool,
        credential_id: str
    ) -> None:
        """Shared connect/login flow for both MT5 instances."""
        if not terminal_path:
            self._set_login_status(status_label, f"{success_prefix} terminal path required", "#ff8800")
            return

        if not account_text.isdigit():
            self._set_login_status(status_label, f"{success_prefix} account must be numeric", "#ff0000")
            return

        if not password or not server:
            self._set_login_status(status_label, f"{success_prefix} password and server required", "#ff0000")
            return

        account = int(account_text)

        if instance_type == MT5InstanceType.MAVEN_FLEET:
            initialized = self.system.initialize_maven_instance(terminal_path)
            login_ok = initialized and self.system.login_maven_account(account, password, server)
        else:
            initialized = self.system.initialize_hedge_instance(terminal_path)
            login_ok = initialized and self.system.login_hedge_account(account, password, server)

        if login_ok:
            self._set_login_status(status_label, f"{success_prefix} connected", "#00ff88")
            self._persist_credentials(credential_id, account, password, server, terminal_path, remember)

            if instance_type == MT5InstanceType.MAVEN_FLEET:
                self.config.set("mt5.maven_terminal_path", terminal_path)
            else:
                self.config.set("mt5.hedge_terminal_path", terminal_path)

            self._refresh_connection_status()
        else:
            self._set_login_status(status_label, f"{success_prefix} login failed", "#ff0000")

    def _set_login_status(self, label, text: str, color: str) -> None:
        """Update a login status label safely."""
        try:
            label.configure(text=text, text_color=color)
        except Exception:
            pass

    def _refresh_connection_status(self) -> None:
        """Refresh header status indicators from current MT5 state."""
        try:
            maven_status = self.system.mt5_manager.get_status(MT5InstanceType.MAVEN_FLEET)
            hedge_status = self.system.mt5_manager.get_status(MT5InstanceType.HEDGE_ACCOUNT)

            self.maven_status.set_status(maven_status.get("state", ConnectionState.DISCONNECTED.value))
            self.hedge_status.set_status(hedge_status.get("state", ConnectionState.DISCONNECTED.value))
            # If connected, fetch account info and display balance/account
            try:
                if maven_status.get("state") == ConnectionState.CONNECTED.value:
                    acc = self.system.mt5_manager.get_account_info(MT5InstanceType.MAVEN_FLEET) or {}
                    login = acc.get("login") or acc.get("account") or acc.get("account_number") or "-"
                    bal = acc.get("balance")
                    curr = acc.get("currency", "")
                    bal_text = f"{float(bal):,.2f} {curr}" if bal is not None else "-"
                    try:
                        self.maven_login_status_label.configure(text=f"Maven: {login} | {bal_text}", text_color="#00ff88")
                    except Exception:
                        pass
                    try:
                        self.maven_login_card._status_label.configure(text=f"Acct {login} | Balance: {bal_text}", text_color="#00ff88")
                    except Exception:
                        pass
                else:
                    try:
                        self.maven_login_status_label.configure(text="Maven: disconnected", text_color="#888888")
                    except Exception:
                        pass

                if hedge_status.get("state") == ConnectionState.CONNECTED.value:
                    acc = self.system.mt5_manager.get_account_info(MT5InstanceType.HEDGE_ACCOUNT) or {}
                    login = acc.get("login") or acc.get("account") or acc.get("account_number") or "-"
                    bal = acc.get("balance")
                    curr = acc.get("currency", "")
                    bal_text = f"{float(bal):,.2f} {curr}" if bal is not None else "-"
                    try:
                        self.hedge_login_card._status_label.configure(text=f"Acct {login} | Balance: {bal_text}", text_color="#00ff88")
                    except Exception:
                        pass
                    try:
                        self.hedge_login_status = getattr(self, "hedge_login_status_label", None)
                        if self.hedge_login_status:
                            self.hedge_login_status.configure(text=f"Hedge: {login} | {bal_text}", text_color="#00ff88")
                    except Exception:
                        pass
                else:
                    try:
                        self.hedge_login_card._status_label.configure(text="Disconnected", text_color="#888888")
                    except Exception:
                        pass
            except Exception:
                # Non-fatal: continue with status dots only
                pass
        except Exception as e:
            self.logger.debug(f"Status refresh error: {str(e)}")
    
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
            tp, sl = self.trading_controls.get_tp_sl()
            asyncio.run(self._execute_buy(tp, sl))
        elif command == "sell":
            tp, sl = self.trading_controls.get_tp_sl()
            asyncio.run(self._execute_sell(tp, sl))
        elif command == "close_all":
            asyncio.run(self._close_all())
        elif command == "toggle_hedge":
            self.system.hedge_enabled = not self.system.hedge_enabled
        elif command == "toggle_recovery":
            self.system.auto_recovery_enabled = not self.system.auto_recovery_enabled
        elif command == "calc_recovery":
            # Calculate recovery estimate and update controls
            try:
                lot, target = self.system.get_recovery_target()
            except Exception:
                lot, target = (0.0, 0.0)

            try:
                self.trading_controls.set_recovery_estimate(lot, target)
            except Exception:
                pass
    
    async def _execute_buy(self, tp_pips: float = None, sl_pips: float = None) -> None:
        """Execute BUY order"""
        lot_size = self.trading_controls.get_lot_size()
        symbol = self.trading_controls.get_symbol()
        
        success, results = await self.system.execute_buy_order(symbol, lot_size, tp_pips=tp_pips, sl_pips=sl_pips)
        
        if success:
            self.logger.info(f"BUY executed: {results.get('success_count')} accounts")
        else:
            self.logger.error(f"BUY failed: {results.get('error', 'Unknown error')}")
    
    async def _execute_sell(self, tp_pips: float = None, sl_pips: float = None) -> None:
        """Execute SELL order"""
        lot_size = self.trading_controls.get_lot_size()
        symbol = self.trading_controls.get_symbol()
        
        success, results = await self.system.execute_sell_order(symbol, lot_size, tp_pips=tp_pips, sl_pips=sl_pips)
        
        if success:
            self.logger.info(f"SELL executed: {results.get('success_count')} accounts")
        else:
            self.logger.error(f"SELL failed: {results.get('error', 'Unknown error')}")
    
    async def _close_all(self) -> None:
        """Emergency close all positions"""
        symbol = self.trading_controls.get_symbol()
        results = await self.system.close_all_emergency()
        self.logger.info(f"Emergency close for {symbol}: {results.get('closed_count', 0)} positions closed")
    
    def _start_update_loop(self) -> None:
        """Start background update thread"""
        def update_loop():
            while self.is_running:
                try:
                    # Update market data
                    current_symbol = self.trading_controls.get_symbol()
                    self.market_feed.set_symbol(current_symbol)
                    market_data = self.system.get_market_data(current_symbol)
                    if market_data:
                        self.market_feed.update_data(market_data)
                    
                    # Update status indicators
                    self._refresh_connection_status()
                    
                    # Update account grid
                    self.account_grid.refresh_accounts(self.system.mt5_manager)
                    
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
