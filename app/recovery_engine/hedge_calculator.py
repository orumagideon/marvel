"""
Recovery and Hedge Calculation Engine
Intelligent hedge lot sizing for recovery of fees and losses
Persistent ledger tracking for multi-cycle recovery
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from app.utils.logger import get_logger
from app.utils.constants import (
    DEFAULT_DAILY_DRAWDOWN, DEFAULT_DESIRED_SURPLUS, 
    RECOVERY_LOSS_PERSISTENCE, VOLUME_UNIT_PRECISION
)


@dataclass
class RecoveryLedgerEntry:
    """Single recovery ledger entry tracking hedge losses and recoveries"""
    timestamp: str
    cycle_id: str
    account_number: int
    action: str  # "loss_recorded", "recovered", "target_calculated"
    hedge_loss: float
    challenge_fee: float
    total_target: float
    hedge_lot_size: float
    status: str  # "pending", "completed", "partial"
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "cycle_id": self.cycle_id,
            "account_number": self.account_number,
            "action": self.action,
            "hedge_loss": self.hedge_loss,
            "challenge_fee": self.challenge_fee,
            "total_target": self.total_target,
            "hedge_lot_size": self.hedge_lot_size,
            "status": self.status,
            "notes": self.notes
        }


class HedgeRecoveryEngine:
    """
    Calculates hedge lot sizes and manages recovery from Maven challenge fees
    and accumulated hedge losses.
    
    Recovery Formula:
    TargetProfit = sum(ActiveFees) + DesiredSurplus + OutstandingRecoveryLoss
    HedgeLot = TargetProfit / (DrawdownDistance × PipValue)
    """
    
    def __init__(self, ledger_file: str = RECOVERY_LOSS_PERSISTENCE):
        self.logger = get_logger()
        self.ledger_file = Path(ledger_file)
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize ledger if not exists
        if not self.ledger_file.exists():
            self._init_ledger()
        
        self.outstanding_losses: Dict[str, float] = self._load_outstanding_losses()
        self.current_cycle_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _init_ledger(self) -> None:
        """Initialize empty ledger with headers"""
        headers = [
            "timestamp", "cycle_id", "account_number", "action",
            "hedge_loss", "challenge_fee", "total_target", "hedge_lot_size",
            "status", "notes"
        ]
        with open(self.ledger_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
    
    def _load_outstanding_losses(self) -> Dict[str, float]:
        """Load cumulative outstanding losses from ledger"""
        losses = {}
        try:
            if self.ledger_file.exists():
                with open(self.ledger_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row['action'] == 'loss_recorded' and row['status'] != 'recovered':
                            key = f"{row['cycle_id']}_{row['account_number']}"
                            losses[key] = float(row['hedge_loss'])
        except Exception as e:
            self.logger.log_error(e, "Failed to load outstanding losses")
        
        return losses
    
    def calculate_recovery_target(self, 
                                 active_fees: List[float],
                                 desired_surplus: float = DEFAULT_DESIRED_SURPLUS,
                                 account_id: Optional[str] = None) -> float:
        """
        Calculate total recovery target including:
        - Challenge fees from active accounts
        - Desired profit surplus
        - Outstanding recovery losses
        
        Args:
            active_fees: List of challenge fees from active Maven accounts
            desired_surplus: Target profit beyond fee recovery
            account_id: Account identifier for loss tracking
        
        Returns:
            Total target profit required
        """
        base_fees = sum(active_fees)
        outstanding = 0.0
        
        if account_id:
            for key, loss in self.outstanding_losses.items():
                if account_id in key:
                    outstanding += loss
        else:
            outstanding = sum(self.outstanding_losses.values())
        
        target = base_fees + desired_surplus + outstanding
        
        self.logger.info(
            f"Recovery target calculated: "
            f"Fees=${base_fees:.2f} + Surplus=${desired_surplus:.2f} + "
            f"Outstanding=${outstanding:.2f} = Total=${target:.2f}"
        )
        
        return target
    
    def calculate_hedge_lot_size(self,
                                target_profit: float,
                                max_drawdown: float = DEFAULT_DAILY_DRAWDOWN,
                                pip_value: float = 10.0,  # USD per pip for standard lot
                                symbol: str = "EURUSD") -> float:
        """
        Calculate hedge lot size using recovery formula.
        
        HedgeLot = TargetProfit / (DrawdownDistance × PipValue)
        
        Args:
            target_profit: Total recovery target in USD
            max_drawdown: Maximum daily drawdown allowance in USD
            pip_value: Value per pip in USD (default 10 for standard lot)
            symbol: Trading symbol for pip calculation
        
        Returns:
            Calculated lot size (0.01 lot precision)
        """
        if max_drawdown <= 0:
            self.logger.error("Max drawdown must be positive")
            return 0.0
        
        # Calculate lot size
        drawdown_distance = max_drawdown
        lot_size = target_profit / (drawdown_distance * pip_value)
        
        # Normalize to precision
        lot_size = round(lot_size, 2)
        
        self.logger.debug(
            f"Hedge lot calculated: Target=${target_profit:.2f} / "
            f"(${drawdown_distance:.2f} × ${pip_value:.2f}) = {lot_size:.2f}L"
        )
        
        return lot_size
    
    def record_hedge_loss(self,
                         cycle_id: str,
                         account_number: int,
                         hedge_loss: float,
                         challenge_fee: float = 0.0) -> bool:
        """
        Record hedge loss to ledger for future recovery
        Used when Maven passes but hedge account loses
        
        Args:
            cycle_id: Trading cycle identifier
            account_number: Maven account number
            hedge_loss: Amount lost on hedge trade
            challenge_fee: Associated challenge fee
        
        Returns:
            True if successfully recorded
        """
        try:
            entry = RecoveryLedgerEntry(
                timestamp=datetime.now().isoformat(),
                cycle_id=cycle_id,
                account_number=account_number,
                action="loss_recorded",
                hedge_loss=hedge_loss,
                challenge_fee=challenge_fee,
                total_target=hedge_loss + challenge_fee,
                hedge_lot_size=0.0,
                status="pending",
                notes=f"Loss recorded for recovery in next cycle"
            )
            
            self._append_ledger_entry(entry)
            key = f"{cycle_id}_{account_number}"
            self.outstanding_losses[key] = hedge_loss
            
            self.logger.info(
                f"Hedge loss recorded: ${hedge_loss:.2f} on account {account_number}"
            )
            return True
        except Exception as e:
            self.logger.log_error(e, "Failed to record hedge loss")
            return False
    
    def record_recovery_execution(self,
                                 cycle_id: str,
                                 account_number: int,
                                 hedge_lot_executed: float,
                                 target_amount: float,
                                 profit_achieved: float) -> bool:
        """
        Record successful recovery execution
        Updates ledger with recovery status
        
        Args:
            cycle_id: Trading cycle identifier
            account_number: Maven account number
            hedge_lot_executed: Lot size used for recovery
            target_amount: Target amount to recover
            profit_achieved: Actual profit from hedge trade
        
        Returns:
            True if successfully recorded
        """
        try:
            status = "completed" if profit_achieved >= target_amount else "partial"
            
            entry = RecoveryLedgerEntry(
                timestamp=datetime.now().isoformat(),
                cycle_id=cycle_id,
                account_number=account_number,
                action="recovered",
                hedge_loss=0.0,
                challenge_fee=0.0,
                total_target=target_amount,
                hedge_lot_size=hedge_lot_executed,
                status=status,
                notes=f"Recovery executed: ${profit_achieved:.2f} achieved of ${target_amount:.2f}"
            )
            
            self._append_ledger_entry(entry)
            
            # Update outstanding losses
            key = f"{cycle_id}_{account_number}"
            if key in self.outstanding_losses:
                if status == "completed":
                    del self.outstanding_losses[key]
                else:
                    remaining = self.outstanding_losses[key] - profit_achieved
                    self.outstanding_losses[key] = max(0, remaining)
            
            self.logger.info(
                f"Recovery executed: {status} - "
                f"${profit_achieved:.2f} achieved on {hedge_lot_executed:.2f}L"
            )
            return True
        except Exception as e:
            self.logger.log_error(e, "Failed to record recovery execution")
            return False
    
    def _append_ledger_entry(self, entry: RecoveryLedgerEntry) -> None:
        """Append entry to CSV ledger"""
        with open(self.ledger_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=entry.to_dict().keys())
            writer.writerow(entry.to_dict())
    
    def get_ledger_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recovery ledger for last N days"""
        try:
            entries = []
            cutoff = datetime.now().timestamp() - (days * 86400)
            
            with open(self.ledger_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ts = datetime.fromisoformat(row['timestamp']).timestamp()
                    if ts >= cutoff:
                        entries.append(row)
            
            total_losses = sum(
                float(e['hedge_loss']) for e in entries 
                if e['action'] == 'loss_recorded'
            )
            total_recovered = sum(
                float(e['total_target']) for e in entries 
                if e['action'] == 'recovered'
            )
            
            return {
                "period_days": days,
                "entries_count": len(entries),
                "total_losses": total_losses,
                "total_recovered": total_recovered,
                "net_outstanding": total_losses - total_recovered,
                "outstanding_losses": self.outstanding_losses
            }
        except Exception as e:
            self.logger.log_error(e, "Failed to get ledger summary")
            return {}
    
    def estimate_next_recovery_lot(self, 
                                  active_accounts: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Estimate required hedge lot size for next recovery cycle
        
        Returns:
            Tuple of (estimated_lot_size, target_recovery_amount)
        """
        fees = [acc.get('challenge_fee', 0.0) for acc in active_accounts]
        target = self.calculate_recovery_target(fees)
        lot = self.calculate_hedge_lot_size(target)
        
        return (lot, target)
