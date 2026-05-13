"""
Maven Fleet Account Manager
Dynamic account matrix supporting 5+ slots with secure credential storage
"""

import json
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from app.utils.logger import get_logger
from app.utils.crypto import CredentialVault
from app.utils.constants import MAVEN_ACCOUNT_SLOTS, MAVEN_PHASE_1, MAVEN_PHASE_2


class TradingPhase(Enum):
    """Maven phase designation"""
    PHASE_1 = MAVEN_PHASE_1
    PHASE_2 = MAVEN_PHASE_2


@dataclass
class MavenAccount:
    """Represents a Maven prop firm trading account"""
    slot_id: int
    account_number: int
    password: str
    server: str
    phase: TradingPhase
    is_active: bool = False
    display_name: str = ""
    created_at: str = field(default_factory=lambda: str(Path.stat(Path.cwd())))
    last_login: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "account_number": self.account_number,
            "server": self.server,
            "phase": self.phase.value,
            "is_active": self.is_active,
            "display_name": self.display_name,
            "created_at": self.created_at,
            "last_login": self.last_login
        }


class AccountManager:
    """Manages Maven account fleet with encryption and persistence"""
    
    def __init__(self, accounts_file: str = "data/accounts.json", 
                 credentials_file: str = "data/credentials.enc"):
        self.logger = get_logger()
        self.accounts_file = Path(accounts_file)
        self.accounts_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.vault = CredentialVault(credentials_file)
        self.accounts: Dict[int, MavenAccount] = {}
        self.selected_account_slot: Optional[int] = None
        
        self._load_accounts()
    
    def _load_accounts(self) -> None:
        """Load accounts from persistent storage"""
        try:
            if self.accounts_file.exists():
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                    for slot_id, account_data in data.items():
                        phase = TradingPhase(account_data['phase'])
                        self.accounts[int(slot_id)] = MavenAccount(
                            slot_id=int(slot_id),
                            account_number=account_data['account_number'],
                            password="",  # Never persist passwords in JSON
                            server=account_data['server'],
                            phase=phase,
                            is_active=account_data.get('is_active', False),
                            display_name=account_data.get('display_name', ''),
                            created_at=account_data.get('created_at', ''),
                            last_login=account_data.get('last_login')
                        )
            else:
                # Initialize empty slots
                for i in range(1, MAVEN_ACCOUNT_SLOTS + 1):
                    self.accounts[i] = None
            
            self.logger.info(f"Loaded {len([a for a in self.accounts.values() if a])} accounts")
        except Exception as e:
            self.logger.log_error(e, "Failed to load accounts")
    
    def _save_accounts(self) -> None:
        """Persist accounts (without passwords) to storage"""
        try:
            data = {}
            for slot_id, account in self.accounts.items():
                if account:
                    data[str(slot_id)] = account.to_dict()
            
            with open(self.accounts_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug("Accounts saved to persistent storage")
        except Exception as e:
            self.logger.log_error(e, "Failed to save accounts")
    
    def add_account(self, slot_id: int, account_number: int, password: str, 
                   server: str, phase: TradingPhase, display_name: str = "") -> bool:
        """
        Register new Maven account in specified slot
        Credentials stored encrypted, metadata in JSON
        """
        if slot_id < 1 or slot_id > MAVEN_ACCOUNT_SLOTS:
            self.logger.error(f"Invalid slot ID: {slot_id}")
            return False
        
        try:
            # Create account object
            account = MavenAccount(
                slot_id=slot_id,
                account_number=account_number,
                password=password,
                server=server,
                phase=phase,
                display_name=display_name or f"Account {account_number}"
            )
            
            # Store in vault
            self.vault.add_account(
                f"maven_slot_{slot_id}",
                {
                    "account_number": account_number,
                    "password": password,
                    "server": server
                }
            )
            
            # Store metadata
            self.accounts[slot_id] = account
            self._save_accounts()
            
            self.logger.info(f"Added account to slot {slot_id}: {account_number}")
            return True
        except Exception as e:
            self.logger.log_error(e, f"Failed to add account to slot {slot_id}")
            return False
    
    def get_account(self, slot_id: int) -> Optional[MavenAccount]:
        """Retrieve account metadata for slot"""
        return self.accounts.get(slot_id)
    
    def get_account_credentials(self, slot_id: int) -> Optional[Dict[str, str]]:
        """
        Retrieve decrypted credentials for account
        Should only be called when needed for login
        """
        try:
            creds = self.vault.get_account(f"maven_slot_{slot_id}")
            return creds
        except Exception as e:
            self.logger.log_error(e, f"Failed to retrieve credentials for slot {slot_id}")
            return None
    
    def set_account_active(self, slot_id: int, active: bool) -> bool:
        """Toggle account active status for next trade execution"""
        try:
            account = self.accounts.get(slot_id)
            if not account:
                return False
            
            account.is_active = active
            self._save_accounts()
            
            status = "active" if active else "inactive"
            self.logger.info(f"Account slot {slot_id} set to {status}")
            return True
        except Exception as e:
            self.logger.log_error(e, f"Failed to set account active status")
            return False
    
    def set_account_phase(self, slot_id: int, phase: TradingPhase) -> bool:
        """Update trading phase for account"""
        try:
            account = self.accounts.get(slot_id)
            if not account:
                return False
            
            account.phase = phase
            self._save_accounts()
            
            self.logger.info(f"Account slot {slot_id} phase set to {phase.value}")
            return True
        except Exception as e:
            self.logger.log_error(e, f"Failed to set account phase")
            return False

    def set_account_phase_by_text(self, slot_id: int, phase_text: str) -> bool:
        """Update account phase from UI text (Phase 1 / Phase 2)."""
        normalized = str(phase_text).strip().lower()
        if normalized == "phase 2":
            return self.set_account_phase(slot_id, TradingPhase.PHASE_2)
        return self.set_account_phase(slot_id, TradingPhase.PHASE_1)

    def get_account_phase(self, slot_id: int) -> TradingPhase:
        """Return slot phase, defaulting to Phase 1 when missing."""
        account = self.accounts.get(slot_id)
        if account and account.phase:
            return account.phase
        return TradingPhase.PHASE_1

    def get_phase_profit_target_pct(self, phase: TradingPhase) -> float:
        """Return challenge target percent by phase."""
        return 5.0 if phase == TradingPhase.PHASE_2 else 8.0

    def get_phase_recovery_surplus(self, phase: TradingPhase) -> float:
        """Return default recovery surplus by phase.

        Phase 1 uses higher surplus to cover progression risk to Phase 2.
        Phase 2 uses lower surplus due to shorter funded path.
        """
        return 45.0 if phase == TradingPhase.PHASE_2 else 60.0
    
    def get_active_accounts(self) -> List[MavenAccount]:
        """Get list of accounts marked active for next execution"""
        return [acc for acc in self.accounts.values() if acc and acc.is_active]
    
    def get_accounts_by_phase(self, phase: TradingPhase) -> List[MavenAccount]:
        """Get accounts filtered by trading phase"""
        return [acc for acc in self.accounts.values() if acc and acc.phase == phase]
    
    def select_account(self, slot_id: int) -> bool:
        """Select account for current interaction"""
        account = self.accounts.get(slot_id)
        if not account:
            return False
        
        self.selected_account_slot = slot_id
        self.logger.debug(f"Selected account slot {slot_id}")
        return True
    
    def get_selected_account(self) -> Optional[MavenAccount]:
        """Get currently selected account"""
        if self.selected_account_slot is None:
            return None
        return self.accounts.get(self.selected_account_slot)
    
    def list_accounts(self) -> List[Dict[str, Any]]:
        """List all configured accounts with metadata"""
        accounts = []
        for slot_id, account in sorted(self.accounts.items()):
            if account:
                accounts.append({
                    "slot_id": slot_id,
                    "account_number": account.account_number,
                    "phase": account.phase.value,
                    "is_active": account.is_active,
                    "display_name": account.display_name,
                    "server": account.server
                })
        return accounts
    
    def remove_account(self, slot_id: int) -> bool:
        """Remove account from slot"""
        try:
            self.accounts[slot_id] = None
            self._save_accounts()
            self.logger.info(f"Removed account from slot {slot_id}")
            return True
        except Exception as e:
            self.logger.log_error(e, f"Failed to remove account")
            return False
    
    def clear_all_active(self) -> None:
        """Clear all active account selections"""
        for account in self.accounts.values():
            if account:
                account.is_active = False
        self._save_accounts()
        self.logger.debug("Cleared all account active selections")
    
    def detect_phase_transitions(self) -> Dict[int, Tuple[TradingPhase, TradingPhase]]:
        """
        Detect accounts that have transitioned from Phase 1 to Phase 2 (Funded)
        Returns dictionary of {slot_id: (old_phase, new_phase)}
        
        Called periodically to enable automatic Farming Mode when an account
        reaches the Funded stage (Phase 2).
        
        Farming Mode: When an account transitions to Funded, reduce lot sizes to 0.1x
        to maintain consistency requirements and reduce risk.
        """
        transitions = {}
        # This method would be called with updated phase info from MT5
        # For now, it's a template for integration with actual MT5 account checks
        return transitions
    
    def is_farming_mode_enabled(self, slot_id: int) -> bool:
        """
        Check if an account should operate in farming mode
        
        Farming Mode is enabled when:
        1. Account has transitioned from Phase 1 to Phase 2 (Funded)
        2. Account is in profit and meeting consistency requirements
        
        Args:
            slot_id: Account slot to check
        
        Returns:
            True if farming mode should be active, False otherwise
        """
        account = self.accounts.get(slot_id)
        if not account:
            return False
        
        # Farming mode is active when in Phase 2 (Funded)
        is_funded = account.phase == TradingPhase.PHASE_2
        
        if is_funded:
            self.logger.debug(f"[FARMING MODE] Account slot {slot_id} is FUNDED - using 0.1x lot multiplier")
        
        return is_funded
    
    def get_farming_lot_multiplier(self, slot_id: int) -> float:
        """
        Get lot size multiplier for farming mode
        
        Args:
            slot_id: Account slot ID
        
        Returns:
            1.0 (normal) if Phase 1, 0.1 (farming) if Phase 2
        """
        account = self.accounts.get(slot_id)
        if not account:
            return 1.0
        
        if account.phase == TradingPhase.PHASE_2:
            return 0.1  # 0.1x for farming mode
        else:
            return 1.0  # Normal size for Phase 1
    
    def apply_farming_multiplier(self, base_lot_size: float, slot_id: int) -> float:
        """
        Apply farming mode multiplier to lot size if applicable
        
        Args:
            base_lot_size: Original lot size
            slot_id: Account slot ID
        
        Returns:
            Adjusted lot size (0.1x if farming, 1.0x if phase 1)
        """
        multiplier = self.get_farming_lot_multiplier(slot_id)
        adjusted_lot = base_lot_size * multiplier
        
        if multiplier < 1.0:
            self.logger.info(f"[FARMING] Lot adjusted: {base_lot_size:.2f}L × {multiplier} = {adjusted_lot:.2f}L")
        
        return adjusted_lot
