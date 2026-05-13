# MARVEL MULTI-ASSET API REFERENCE

## Table of Contents
1. [AssetRegistry API](#assetregistry-api)
2. [SessionManager API](#sessionmanager-api)
3. [CTraderBridge API](#ctraderbridge-api)
4. [EnhancedExecutionEngine API](#enhancedexecutionengine-api)
5. [LatencyMonitor API](#latencymonitor-api)
6. [MavelCoreSystem API](#marvelcoresystem-api)

---

## AssetRegistry API

Location: `app/market_data/asset_registry.py`

### Class: `AssetRegistry`

#### Constructor
```python
registry = AssetRegistry()
```

#### Primary Methods

##### `select_symbol(symbol: str) -> bool`
Select the active trading symbol.
```python
success = registry.select_symbol("XAUUSD")
# Returns: True if symbol exists, False otherwise
```

##### `get_asset_profile(symbol: str) -> Optional[AssetProfile]`
Retrieve complete profile for a symbol.
```python
profile = registry.get_asset_profile("XAUUSD")
# Returns: AssetProfile with pip_value, margin_per_lot, volatility, etc.
```

##### `get_selected_profile() -> Optional[AssetProfile]`
Get profile of currently selected symbol.
```python
profile = registry.get_selected_profile()
# Returns: AssetProfile
```

##### `get_pip_value(symbol: str) -> float`
Get USD per pip for symbol.
```python
pip_value = registry.get_pip_value("XAUUSD")
# Returns: 10.0 for Gold
```

##### `get_margin_requirement(symbol: str) -> float`
Get USD margin per lot.
```python
margin = registry.get_margin_requirement("XAUUSD")
# Returns: 1800.0
```

##### `get_primary_symbols() -> List[str]`
Get list of primary trading symbols.
```python
symbols = registry.get_primary_symbols()
# Returns: ["USTECH", "NAS100", "XAUUSD", "US30", "GER40"]
```

##### `get_all_symbols() -> List[str]`
Get all supported symbols.
```python
all_symbols = registry.get_all_symbols()
# Returns: sorted list of all available symbols
```

##### `calculate_position_margin(symbol: str, lot_size: float) -> float`
Calculate total margin for a position.
```python
total_margin = registry.calculate_position_margin("XAUUSD", 8.4)
# Returns: 1800.0 * 8.4 = 15,120.0
```

##### `calculate_pip_risk(symbol: str, lot_size: float, pips: float) -> float`
Calculate USD risk in pips.
```python
risk = registry.calculate_pip_risk("XAUUSD", 8.4, 20.0)
# Returns: 10.0 * 8.4 * 20.0 = 1,680.0 USD risk
```

#### Properties

##### `AssetProfile`
```python
@dataclass
class AssetProfile:
    symbol: str                      # "XAUUSD"
    category: AssetCategory          # .METALS
    pip_value_per_lot: float        # 10.0
    margin_per_lot: float           # 1800.0
    avg_volatility_score: float     # 1.35
    spread_profile: str             # "medium"
    hedge_efficiency: float         # 0.78
    correlation_coefficient: float  # 0.54
```

---

## SessionManager API

Location: `app/session_manager/session_manager.py`

### Class: `SessionManager`

#### Constructor
```python
session_mgr = SessionManager(browser_bridge=None, mt5_manager=None)
```

#### Primary Methods

##### `create_session(account_id: int, platform: str = "ctrader") -> SessionContext`
Create a new trading session.
```python
session = session_mgr.create_session(account_id=50000, platform="ctrader")
```

##### `async auto_detect_account_balance(session: SessionContext) -> bool`
Auto-detect account balance from broker.
```python
success = await session_mgr.auto_detect_account_balance(session)
# Sets: session.account_balance, session.account_size_preset
```

##### `async detect_challenge_phase(session: SessionContext) -> ChallengePhase`
Detect current challenge phase.
```python
phase = await session_mgr.detect_challenge_phase(session)
# Returns: ChallengePhase.CHALLENGE_1 or .CHALLENGE_2 or .FUNDED or .FARMING
```

##### `set_selected_symbol(symbol: str) -> None`
Set selected symbol for current session.
```python
session_mgr.set_selected_symbol("XAUUSD")
```

##### `get_session_summary() -> Dict[str, Any]`
Get current session context.
```python
summary = session_mgr.get_session_summary()
# Returns: {
#   "session_id": "50000_20260514_120345",
#   "account_balance": 50000.0,
#   "challenge_phase": "Challenge 1",
#   "hedge_multiplier": 1.3,
#   "profit_target_pct": 8.0,
# }
```

##### `should_use_vps_mode(latency_threshold_ms: float = 200.0) -> bool`
Check if VPS mode recommended.
```python
use_vps = session_mgr.should_use_vps_mode()
# Returns: True if latency > 200ms
```

#### Properties

##### `ChallengePhaseConfig`
```python
@dataclass
class ChallengePhaseConfig:
    phase: ChallengePhase             # Challenge 1
    profit_target_pct: float          # 8.0
    aggressive_hedge_multiplier: float # 1.3
    lot_size_override: Optional[float] # None or 0.1
    max_daily_drawdown_pct: float     # 5.0
    max_total_drawdown_pct: float     # 10.0
```

##### `SessionContext`
```python
@dataclass
class SessionContext:
    session_id: str
    account_id: int
    platform: str                     # "ctrader"
    account_balance: float            # 50000.0
    account_size_preset: Optional[str] # "50K"
    challenge_phase: ChallengePhase   # Challenge 1
    selected_symbol: Optional[str]    # "XAUUSD"
    hedge_enabled: bool               # True
```

---

## CTraderBridge API

Location: `app/browser_bridge/match_trader_bridge.py`

### Class: `CTraderBridge`

#### Constructor
```python
bridge = CTraderBridge()
```

#### Primary Methods

##### `async start(url: str, headless: bool = True, viewport: Dict[str, int] = None) -> Dict[str, Any]`
Launch browser and connect to cTrader.
```python
result = await bridge.start("https://ctrader.example.com", headless=False)
# Returns: {"success": True, "url": "...", "discovered_fields": 3}
```

##### `async shutdown() -> None`
Close browser session cleanly.
```python
await bridge.shutdown()
```

##### `async inject_trade(lot: float, tp: float, sl: float) -> Dict[str, Any]`
Inject trading values into form fields.
```python
result = await bridge.inject_trade(lot=8.4, tp=50.0, sl=20.0)
# Returns: {
#   "success": True,
#   "injected": {
#     "quantity": {"value": 8.4, "injected": True},
#     "tp": {"value": 50.0, "injected": True},
#     "sl": {"value": 20.0, "injected": True}
#   },
#   "latency_ms": 245.3
# }
```

##### `async click_trade_button(direction: str) -> Dict[str, Any]`
Click Buy or Sell button.
```python
result = await bridge.click_trade_button("buy")
# Returns: {"success": True, "direction": "buy", "latency_ms": 123.4}
```

##### `async click_place_order() -> Dict[str, Any]`
Click Place Order or Execute button.
```python
result = await bridge.click_place_order()
# Returns: {"success": True, "latency_ms": 89.2}
```

##### `async read_account_balance() -> float`
Extract account balance from DOM.
```python
balance = await bridge.read_account_balance()
# Returns: 50000.0
```

##### `async read_challenge_phase() -> Dict[str, Any]`
Read challenge phase from account info.
```python
phase_info = await bridge.read_challenge_phase()
# Returns: {"name": "Challenge 1", "phase": 1, "target_pct": 8.0}
```

##### `async read_chart_symbol() -> Optional[str]`
Get currently active chart symbol.
```python
symbol = await bridge.read_chart_symbol()
# Returns: "XAUUSD" or None
```

##### `async execute_full_trade(direction: str, lot: float, tp: float, sl: float) -> Dict[str, Any]`
Complete trade execution workflow.
```python
result = await bridge.execute_full_trade(
    direction="buy",
    lot=8.4,
    tp=50.0,
    sl=20.0
)
# Returns: {
#   "success": True,
#   "direction": "buy",
#   "steps": {
#     "inject": {"success": True, ...},
#     "click_direction": {"success": True, ...},
#     "place_order": {"success": True, ...}
#   },
#   "total_latency_ms": 458.7
# }
```

#### Properties

##### `is_session_active() -> bool`
Check if browser session is active.
```python
if bridge.is_session_active():
    # Safe to use bridge
```

---

## EnhancedExecutionEngine API

Location: `app/execution_engine/enhanced_sync_executor.py`

### Class: `EnhancedSynchronizedExecutionEngine`

#### Constructor
```python
engine = EnhancedSynchronizedExecutionEngine()
```

#### Primary Methods

##### `async execute_synchronized_trade(...) -> ParallelExecutionResult`
Execute trade with parallel dispatch.
```python
result = await engine.execute_synchronized_trade(
    symbol="XAUUSD",
    lot_size=8.4,
    trade_type=TradeType.BUY,
    maven_accounts=[{"account_id": 12345, "slot_id": 1}],
    hedge_instance_info={"account_id": 67890, "is_active": True},
    tp_pips=50.0,
    sl_pips=20.0,
    match_trader_bridge=bridge,
    session_manager=session_mgr
)

# Returns:
# ParallelExecutionResult(
#   success=True,
#   hedge_result={"success": True, "ticket": 12345},
#   maven_results=[{"success": True, "ticket": 54321}],
#   ctrader_result={"success": True, "total_latency_ms": 245},
#   total_latency_ms=342.5,
#   symbol_mismatch=False
# )
```

##### `validate_symbol_match(expected_symbol: str, chart_symbol: Optional[str]) -> bool`
Validate symbol matching.
```python
valid = engine.validate_symbol_match("XAUUSD", "XAUUSD")
# Returns: True
```

##### `should_execute_be_blocked() -> bool`
Check if execution is locked due to symbol mismatch.
```python
blocked = engine.should_execute_be_blocked()
# Returns: False
```

##### `clear_execution_lock() -> None`
Clear execution lock after manual confirmation.
```python
engine.clear_execution_lock()
```

#### Properties

##### `ParallelExecutionResult`
```python
@dataclass
class ParallelExecutionResult:
    success: bool                           # True/False
    hedge_result: Optional[Dict]            # Exness MT5 result
    maven_results: List[Dict]               # All Maven results
    ctrader_result: Optional[Dict]          # cTrader result
    total_latency_ms: float                 # 342.5
    symbol_mismatch: bool                   # False
    error_message: Optional[str]            # None or error text
```

---

## LatencyMonitor API

Location: `app/monitoring/latency_monitor.py`

### Class: `LatencyMonitor`

#### Constructor
```python
monitor = LatencyMonitor()
```

#### Primary Methods

##### `async start_monitoring() -> None`
Start background latency monitoring.
```python
await monitor.start_monitoring()
# Runs continuous measurement loop
```

##### `async stop_monitoring() -> None`
Stop background monitoring.
```python
await monitor.stop_monitoring()
```

##### `async measure_latency(server: str, url: Optional[str] = None) -> float`
Measure latency to server.
```python
latency_ms = await monitor.measure_latency("ctrader")
# Returns: 142.5
```

##### `get_current_stats(server: Optional[str] = None, window_seconds: Optional[int] = None) -> Dict[str, LatencyStats]`
Get latency statistics.
```python
stats = monitor.get_current_stats("ctrader", window_seconds=300)
# Returns: {
#   "ctrader": LatencyStats(
#     avg_latency_ms=145.3,
#     quality=ConnectionQuality.FAIR,
#     vps_recommended=False
#   )
# }
```

##### `should_use_vps_mode() -> bool`
Check if VPS mode should be used.
```python
use_vps = monitor.should_use_vps_mode()
# Returns: True if avg latency > 200ms
```

##### `get_recommendations() -> Dict[str, str]`
Get actionable recommendations.
```python
recommendations = monitor.get_recommendations()
# Returns: {
#   "ctrader": "⚠️ Fair connectivity... Consider VPS mode.",
#   "exness_ke": "✓ Good connectivity... Direct execution OK."
# }
```

#### Properties

##### `ConnectionQuality` Enum
```python
class ConnectionQuality(Enum):
    EXCELLENT = "excellent"  # < 50ms
    GOOD = "good"            # 50-100ms
    FAIR = "fair"            # 100-200ms
    POOR = "poor"            # > 200ms
```

##### `LatencyStats`
```python
@dataclass
class LatencyStats:
    server: str                     # "ctrader"
    sample_count: int               # 15
    min_latency_ms: float           # 120.0
    max_latency_ms: float           # 180.0
    avg_latency_ms: float           # 145.3
    quality: ConnectionQuality      # .FAIR
    vps_recommended: bool           # False
```

---

## MavelCoreSystem API

Location: `app/core/orchestrator.py`

### Class: `MavelCoreSystem`

#### Asset Management Methods

##### `select_symbol(symbol: str) -> bool`
Select active trading symbol.
```python
success = system.select_symbol("XAUUSD")
# Returns: True
```

##### `get_selected_symbol() -> Optional[str]`
Get currently selected symbol.
```python
symbol = system.get_selected_symbol()
# Returns: "XAUUSD"
```

##### `get_primary_symbols() -> List[str]`
Get list of primary symbols.
```python
symbols = system.get_primary_symbols()
# Returns: ["USTECH", "NAS100", "XAUUSD", "US30", "GER40"]
```

##### `get_symbol_profile(symbol: str) -> Dict[str, str]`
Get symbol profile with formatted display.
```python
profile = system.get_symbol_profile("XAUUSD")
# Returns: {
#   "symbol": "XAUUSD",
#   "pip_value": "$10.00",
#   "margin_per_lot": "$1,800.00",
#   "category": "metals"
# }
```

#### Session Management Methods

##### `async initialize_ctrader_session(account_id: int) -> bool`
Initialize cTrader session with auto-detection.
```python
success = await system.initialize_ctrader_session(50000)
# Auto-detects balance and phase
# Returns: True if successful
```

##### `get_session_summary() -> Dict[str, Any]`
Get current session context.
```python
summary = system.get_session_summary()
# Returns session details
```

##### `validate_symbol_match(expected_symbol: str) -> Tuple[bool, str]`
Validate symbol matching.
```python
valid, msg = system.validate_symbol_match("XAUUSD")
# Returns: (True, "Symbol match validated")
```

#### Latency Monitoring Methods

##### `async start_latency_monitoring() -> None`
Start latency monitoring.
```python
await system.start_latency_monitoring()
```

##### `async stop_latency_monitoring() -> None`
Stop latency monitoring.
```python
await system.stop_latency_monitoring()
```

##### `get_latency_stats() -> Dict[str, Any]`
Get latency statistics.
```python
stats = system.get_latency_stats()
```

##### `should_use_vps_mode() -> bool`
Check VPS recommendation.
```python
if system.should_use_vps_mode():
    print("Use VPS mode")
```

##### `get_latency_recommendations() -> Dict[str, str]`
Get actionable recommendations.
```python
recommendations = system.get_latency_recommendations()
```

#### Enhanced Execution Methods

##### `async execute_buy_order_enhanced(symbol: str, lot_size: float, ...) -> ParallelExecutionResult`
Execute BUY with validation and parallel dispatch.
```python
result = await system.execute_buy_order_enhanced(
    symbol="XAUUSD",
    lot_size=8.4,
    use_hedge=True,
    use_maven=True,
    tp_pips=50.0,
    sl_pips=20.0
)
# Returns: ParallelExecutionResult
```

##### `async execute_sell_order_enhanced(...) -> ParallelExecutionResult`
Execute SELL with validation and parallel dispatch.
```python
result = await system.execute_sell_order_enhanced(...)
```

---

## Global Functions

### `get_system() -> MavelCoreSystem`
Get or create the global system instance.
```python
from app.core.orchestrator import get_system

system = get_system()
```

---

## Enums

### `TradeType`
```python
class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"
```

### `ChallengePhase`
```python
class ChallengePhase(Enum):
    CHALLENGE_1 = "Challenge 1"
    CHALLENGE_2 = "Challenge 2"
    FUNDED = "Funded"
    FARMING = "Farming"
```

### `AssetCategory`
```python
class AssetCategory(Enum):
    INDICES = "indices"
    METALS = "metals"
    FOREX = "forex"
```

---

## Complete Example

```python
import asyncio
from app.core.orchestrator import get_system

async def main():
    system = get_system()
    
    # 1. Initialize bridges and connections
    system.initialize_maven_instance("path/to/maven")
    system.initialize_hedge_instance("path/to/exness")
    
    # 2. Start latency monitoring
    await system.start_latency_monitoring()
    
    # 3. Select asset
    system.select_symbol("XAUUSD")
    profile = system.get_symbol_profile("XAUUSD")
    print(f"Trading {profile['symbol']}: {profile['pip_value']}/pip")
    
    # 4. Initialize session
    await system.initialize_ctrader_session(50000)
    
    # 5. Check VPS need
    if system.should_use_vps_mode():
        print("High latency - use VPS")
    
    # 6. Execute trade
    result = await system.execute_buy_order_enhanced(
        symbol="XAUUSD",
        lot_size=8.4,
        tp_pips=50.0,
        sl_pips=20.0
    )
    
    print(f"Trade success: {result.success}")
    print(f"Latency: {result.total_latency_ms:.2f}ms")

asyncio.run(main())
```

---

Last Updated: 2026-05-14
Status: Complete API Reference
