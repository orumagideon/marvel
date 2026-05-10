"""
Marvel Trading System - Comprehensive API Reference
Complete documentation of all system APIs and methods
"""

API_REFERENCE = """
# MARVEL TRADING SYSTEM - API REFERENCE

## Core System API

### MavelCoreSystem (app/core/orchestrator.py)

**Initialization**
```python
from app.core.orchestrator import get_system

system = get_system()  # Singleton pattern - returns global instance
```

### MT5 Instance Management

#### initialize_maven_instance(terminal_path: str) -> bool
Initialize Maven fleet MT5 instance
```python
success = system.initialize_maven_instance("C:\\\\Program Files\\\\MetaTrader 5")
```

#### initialize_hedge_instance(terminal_path: str) -> bool
Initialize personal hedge MT5 instance
```python
success = system.initialize_hedge_instance("C:\\\\Program Files\\\\MetaTrader 5 Hedge")
```

#### login_maven_account(account: int, password: str, server: str) -> bool
Login to Maven account
```python
success = system.login_maven_account(123456, "password", "MavenPropFirm-Live")
```

#### login_hedge_account(account: int, password: str, server: str) -> bool
Login to personal hedge account
```python
success = system.login_hedge_account(654321, "password", "ICMarkets-Live")
```

### Trade Execution

#### execute_buy_order(symbol: str, lot_size: float, use_hedge: bool = True, use_maven: bool = True) 
-> Tuple[bool, Dict[str, Any]]
Execute synchronized BUY across active accounts
```python
success, results = await system.execute_buy_order("US100", 0.1, use_hedge=True, use_maven=True)
print(f"Success: {results['success_count']}, Failed: {results['failure_count']}")
```

Execution mode mapping:
- `Hedge + Funded`: `use_hedge=True`, `use_maven=True`
- `Funded Only`: `use_hedge=False`, `use_maven=True`
- `Hedge Only`: `use_hedge=True`, `use_maven=False`

#### execute_sell_order(symbol: str, lot_size: float, use_hedge: bool = True, use_maven: bool = True)
-> Tuple[bool, Dict[str, Any]]
Execute synchronized SELL
```python
success, results = await system.execute_sell_order("US100", 0.1, use_hedge=True, use_maven=True)
```

#### close_all_emergency() -> Dict[str, Any]
Emergency close all open positions
```python
results = await system.close_all_emergency()
print(f"Closed {results['closed_count']} positions")
```

### Account Management

#### add_maven_account(slot_id: int, account_number: int, password: str, 
                      server: str, phase: TradingPhase) -> bool
Register Maven account
```python
from app.account_manager.fleet_manager import TradingPhase

success = system.add_maven_account(
    slot_id=1,
    account_number=123456,
    password="secure_password",
    server="MavenPropFirm-Live",
    phase=TradingPhase.PHASE_1
)
```

#### set_account_active(slot_id: int, active: bool) -> bool
Toggle account active for next trade
```python
system.set_account_active(1, True)   # Activate
system.set_account_active(1, False)  # Deactivate
```

#### get_system_status() -> Dict[str, Any]
Get comprehensive system status
```python
status = system.get_system_status()
# Returns: session_id, is_running, mt5_instances, features, accounts
```

### Market Data

#### get_market_data(symbol: str = "US100") -> Optional[Dict[str, Any]]
Get live market data
```python
data = system.get_market_data("US100")
if data:
    print(f"Bid: {data['bid']}, Ask: {data['ask']}, Spread: {data['spread_pips']}pips")
```

#### get_account_health(account: int) -> Dict[str, Any]
Get account risk status
```python
health = system.get_account_health(123456)
print(f"Equity: ${health['equity']}, Drawdown: {health['drawdown_percentage']}%")
```

### Recovery Engine

#### get_recovery_target(account_ids: Optional[List[int]] = None) 
-> Tuple[float, float]
Get recovery target and estimated hedge lot
```python
lot_size, target = system.get_recovery_target([123456])
print(f"Target: ${target}, Hedge Lot: {lot_size:.2f}L")
```

#### record_hedge_loss(cycle_id: str, account_number: int, 
                       hedge_loss: float, fee: float = 0.0) -> bool
Record hedge loss for recovery
```python
success = system.record_hedge_loss(
    cycle_id="20260510_143022",
    account_number=123456,
    hedge_loss=100.0,
    fee=50.0
)
```

#### record_recovery_execution(cycle_id: str, account_number: int,
                              hedge_lot: float, target: float, 
                              profit: float) -> bool
Record recovery execution result
```python
success = system.record_recovery_execution(
    cycle_id="20260510_143022",
    account_number=123456,
    hedge_lot_executed=0.1,
    target_amount=150.0,
    profit_achieved=155.0
)
```

### Prop Firm Rules & Hedge Intelligence

#### configure_prop_challenge(payload: Dict[str, Any]) -> Dict[str, Any]
Configure dynamic prop-firm rules and return derived dollar limits.
```python
summary = system.configure_prop_challenge({
    "account_size": 5000,
    "purchase_fee": 59,
    "profit_target_pct": 8,
    "daily_drawdown_pct": 5,
    "overall_drawdown_pct": 10,
    "max_lots_allowed": 5,
    "profit_split_pct": 80,
    "recovery_mode": "balanced"
})
print(summary["target_dollar_amount"], summary["max_daily_loss_allowed"])
```

#### calculate_dynamic_hedge_plan(payload: Dict[str, Any]) -> Dict[str, Any]
Compute funded lot size, hedge lot size, recovery target, and risk projections.
```python
plan = system.calculate_dynamic_hedge_plan({
    "symbol": "US100",
    "stop_loss_pips": 20,
    "take_profit_pips": 10,
    "recovery_deficit": 108,
    "desired_surplus": 100,
    "risk_per_trade_pct": 0.5,
    "recovery_mode": "balanced"
})
print(plan["funded_lot_size"], plan["hedge_lot_size"], plan["recovery_efficiency_pct"])
```

#### save_challenge_template(template_name: str) -> bool
Save the currently applied challenge configuration as a reusable template.
```python
system.save_challenge_template("Maven 5K")
```

#### get_drawdown_guardrail(account: int) -> Dict[str, Any]
Get real-time drawdown usage and auto-protection state.
```python
guard = system.get_drawdown_guardrail(123456)
if guard["protection_triggered"]:
    print("Protection active: reduce lot size and block new entries")
```

---

## MT5 Connection Manager API

### MT5ConnectionManager (app/mt5_bridge/connection_manager.py)

#### initialize(instance_type: MT5InstanceType, terminal_path: str) -> bool
Initialize MT5 terminal instance
```python
from app.mt5_bridge.connection_manager import MT5ConnectionManager, MT5InstanceType

mgr = MT5ConnectionManager()
mgr.initialize(MT5InstanceType.MAVEN_FLEET, "C:\\\\Program Files\\\\MetaTrader 5")
mgr.initialize(MT5InstanceType.HEDGE_ACCOUNT, "C:\\\\Program Files\\\\MetaTrader 5 Hedge")
```

#### login(instance_type: MT5InstanceType, account: int, 
         password: str, server: str) -> bool
Login to account
```python
mgr.login(MT5InstanceType.MAVEN_FLEET, 123456, "password", "server")
```

#### is_connected(instance_type: MT5InstanceType) -> bool
Check connection status
```python
if mgr.is_connected(MT5InstanceType.HEDGE_ACCOUNT):
    print("Hedge account connected")
```

#### get_account_info(instance_type: MT5InstanceType) 
-> Optional[Dict[str, Any]]
Get account information
```python
info = mgr.get_account_info(MT5InstanceType.MAVEN_FLEET)
if info:
    print(f"Equity: ${info['equity']}, Balance: ${info['balance']}")
```

#### get_symbol_tick(symbol: str, instance_type: MT5InstanceType) 
-> Optional[Dict[str, Any]]
Get symbol tick data
```python
tick = mgr.get_symbol_tick("US100", MT5InstanceType.MAVEN_FLEET)
if tick:
    print(f"Bid: {tick['bid']}, Ask: {tick['ask']}")
```

#### reconnect(instance_type: MT5InstanceType, account: int, 
              password: str, server: str) -> bool
Automatic reconnection
```python
mgr.reconnect(MT5InstanceType.HEDGE_ACCOUNT, 654321, "password", "server")
```

#### get_status(instance_type: MT5InstanceType) -> Dict[str, Any]
Get comprehensive instance status
```python
status = mgr.get_status(MT5InstanceType.MAVEN_FLEET)
# Returns: state, connected, latency_ms, retry_count, etc
```

---

## Account Manager API

### AccountManager (app/account_manager/fleet_manager.py)

#### add_account(slot_id: int, account_number: int, password: str,
                 server: str, phase: TradingPhase, display_name: str = "") -> bool
Register new account
```python
from app.account_manager.fleet_manager import AccountManager, TradingPhase

mgr = AccountManager()
mgr.add_account(
    slot_id=1,
    account_number=123456,
    password="password",
    server="server",
    phase=TradingPhase.PHASE_1,
    display_name="Primary Maven"
)
```

#### get_account(slot_id: int) -> Optional[MavenAccount]
Get account by slot
```python
account = mgr.get_account(1)
if account:
    print(f"Account: {account.account_number}, Phase: {account.phase.value}")
```

#### get_account_credentials(slot_id: int) -> Optional[Dict[str, str]]
Get decrypted credentials
```python
creds = mgr.get_account_credentials(1)
if creds:
    # creds = {"account_number": ..., "password": ..., "server": ...}
```

#### set_account_active(slot_id: int, active: bool) -> bool
Toggle account active status
```python
mgr.set_account_active(1, True)
```

#### get_active_accounts() -> List[MavenAccount]
Get all active accounts
```python
active = mgr.get_active_accounts()
for acc in active:
    print(f"Active: {acc.account_number}")
```

#### list_accounts() -> List[Dict[str, Any]]
List all configured accounts
```python
accounts = mgr.list_accounts()
for acc in accounts:
    print(f"Slot {acc['slot_id']}: {acc['account_number']}")
```

#### select_account(slot_id: int) -> bool
Set current working account
```python
mgr.select_account(1)
```

#### remove_account(slot_id: int) -> bool
Remove account from slot
```python
mgr.remove_account(1)
```

---

## Recovery Engine API

### HedgeRecoveryEngine (app/recovery_engine/hedge_calculator.py)

#### calculate_recovery_target(active_fees: List[float],
                             desired_surplus: float = 100.0,
                             account_id: Optional[str] = None) -> float
Calculate recovery target
```python
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine

engine = HedgeRecoveryEngine()
target = engine.calculate_recovery_target(
    active_fees=[50.0, 75.0],
    desired_surplus=100.0
)
# Returns: 225.0
```

#### calculate_hedge_lot_size(target_profit: float,
                            max_drawdown: float = 400.0,
                            pip_value: float = 10.0,
                            symbol: str = "EURUSD") -> float
Calculate hedge lot size
```python
lot = engine.calculate_hedge_lot_size(
    target_profit=225.0,
    max_drawdown=400.0,
    pip_value=10.0
)
# Returns: 0.06 (normalized to 0.01 increments)
```

#### record_hedge_loss(cycle_id: str, account_number: int,
                      hedge_loss: float, challenge_fee: float = 0.0) -> bool
Record loss for recovery
```python
engine.record_hedge_loss(
    cycle_id="cycle_001",
    account_number=123456,
    hedge_loss=100.0,
    challenge_fee=50.0
)
```

#### record_recovery_execution(cycle_id: str, account_number: int,
                              hedge_lot_executed: float,
                              target_amount: float,
                              profit_achieved: float) -> bool
Record recovery execution
```python
engine.record_recovery_execution(
    cycle_id="cycle_001",
    account_number=123456,
    hedge_lot_executed=0.1,
    target_amount=150.0,
    profit_achieved=155.0
)
```

#### get_ledger_summary(days: int = 7) -> Dict[str, Any]
Get recovery history summary
```python
summary = engine.get_ledger_summary(days=7)
print(f"Total losses: ${summary['total_losses']}")
print(f"Total recovered: ${summary['total_recovered']}")
```

#### estimate_next_recovery_lot(active_accounts: List[Dict[str, Any]]) 
-> Tuple[float, float]
Estimate next recovery requirement
```python
lot, target = engine.estimate_next_recovery_lot(
    [{"challenge_fee": 50.0}, {"challenge_fee": 75.0}]
)
```

---

## Risk Management API

### RiskManagementSystem (app/risk_management/safety_monitor.py)

#### initialize_account_equity(account: int, starting_equity: float) -> None
Record starting equity
```python
from app.risk_management.safety_monitor import RiskManagementSystem

risk_mgr = RiskManagementSystem(max_daily_drawdown=400.0)
risk_mgr.initialize_account_equity(123456, 10000.0)
```

#### get_current_metrics(account: int) -> Optional[RiskMetrics]
Get real-time risk metrics
```python
metrics = risk_mgr.get_current_metrics(123456)
if metrics:
    print(f"Equity: ${metrics.current_equity}")
    print(f"Drawdown: {metrics.drawdown_percentage}%")
    print(f"Critical: {metrics.is_critical}")
```

#### check_drawdown_limit(account: int) -> bool
Check if drawdown limit exceeded
```python
if risk_mgr.check_drawdown_limit(123456):
    print("WARNING: Daily drawdown limit exceeded!")
```

#### validate_trade_execution(symbol: str, account: int,
                            lot_size: float) -> Tuple[bool, Optional[str]]
Pre-execution validation
```python
is_valid, error = risk_mgr.validate_trade_execution("US100", 123456, 0.1)
if not is_valid:
    print(f"Trade blocked: {error}")
```

#### validate_spread(symbol: str, max_spread: float = 0.5) -> bool
Validate current spread
```python
if risk_mgr.validate_spread("US100"):
    print("Spread acceptable, ready to trade")
```

#### validate_free_margin(account: int, min_ratio: float = 0.15) -> bool
Check free margin ratio
```python
if risk_mgr.validate_free_margin(123456):
    print("Sufficient margin available")
```

#### get_status(account: int) -> Dict[str, Any]
Get comprehensive risk status
```python
status = risk_mgr.get_status(123456)
# Returns: equity, drawdown_used, margin_level, is_critical, etc
```

#### reset_daily_metrics() -> None
Reset daily statistics
```python
risk_mgr.reset_daily_metrics()  # Call at market open
```

---

## Logging API

### StructuredLogger (app/utils/logger.py)

```python
from app.utils.logger import get_logger

logger = get_logger()

# Trade logging
logger.log_trade({
    "action": "buy",
    "symbol": "US100",
    "account": 123456,
    "lot": 0.1,
    "price": 19500.50
})

# Recovery logging
logger.log_recovery({
    "action": "target_calculated",
    "target": 225.0,
    "hedge_lot": 0.06
})

# Risk events
logger.log_risk_event("DRAWDOWN_EXCEEDED", {
    "account": 123456,
    "drawdown": 400.50
})

# General logging
logger.info("Trade executed successfully")
logger.warning("High spread detected")
logger.error("Connection failed")
```

---

## Configuration API

### SystemConfig (app/utils/config.py)

```python
from app.utils.config import get_config

config = get_config()

# Get values with dot notation
terminal_path = config.get('mt5.maven_terminal_path')
drawdown_limit = config.get('risk_management.daily_drawdown_limit')

# Set values
config.set('risk_management.daily_drawdown_limit', 500.0)

# Get sections
mt5_config = config.get_mt5_config()
trading_config = config.get_trading_config()
risk_config = config.get_risk_config()

# Reset to defaults
config.reset_to_defaults()
```

---

## Execution Engine API

### SynchronizedExecutionEngine (app/execution_engine/sync_executor.py)

```python
from app.execution_engine.sync_executor import SynchronizedExecutionEngine, TradeType

executor = SynchronizedExecutionEngine()

# Execute synchronized trade
success, results = await executor.execute_synchronized_trade(
    symbol="US100",
    lot_size=0.1,
    trade_type=TradeType.BUY,
    maven_accounts=[
        {"account_number": 123456},
        {"account_number": 234567}
    ],
    hedge_instance_info={"account": 654321, "is_active": True}
)

# Close all positions
close_results = await executor.close_all_positions()
print(f"Closed: {close_results['closed_count']}")
```

---

## UI Components

### MarketFeedWidget
```python
widget = MarketFeedWidget(parent)
widget.update_data({
    "bid": 19500.50,
    "ask": 19500.70,
    "spread_pips": 0.2
})
```

### AccountHealthWidget
```python
widget = AccountHealthWidget(parent)
widget.update_health({
    "equity": 9500.0,
    "drawdown_percentage": 5.0,
    "margin_level": 850.0,
    "is_critical": False
})
```

### TradingControlsWidget
```python
def handle_command(cmd):
    print(f"Command: {cmd}")

widget = TradingControlsWidget(parent, handle_command)
lot = widget.get_lot_size()  # Returns float
```

---

**API Version**: 1.0.0
**Last Updated**: May 2026
"""

if __name__ == "__main__":
    print(API_REFERENCE)
