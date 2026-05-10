"""
Main Dashboard UI
Professional SaaS-style trading dashboard with CustomTkinter
"""

import customtkinter as ctk
from typing import Optional, Dict, Any, Callable
import asyncio
import csv
import json
import threading
from datetime import datetime
from pathlib import Path
from app.core.orchestrator import get_system
from app.mt5_bridge.connection_manager import MT5InstanceType, ConnectionState
from app.utils.config import get_config
from app.ui.components import (
    MarketFeedWidget, AccountHealthWidget, StatusIndicatorWidget,
    TradingControlsWidget, AccountGridWidget, ChallengeConfigWidget
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
        self.current_risk_mode = "balanced"
        self.ledger_days_var = ctk.StringVar(value="30")
        self.ledger_account_var = ctk.StringVar(value="")
        self.ledger_status_var = ctk.StringVar(value="all")
        self.ledger_action_var = ctk.StringVar(value="all")
        self.ledger_source_var = ctk.StringVar(value="all")
        self.ledger_export_status_var = ctk.StringVar(value="")
        
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
        self.main_container.grid_rowconfigure(3, weight=0)
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

        # === BOTTOM ANALYTICS / LEDGER PANEL ===
        self._create_ledger_panel(self.main_container)

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
                self.main_container.grid_rowconfigure(3, weight=0)
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

    def _create_ledger_panel(self, parent) -> None:
        """Create bottom-wide recovery ledger panel."""
        self.ledger_panel = ctk.CTkFrame(parent, fg_color="#111111")
        self.ledger_panel.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.ledger_panel.grid_columnconfigure(0, weight=1)
        self.ledger_panel.grid_rowconfigure(1, weight=0)
        self.ledger_panel.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self.ledger_panel, fg_color="#111111")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="RECOVERY LEDGER",
            font=("Arial", 12, "bold"),
            text_color="#00ffcc"
        ).grid(row=0, column=0, sticky="w")

        self.ledger_summary_label = ctk.CTkLabel(
            header,
            text="No recovery activity yet",
            font=("Arial", 10),
            text_color="#888888"
        )
        self.ledger_summary_label.grid(row=0, column=1, sticky="e")

        filter_bar = ctk.CTkFrame(self.ledger_panel, fg_color="#111111")
        filter_bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        for column_index in range(10):
            filter_bar.grid_columnconfigure(column_index, weight=1)

        ctk.CTkLabel(filter_bar, text="Days", text_color="#888", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=(0, 4))
        ctk.CTkEntry(filter_bar, textvariable=self.ledger_days_var, width=60).grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(filter_bar, text="Account", text_color="#888", font=("Arial", 10)).grid(row=0, column=2, sticky="w", padx=(0, 4))
        ctk.CTkEntry(filter_bar, textvariable=self.ledger_account_var, width=90).grid(row=0, column=3, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(filter_bar, text="Status", text_color="#888", font=("Arial", 10)).grid(row=0, column=4, sticky="w", padx=(0, 4))
        ctk.CTkOptionMenu(filter_bar, variable=self.ledger_status_var, values=["all", "pending", "partial", "completed"]).grid(row=0, column=5, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(filter_bar, text="Action", text_color="#888", font=("Arial", 10)).grid(row=0, column=6, sticky="w", padx=(0, 4))
        ctk.CTkOptionMenu(filter_bar, variable=self.ledger_action_var, values=["all", "loss_recorded", "recovered"]).grid(row=0, column=7, sticky="ew", padx=(0, 8))

        ctk.CTkLabel(filter_bar, text="Source", text_color="#888", font=("Arial", 10)).grid(row=0, column=8, sticky="w", padx=(0, 4))
        ctk.CTkOptionMenu(filter_bar, variable=self.ledger_source_var, values=["all", "manual", "auto"]).grid(row=0, column=9, sticky="ew", padx=(0, 8))

        ctk.CTkButton(filter_bar, text="Refresh", width=90, command=self._refresh_ledger_display).grid(row=0, column=10, sticky="e", padx=(0, 6))
        ctk.CTkButton(filter_bar, text="Export CSV", width=100, command=self._export_ledger_display).grid(row=0, column=11, sticky="e")

        self.recovery_ledger_box = ctk.CTkTextbox(
            self.ledger_panel,
            height=140,
            fg_color="#0d0d0d",
            text_color="#d8e2f0"
        )
        self.recovery_ledger_box.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.recovery_ledger_box.configure(state="disabled")
        self._refresh_ledger_display()

    def _append_ledger_line(self, line: str) -> None:
        """Append a new line to the visible recovery ledger."""
        try:
            self.recovery_ledger_box.configure(state="normal")
            self.recovery_ledger_box.insert("end", line.rstrip() + "\n")
            self.recovery_ledger_box.see("end")
            self.recovery_ledger_box.configure(state="disabled")
        except Exception:
            pass

    def _refresh_ledger_display(self) -> None:
        """Reload recent ledger entries into the UI."""
        try:
            entries = self._get_filtered_ledger_entries()

            def parse_time(value: str) -> Optional[datetime]:
                try:
                    return datetime.fromisoformat(value)
                except Exception:
                    return None

            def get_source(row: Dict[str, Any]) -> str:
                notes = str(row.get("notes", "") or "").lower()
                if "source=auto" in notes:
                    return "auto"
                if "source=manual" in notes:
                    return "manual"
                return "manual"

            days_raw = self.ledger_days_var.get().strip()
            days = int(days_raw) if days_raw.isdigit() and int(days_raw) > 0 else 30
            cutoff = datetime.now().timestamp() - (days * 86400)

            account_filter = self.ledger_account_var.get().strip()
            status_filter = self.ledger_status_var.get().strip().lower()
            action_filter = self.ledger_action_var.get().strip().lower()
            source_filter = self.ledger_source_var.get().strip().lower()

            filtered_entries: list[Dict[str, Any]] = []
            for row in entries:
                row_time = parse_time(str(row.get("timestamp", "")))
                if row_time is None or row_time.timestamp() < cutoff:
                    continue

                if account_filter and str(row.get("account_number", "")).strip() != account_filter:
                    continue

                if status_filter != "all" and str(row.get("status", "")).strip().lower() != status_filter:
                    continue

                if action_filter != "all" and str(row.get("action", "")).strip().lower() != action_filter:
                    continue

                if source_filter != "all" and get_source(row) != source_filter:
                    continue

                filtered_entries.append(row)

            self.recovery_ledger_box.configure(state="normal")
            self.recovery_ledger_box.delete("1.0", "end")

            if not filtered_entries:
                self.recovery_ledger_box.insert("end", "No recovery ledger entries match the current filters.\n")
                self.ledger_summary_label.configure(text="Waiting for matching recovery activity...")
            else:
                for row in filtered_entries:
                    source = get_source(row)
                    line = (
                        f"[{row.get('timestamp', '')}] {row.get('action', '')} | "
                        f"Account {row.get('account_number', '')} | "
                        f"Loss ${float(row.get('hedge_loss', 0.0)):.2f} | "
                        f"Target ${float(row.get('total_target', 0.0)):.2f} | "
                        f"Status {row.get('status', '')} | Source {source}"
                    )
                    self.recovery_ledger_box.insert("end", line + "\n")

                last = filtered_entries[-1]
                self.ledger_summary_label.configure(
                    text=f"Latest: {last.get('action', '')} | ${float(last.get('hedge_loss', 0.0)):.2f} hedge loss | {get_source(last)}"
                )

            self.recovery_ledger_box.configure(state="disabled")
        except Exception as e:
            self.logger.debug(f"Ledger refresh failed: {str(e)}")

    def _get_filtered_ledger_entries(self) -> list[Dict[str, Any]]:
        """Return ledger entries that match the active UI filters."""
        entries = self.system.recovery_engine.get_recent_ledger_entries(limit=200)

        def parse_time(value: str) -> Optional[datetime]:
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None

        def get_source(row: Dict[str, Any]) -> str:
            notes = str(row.get("notes", "") or "").lower()
            if "source=auto" in notes:
                return "auto"
            return "manual"

        days_raw = self.ledger_days_var.get().strip()
        days = int(days_raw) if days_raw.isdigit() and int(days_raw) > 0 else 30
        cutoff = datetime.now().timestamp() - (days * 86400)

        account_filter = self.ledger_account_var.get().strip()
        status_filter = self.ledger_status_var.get().strip().lower()
        action_filter = self.ledger_action_var.get().strip().lower()
        source_filter = self.ledger_source_var.get().strip().lower()

        filtered_entries: list[Dict[str, Any]] = []
        for row in entries:
            row_time = parse_time(str(row.get("timestamp", "")))
            if row_time is None or row_time.timestamp() < cutoff:
                continue

            if account_filter and str(row.get("account_number", "")).strip() != account_filter:
                continue

            if status_filter != "all" and str(row.get("status", "")).strip().lower() != status_filter:
                continue

            if action_filter != "all" and str(row.get("action", "")).strip().lower() != action_filter:
                continue

            if source_filter != "all" and get_source(row) != source_filter:
                continue

            filtered_entries.append(row)

        return filtered_entries

    def _export_ledger_display(self) -> None:
        """Export the currently filtered ledger view to CSV and JSON."""
        try:
            entries = self._get_filtered_ledger_entries()
            export_dir = Path("data") / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = export_dir / f"recovery_ledger_{stamp}.csv"
            json_path = export_dir / f"recovery_ledger_{stamp}.json"

            fieldnames = [
                "timestamp",
                "cycle_id",
                "account_number",
                "action",
                "hedge_loss",
                "challenge_fee",
                "total_target",
                "hedge_lot_size",
                "status",
                "notes",
            ]

            with open(csv_path, "w", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                for row in entries:
                    writer.writerow({field: row.get(field, "") for field in fieldnames})

            with open(json_path, "w") as json_file:
                json.dump(entries, json_file, indent=2)

            self.ledger_summary_label.configure(text=f"Exported {len(entries)} rows")
            self.ledger_export_status_var.set(f"Saved to {csv_path} and {json_path}")
            self.logger.info(f"Recovery ledger exported: {csv_path} | {json_path}")
        except Exception as e:
            self.logger.debug(f"Ledger export failed: {str(e)}")
            self.ledger_summary_label.configure(text="Export failed")
    
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

        # Supplemental telemetry for hedge intelligence
        self.engine_status_label = ctk.CTkLabel(
            header,
            text="Engine: Ready",
            font=("Arial", 10, "bold"),
            text_color="#00bcd4"
        )
        self.engine_status_label.pack(side="right", padx=8)

        self.recovery_deficit_label = ctk.CTkLabel(
            header,
            text="Recovery Deficit: $0.00",
            font=("Arial", 10),
            text_color="#8ecae6"
        )
        self.recovery_deficit_label.pack(side="right", padx=8)

        self.risk_mode_label = ctk.CTkLabel(
            header,
            text="Risk Mode: BALANCED",
            font=("Arial", 10, "bold"),
            text_color="#90ee90"
        )
        self.risk_mode_label.pack(side="right", padx=8)

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
        left_panel.grid_rowconfigure(3, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        
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
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(right_panel, fg_color="#0a0a0a")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        
        # Trading Controls
        controls_label = ctk.CTkLabel(
            scroll,
            text="TRADING CONTROLS",
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        )
        controls_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        self.trading_controls = TradingControlsWidget(scroll, self._on_trade_command)
        self.trading_controls.grid(row=1, column=0, sticky="nsew")

        challenge_label = ctk.CTkLabel(
            scroll,
            text="PROP FIRM RULES ENGINE",
            font=("Arial", 12, "bold"),
            text_color="#00ffcc"
        )
        challenge_label.grid(row=2, column=0, sticky="ew", pady=(14, 8))

        self.challenge_config = ChallengeConfigWidget(scroll, self._on_challenge_action)
        self.challenge_config.grid(row=3, column=0, sticky="nsew")
        
        # Account Grid
        accounts_label = ctk.CTkLabel(
            scroll,
            text="MAVEN FLEET",
            font=("Arial", 12, "bold"),
            text_color="#00ff88"
        )
        accounts_label.grid(row=4, column=0, sticky="ew", pady=(20, 10))
        
        self.account_grid = AccountGridWidget(scroll, self.system.account_manager)
        self.account_grid.grid(row=5, column=0, sticky="nsew")
        
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

    def _on_challenge_action(self, action: str, payload: Dict[str, Any]) -> None:
        """Handle Prop Firm Rules Engine actions from the dashboard panel."""
        try:
            if action == "apply_challenge_rules":
                summary = self.system.configure_prop_challenge(payload)
                self.current_risk_mode = str(payload.get("recovery_mode", "balanced")).upper()
                self.risk_mode_label.configure(text=f"Risk Mode: {self.current_risk_mode}")
                self.engine_status_label.configure(text="Engine: Rules Applied", text_color="#00ffcc")
                self.recovery_deficit_label.configure(
                    text=f"Daily DD ${summary.get('max_daily_loss_allowed', 0.0):.2f} | Target ${summary.get('target_dollar_amount', 0.0):.2f}"
                )
            elif action == "compute_dynamic_plan":
                result = self.system.calculate_dynamic_hedge_plan(payload)
                self.challenge_config.update_output(result)
                self.trading_controls.lot_var.set(f"{result.get('funded_lot_size', 0.1):.2f}")
                self.trading_controls.set_recovery_estimate(
                    float(result.get("hedge_lot_size", 0.0)),
                    float(result.get("recovery_target", 0.0)),
                )
                self.recovery_deficit_label.configure(text=f"Recovery Deficit: ${result.get('recovery_target', 0.0):.2f}")
                self.engine_status_label.configure(text="Engine: Plan Updated", text_color="#00ff88")
            elif action == "save_template":
                name = str(payload.get("template_name", "")).strip()
                if name:
                    self.system.configure_prop_challenge(payload)
                    if self.system.save_challenge_template(name):
                        self.engine_status_label.configure(text=f"Template Saved: {name}", text_color="#90ee90")
            elif action == "record_hedge_loss":
                hedge_loss = float(payload.get("realized_hedge_loss", 0.0))
                if hedge_loss > 0:
                    active_accounts = self.system.account_manager.get_active_accounts()
                    account_number = active_accounts[0].account_number if active_accounts else 0
                    cycle_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                    fee = float(payload.get("purchase_fee", 0.0))
                    ok = self.system.record_hedge_loss(cycle_id, account_number, hedge_loss, fee)
                    if ok:
                        self.engine_status_label.configure(text=f"Loss Recorded: ${hedge_loss:.2f}", text_color="#ffcc66")
                        self.recovery_deficit_label.configure(text=f"Recovery Deficit Updated (+${hedge_loss:.2f})")
                        self._append_ledger_line(
                            f"[{datetime.now().isoformat(timespec='seconds')}] loss_recorded | Account {account_number} | Loss ${hedge_loss:.2f} | Target ${hedge_loss + fee:.2f} | Status pending"
                        )
            elif action == "auto_fill_latest_hedge_loss":
                latest_pnl = self.system.get_latest_hedge_trade_pnl()
                if latest_pnl is not None:
                    hedge_loss = abs(float(latest_pnl)) if float(latest_pnl) < 0 else 0.0
                    self.challenge_config.realized_hedge_loss.set(f"{hedge_loss:.2f}")
                    if hedge_loss > 0:
                        self.engine_status_label.configure(text=f"Latest Hedge Loss Loaded: ${hedge_loss:.2f}", text_color="#ffcc66")
                    else:
                        self.engine_status_label.configure(text=f"Latest Hedge P/L was positive: ${float(latest_pnl):.2f}", text_color="#90ee90")
                else:
                    self.engine_status_label.configure(text="No hedge trade result found", text_color="#ffaa00")
        except Exception as e:
            self.logger.debug(f"Challenge action error: {str(e)}")
            self.engine_status_label.configure(text="Engine: Error", text_color="#ff5555")
    
    async def _execute_buy(self, tp_pips: float = None, sl_pips: float = None) -> None:
        """Execute BUY order"""
        lot_size = self.trading_controls.get_lot_size()
        symbol = self.trading_controls.get_symbol()
        mode = self.trading_controls.get_execution_mode()
        use_hedge = mode in ["Hedge + Funded", "Hedge Only"]
        use_maven = mode in ["Hedge + Funded", "Funded Only"]

        success, results = await self.system.execute_buy_order(
            symbol,
            lot_size,
            use_hedge=use_hedge,
            use_maven=use_maven,
            tp_pips=tp_pips,
            sl_pips=sl_pips,
        )
        
        if success:
            self.logger.info(f"BUY executed: {results.get('success_count')} accounts")
        else:
            self.logger.error(f"BUY failed: {results.get('error', 'Unknown error')}")
    
    async def _execute_sell(self, tp_pips: float = None, sl_pips: float = None) -> None:
        """Execute SELL order"""
        lot_size = self.trading_controls.get_lot_size()
        symbol = self.trading_controls.get_symbol()
        mode = self.trading_controls.get_execution_mode()
        use_hedge = mode in ["Hedge + Funded", "Hedge Only"]
        use_maven = mode in ["Hedge + Funded", "Funded Only"]

        success, results = await self.system.execute_sell_order(
            symbol,
            lot_size,
            use_hedge=use_hedge,
            use_maven=use_maven,
            tp_pips=tp_pips,
            sl_pips=sl_pips,
        )
        
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
                    self._refresh_ledger_display()

                    # Auto-record any newly closed losing hedge trade once
                    auto_record = self.system.auto_record_latest_hedge_loss()
                    if auto_record.get("recorded"):
                        loss_value = float(auto_record.get("hedge_loss", 0.0))
                        self.challenge_config.realized_hedge_loss.set(f"{loss_value:.2f}")
                        self.engine_status_label.configure(
                            text=f"Auto-recorded Hedge Loss: ${loss_value:.2f}",
                            text_color="#ffcc66"
                        )
                        self.recovery_deficit_label.configure(text=f"Recovery Deficit Updated (+${loss_value:.2f})")
                        self._append_ledger_line(
                            f"[{datetime.now().isoformat(timespec='seconds')}] auto_recorded | Ticket {auto_record.get('ticket')} | Account {auto_record.get('account_number')} | Loss ${loss_value:.2f} | Symbol {auto_record.get('symbol', '')}"
                        )

                    # Auto-protection based on drawdown usage (90%+)
                    active_accounts = self.system.account_manager.get_active_accounts()
                    primary_account = active_accounts[0].account_number if active_accounts else None
                    if primary_account:
                        guard = self.system.get_drawdown_guardrail(primary_account)
                        if guard.get("is_available"):
                            usage = float(guard.get("drawdown_usage_pct", 0.0))
                            if guard.get("protection_triggered"):
                                self.trading_controls.set_trading_enabled(False)
                                self.engine_status_label.configure(text=f"Engine: Protection ON ({usage:.1f}%)", text_color="#ffb703")
                            else:
                                self.trading_controls.set_trading_enabled(True)
                    
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
