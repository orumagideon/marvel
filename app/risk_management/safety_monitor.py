"""
Risk Management and Safety Layer
Emergency protection, drawdown monitoring, and safety validations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from app.utils.logger import get_logger
from app.utils.constants import (
    DEFAULT_DAILY_DRAWDOWN, MIN_FREE_MARGIN_RATIO, 
    MAX_SPREAD_PIPS, EQUITY_CRITICAL_THRESHOLD
)
import MetaTrader5 as mt5


@dataclass
class RiskMetrics:
    """Real-time risk metrics"""
    current_equity: float
    balance: float
    margin_used: float
    margin_free: float
    margin_level: float
    daily_drawdown_used: float
    drawdown_percentage: float
    is_critical: bool
    free_margin_ratio: float


class RiskManagementSystem:
    """
    Comprehensive risk management:
    - Daily drawdown tracking
    - Equity protection
    - Spread validation
    - Margin safeguards
    - Emergency circuit breakers
    """
    
    def __init__(self, max_daily_drawdown: float = DEFAULT_DAILY_DRAWDOWN):
        self.logger = get_logger()
        self.max_daily_drawdown = max_daily_drawdown
        self.session_start_equity: Dict[int, float] = {}
        self.session_start_time = datetime.now()
        self.emergency_triggered = False
        self.drawdown_exceeded_time: Optional[datetime] = None
        
        # Trade statistics
        self.daily_trades = 0
        self.daily_wins = 0
        self.daily_losses = 0
        self.daily_profit_loss = 0.0
    
    def reset_daily_metrics(self) -> None:
        """Reset daily metrics (call at market open)"""
        self.session_start_time = datetime.now()
        self.session_start_equity.clear()
        self.daily_trades = 0
        self.daily_wins = 0
        self.daily_losses = 0
        self.daily_profit_loss = 0.0
        self.emergency_triggered = False
        self.drawdown_exceeded_time = None
        
        self.logger.info("Daily risk metrics reset")
    
    def initialize_account_equity(self, account: int, starting_equity: float) -> None:
        """Record starting equity for drawdown calculation"""
        self.session_start_equity[account] = starting_equity
        self.logger.debug(f"Account {account} starting equity: ${starting_equity:.2f}")
    
    def get_current_metrics(self, account: int) -> Optional[RiskMetrics]:
        """Calculate current risk metrics for account"""
        try:
            acc_info = mt5.account_info()
            if not acc_info:
                return None
            
            starting_equity = self.session_start_equity.get(account, acc_info.equity)
            drawdown = starting_equity - acc_info.equity
            drawdown_percentage = (drawdown / starting_equity * 100) if starting_equity > 0 else 0
            
            is_critical = drawdown >= (self.max_daily_drawdown - EQUITY_CRITICAL_THRESHOLD)
            free_margin_ratio = (acc_info.margin_free / acc_info.margin) if acc_info.margin > 0 else 0
            
            return RiskMetrics(
                current_equity=acc_info.equity,
                balance=acc_info.balance,
                margin_used=acc_info.margin,
                margin_free=acc_info.margin_free,
                margin_level=acc_info.margin_level,
                daily_drawdown_used=drawdown,
                drawdown_percentage=drawdown_percentage,
                is_critical=is_critical,
                free_margin_ratio=free_margin_ratio
            )
            
        except Exception as e:
            self.logger.debug(f"Failed to get risk metrics: {str(e)}")
            return None
    
    def check_drawdown_limit(self, account: int) -> bool:
        """Check if account has exceeded daily drawdown limit"""
        metrics = self.get_current_metrics(account)
        if not metrics:
            return False
        
        exceeded = metrics.daily_drawdown_used >= self.max_daily_drawdown
        
        if exceeded and not self.emergency_triggered:
            self.emergency_triggered = True
            self.drawdown_exceeded_time = datetime.now()
            self.logger.log_risk_event("DRAWDOWN_EXCEEDED", {
                "account": account,
                "drawdown": metrics.daily_drawdown_used,
                "limit": self.max_daily_drawdown,
                "timestamp": datetime.now().isoformat()
            })
        
        return exceeded
    
    def is_critical_equity(self, account: int) -> bool:
        """Check if equity is within critical threshold"""
        metrics = self.get_current_metrics(account)
        if not metrics:
            return False
        
        if metrics.is_critical:
            self.logger.warning(
                f"CRITICAL EQUITY: Account {account} within ${EQUITY_CRITICAL_THRESHOLD:.2f} of limit. "
                f"Current equity: ${metrics.current_equity:.2f}"
            )
        
        return metrics.is_critical
    
    def validate_spread(self, symbol: str, max_spread: float = MAX_SPREAD_PIPS) -> bool:
        """Validate spread is within acceptable range"""
        try:
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False
            
            spread_pips = (tick.ask - tick.bid) / (0.01 if symbol.endswith("JPY") else 0.0001)
            
            if spread_pips > max_spread:
                self.logger.warning(
                    f"Spread alert: {symbol} spread {spread_pips:.2f}pips exceeds limit {max_spread}pips"
                )
                return False
            
            return True
        except Exception as e:
            self.logger.debug(f"Spread validation error: {str(e)}")
            return False
    
    def validate_free_margin(self, account: int, min_ratio: float = MIN_FREE_MARGIN_RATIO) -> bool:
        """
        Validate sufficient free margin exists
        
        Args:
            account: Account number
            min_ratio: Minimum free margin as ratio of used margin
        
        Returns:
            True if sufficient margin exists
        """
        metrics = self.get_current_metrics(account)
        if not metrics:
            return False
        
        sufficient = metrics.free_margin_ratio >= min_ratio
        
        if not sufficient:
            self.logger.warning(
                f"Low margin alert: Account {account} free margin ratio "
                f"{metrics.free_margin_ratio:.2%} below minimum {min_ratio:.2%}"
            )
        
        return sufficient
    
    def validate_trade_execution(self, symbol: str, account: int, 
                                 lot_size: float) -> tuple[bool, Optional[str]]:
        """
        Pre-execution validation checklist
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check drawdown limit
        if self.check_drawdown_limit(account):
            return (False, f"Daily drawdown limit exceeded: ${self.max_daily_drawdown:.2f}")
        
        # Check critical equity
        if self.is_critical_equity(account):
            return (False, "Critical equity threshold breached")
        
        # Check free margin
        if not self.validate_free_margin(account):
            return (False, "Insufficient free margin")
        
        # Check spread
        if not self.validate_spread(symbol):
            return (False, f"Spread too high for {symbol}")
        
        # Get metrics for volume validation
        metrics = self.get_current_metrics(account)
        if not metrics:
            return (False, "Unable to retrieve account metrics")
        
        # Validate lot size against account size (rough check)
        risk_per_trade = (lot_size * 100) / metrics.current_equity * 100  # % of equity
        if risk_per_trade > 10:  # More than 10% risk
            self.logger.warning(f"High risk trade: {risk_per_trade:.2f}% of equity")
        
        return (True, None)
    
    async def monitor_drawdown(self, account: int, check_interval_seconds: int = 5) -> None:
        """
        Continuous drawdown monitoring
        Runs as background task, triggers emergency close if limit exceeded
        """
        while not self.emergency_triggered:
            try:
                if self.check_drawdown_limit(account):
                    self.logger.log_risk_event("EMERGENCY_DRAWDOWN_TRIGGER", {
                        "account": account,
                        "timestamp": datetime.now().isoformat()
                    })
                    break
                
                await asyncio.sleep(check_interval_seconds)
            except Exception as e:
                self.logger.debug(f"Drawdown monitoring error: {str(e)}")
                await asyncio.sleep(check_interval_seconds)
    
    def get_status(self, account: int) -> Dict[str, Any]:
        """Get comprehensive risk status"""
        metrics = self.get_current_metrics(account)
        if not metrics:
            return {"error": "Unable to retrieve metrics"}
        
        return {
            "account": account,
            "equity": metrics.current_equity,
            "drawdown_used": metrics.daily_drawdown_used,
            "drawdown_limit": self.max_daily_drawdown,
            "drawdown_percentage": metrics.drawdown_percentage,
            "margin_level": metrics.margin_level,
            "free_margin_ratio": metrics.free_margin_ratio,
            "is_critical": metrics.is_critical,
            "emergency_triggered": self.emergency_triggered,
            "daily_stats": {
                "trades": self.daily_trades,
                "wins": self.daily_wins,
                "losses": self.daily_losses,
                "pnl": self.daily_profit_loss
            }
        }
    
    def log_trade_result(self, account: int, profit_loss: float) -> None:
        """Log trade result for daily statistics"""
        self.daily_trades += 1
        self.daily_profit_loss += profit_loss
        
        if profit_loss > 0:
            self.daily_wins += 1
        elif profit_loss < 0:
            self.daily_losses += 1
        
        self.logger.debug(
            f"Trade logged: ${profit_loss:+.2f}. "
            f"Daily: {self.daily_wins}W-{self.daily_losses}L, ${self.daily_profit_loss:+.2f}"
        )
