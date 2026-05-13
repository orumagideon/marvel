"""
Session-Based Account Management with Auto-Detection
Handles cTrader/Maven session lifecycle, challenge phase detection, and account balance reading
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from enum import Enum
from datetime import datetime
import asyncio
import json


class ChallengePhase(Enum):
    """Trading challenge phases"""
    CHALLENGE_1 = "Challenge 1"  # 8% target
    CHALLENGE_2 = "Challenge 2"  # 5% target
    FUNDED = "Funded"
    FARMING = "Farming"


class AccountStatus(Enum):
    """Account connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ERROR = "error"


@dataclass
class ChallengePhaseConfig:
    """Configuration for each challenge phase"""
    phase: ChallengePhase
    profit_target_pct: float  # 8% for Phase 1, 5% for Phase 2
    aggressive_hedge_multiplier: float  # 1.3x for Phase 1 (recovery), 1.0x for Phase 2
    lot_size_override: Optional[float] = None  # 0.1x for Farming/Funded
    max_daily_drawdown_pct: float = 5.0
    max_total_drawdown_pct: float = 10.0

    def get_hedge_multiplier(self) -> float:
        """Get hedge multiplier for this phase"""
        if self.lot_size_override:  # Farming/Funded protection
            return self.lot_size_override
        return self.aggressive_hedge_multiplier


@dataclass
class SessionContext:
    """Complete trading session context"""
    session_id: str
    account_id: int
    platform: str  # "ctrader", "mt5"
    account_balance: float = 0.0
    account_size_preset: Optional[str] = None  # "2K", "5K", "10K", "50K"
    challenge_phase: ChallengePhase = ChallengePhase.CHALLENGE_1
    username: Optional[str] = None
    status: AccountStatus = AccountStatus.DISCONNECTED
    selected_symbol: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    hedge_enabled: bool = True
    
    def is_active(self) -> bool:
        return self.status == AccountStatus.AUTHENTICATED
    
    def get_phase_config(self) -> ChallengePhaseConfig:
        """Get configuration for current phase"""
        if self.challenge_phase == ChallengePhase.CHALLENGE_1:
            return ChallengePhaseConfig(
                phase=ChallengePhase.CHALLENGE_1,
                profit_target_pct=8.0,
                aggressive_hedge_multiplier=1.3,  # 1.3x for fee recovery
            )
        elif self.challenge_phase == ChallengePhase.CHALLENGE_2:
            return ChallengePhaseConfig(
                phase=ChallengePhase.CHALLENGE_2,
                profit_target_pct=5.0,
                aggressive_hedge_multiplier=1.0,  # Standard for lower target
            )
        else:  # FUNDED or FARMING
            return ChallengePhaseConfig(
                phase=self.challenge_phase,
                profit_target_pct=0.0,
                aggressive_hedge_multiplier=1.0,
                lot_size_override=0.1,  # Protect with 0.1x lot size
            )


class SessionManager:
    """
    Manages trading session lifecycle
    - Auto-detects Maven/cTrader account balance
    - Determines challenge phase
    - Manages symbol selection
    - Handles account presets
    """

    ACCOUNT_SIZE_PRESETS: Dict[str, float] = {
        "2K": 2000.0,
        "5K": 5000.0,
        "10K": 10000.0,
        "25K": 25000.0,
        "50K": 50000.0,
    }

    def __init__(self, browser_bridge: Optional[Any] = None, mt5_manager: Optional[Any] = None):
        self.browser_bridge = browser_bridge  # cTrader headless bridge
        self.mt5_manager = mt5_manager  # MT5 connection manager
        self.current_session: Optional[SessionContext] = None
        self.session_history: List[SessionContext] = []
        self.latency_log: List[Dict[str, Any]] = []

    def create_session(self, account_id: int, platform: str = "ctrader") -> SessionContext:
        """Create a new trading session"""
        session = SessionContext(
            session_id=f"{account_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            account_id=account_id,
            platform=platform,
            status=AccountStatus.CONNECTING,
        )
        self.current_session = session
        return session

    async def auto_detect_account_balance(self, session: SessionContext) -> bool:
        """
        Auto-detect account balance from cTrader or MT5
        Updates session_context with balance and preset
        Returns True if successful
        """
        try:
            if session.platform == "ctrader" and self.browser_bridge:
                balance = await self.browser_bridge.read_account_balance()
                if balance > 0:
                    session.account_balance = balance
                    session.account_size_preset = self._detect_preset(balance)
                    session.status = AccountStatus.AUTHENTICATED
                    return True
            
            elif session.platform == "mt5" and self.mt5_manager:
                balance = self.mt5_manager.get_account_balance(session.account_id)
                if balance > 0:
                    session.account_balance = balance
                    session.account_size_preset = self._detect_preset(balance)
                    session.status = AccountStatus.AUTHENTICATED
                    return True
        except Exception as e:
            session.status = AccountStatus.ERROR
        
        return False

    async def detect_challenge_phase(self, session: SessionContext) -> ChallengePhase:
        """
        Detect which challenge phase the account is in
        Returns the detected phase
        """
        try:
            if session.platform == "ctrader" and self.browser_bridge:
                phase_info = await self.browser_bridge.read_challenge_phase()
                if phase_info:
                    phase = self._parse_phase(phase_info)
                    session.challenge_phase = phase
                    return phase
        except Exception:
            pass
        
        # Default to Challenge 1 if detection fails
        session.challenge_phase = ChallengePhase.CHALLENGE_1
        return ChallengePhase.CHALLENGE_1

    def _detect_preset(self, balance: float) -> str:
        """Detect account size preset from balance"""
        # Find closest preset
        presets = [(k, v) for k, v in self.ACCOUNT_SIZE_PRESETS.items()]
        closest = min(presets, key=lambda x: abs(x[1] - balance))
        return closest[0]

    def _parse_phase(self, phase_info: Dict[str, Any]) -> ChallengePhase:
        """Parse phase from cTrader/account info"""
        phase_name = phase_info.get("name", "").lower()
        
        if "phase 1" in phase_name or "challenge 1" in phase_name:
            return ChallengePhase.CHALLENGE_1
        elif "phase 2" in phase_name or "challenge 2" in phase_name:
            return ChallengePhase.CHALLENGE_2
        elif "funded" in phase_name:
            return ChallengePhase.FUNDED
        elif "farming" in phase_name:
            return ChallengePhase.FARMING
        
        return ChallengePhase.CHALLENGE_1

    def set_selected_symbol(self, symbol: str) -> None:
        """Set the selected symbol for current session"""
        if self.current_session:
            self.current_session.selected_symbol = symbol
            self.current_session.last_activity = datetime.now()

    def get_selected_symbol(self) -> Optional[str]:
        """Get currently selected symbol"""
        if self.current_session:
            return self.current_session.selected_symbol
        return None

    def validate_symbol_match(self, expected_symbol: str, actual_symbol: Optional[str]) -> bool:
        """
        Validate that selected symbol matches active chart symbol
        Returns False if mismatch (prevents accidental trades)
        """
        return expected_symbol == actual_symbol or actual_symbol is None

    def record_latency(self, server: str, latency_ms: float) -> None:
        """Record latency measurement"""
        self.latency_log.append({
            "timestamp": datetime.now().isoformat(),
            "server": server,
            "latency_ms": latency_ms,
        })
        
        # Trim log to last 100 entries
        if len(self.latency_log) > 100:
            self.latency_log = self.latency_log[-100:]

    def get_average_latency(self, server: str, window_seconds: int = 60) -> float:
        """Get average latency to server in last N seconds"""
        now = datetime.now()
        recent = [
            entry for entry in self.latency_log
            if entry["server"] == server and
            (now - datetime.fromisoformat(entry["timestamp"])).total_seconds() < window_seconds
        ]
        
        if not recent:
            return 0.0
        
        return sum(e["latency_ms"] for e in recent) / len(recent)

    def should_use_vps_mode(self, latency_threshold_ms: float = 200.0) -> bool:
        """
        Determine if VPS-hosted mode should be suggested
        Kenya optimization: if latency exceeds threshold, use VPS
        """
        latency = self.get_average_latency("ctrader", window_seconds=60)
        return latency > latency_threshold_ms

    def end_session(self) -> Optional[SessionContext]:
        """End current session and save to history"""
        if self.current_session:
            self.session_history.append(self.current_session)
            session = self.current_session
            self.current_session = None
            return session
        return None

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.current_session:
            return {"status": "no_active_session"}
        
        session = self.current_session
        phase_config = session.get_phase_config()
        
        return {
            "session_id": session.session_id,
            "account_id": session.account_id,
            "platform": session.platform,
            "account_balance": session.account_balance,
            "account_preset": session.account_size_preset,
            "challenge_phase": session.challenge_phase.value,
            "selected_symbol": session.selected_symbol,
            "status": session.status.value,
            "hedge_multiplier": phase_config.get_hedge_multiplier(),
            "profit_target_pct": phase_config.profit_target_pct,
            "avg_latency_ms": self.get_average_latency("ctrader"),
            "created_at": session.created_at.isoformat(),
            "is_vps_mode_suggested": self.should_use_vps_mode(),
        }
