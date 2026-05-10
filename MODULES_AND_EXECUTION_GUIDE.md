# Marvel Trading Dashboard — Modules & Execution Guide

This comprehensive guide explains the core modules of Marvel Trading Dashboard, how they work together, and walks through practical examples to help you execute trades successfully.

---

## Table of Contents

1. [Maven Fleet Slots](#maven-fleet-slots)
2. [Challenge Configuration (Prop Firm Rules)](#challenge-configuration-prop-firm-rules)
3. [Recovery Modes](#recovery-modes)
4. [Account Types & Presets](#account-types--presets)
5. [Instruments & Pricing](#instruments--pricing)
6. [Example 1: Basic 5K Account Setup](#example-1-basic-5k-account-setup)
7. [Example 2: Multi-Slot Fleet Execution](#example-2-multi-slot-fleet-execution)
8. [How to Execute Successfully](#how-to-execute-successfully)
9. [Code Reference](#code-reference)

---

## Maven Fleet Slots

### What Are Slots?

A **slot** is a numbered container (1 through N) that holds one Maven (Funded Next) account's metadata and encrypted credentials. Slots allow the system to manage multiple funded accounts as a coordinated fleet.

**Key Facts:**
- **Default count:** 5 slots (configurable; see `MAVEN_ACCOUNT_SLOTS` in `app/utils/constants.py`)
- **Max scaling:** 20 slots (future expansion capability)
- **Metadata per slot:** account number, server, trading phase (Phase 1 or Phase 2), active status, display name, login timestamp
- **Credentials storage:** encrypted in `data/credentials.enc` (never persisted unencrypted in JSON)
- **Metadata storage:** `data/accounts.json` (account numbers, servers, phase, active flag, etc.)

### How Slots Work

```
Slot 1  → Maven Account #123456 (Phase 1, active)
Slot 2  → Maven Account #234567 (Phase 1, inactive)
Slot 3  → Maven Account #345678 (Phase 2, active)
Slot 4  → Empty
Slot 5  → Empty
```

When you press **Buy/Sell** in the Trading Controls with `Hedge + Funded` mode:
1. System retrieves all **active slots** (marked `is_active=True`).
2. For each active slot, retrieves encrypted credentials from the vault using `maven_slot_{slot_id}`.
3. Constructs a synchronized trade and sends:
   - **First:** Hedge trade to MT5 hedge account.
   - **Then (after ~20ms delay):** Funded trades to each active Maven slot in parallel.

### Slot Operations (Code Level)

**Key methods in `app/account_manager/fleet_manager.py`:**

| Method | Purpose |
|--------|---------|
| `add_account(slot_id, account_number, password, server, phase)` | Register a Maven account in a slot |
| `get_account(slot_id)` | Retrieve metadata for a slot |
| `get_account_credentials(slot_id)` | Decrypt and retrieve credentials (only when needed) |
| `set_account_active(slot_id, active)` | Mark slot for next trade execution |
| `get_active_accounts()` | List all active slots for a pending execution |
| `select_account(slot_id)` | UI: choose which slot to focus on |
| `get_selected_account()` | UI: get the currently selected slot |
| `list_accounts()` | UI: display all configured slots with metadata |
| `remove_account(slot_id)` | Clear a slot |

### Example: Managing Slots

```python
from app.account_manager.fleet_manager import AccountManager, TradingPhase

mgr = AccountManager()

# Register Maven account in slot 1
mgr.add_account(
    slot_id=1,
    account_number=123456,
    password="secret_pass",
    server="FXOpen-MT5",
    phase=TradingPhase.PHASE_1,
    display_name="Maven 5K"
)

# Mark slot 1 as active for trading
mgr.set_account_active(1, True)

# Get all active slots (ready for trade dispatch)
active_accounts = mgr.get_active_accounts()
# → [MavenAccount(slot_id=1, account_number=123456, ...)]

# UI: Select slot 1 for viewing
mgr.select_account(1)
current = mgr.get_selected_account()
# → MavenAccount(slot_id=1, ...)

# List all slots
all_slots = mgr.list_accounts()
# → [{"slot_id": 1, "account_number": 123456, "phase": "Phase 1", "is_active": True, ...}]
```

---

## Challenge Configuration (Prop Firm Rules)

### What Is the Challenge Configuration?

The **Challenge Configuration** defines the prop-firm account rules (profit targets, drawdown limits, max lots, etc.) and is used by the engine to compute dynamic hedge and funded lot sizes that comply with those rules.

### Challenge Configuration Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `account_size` | float | Funded account nominal size (USD) | `5000.0` |
| `purchase_fee` | float | One-time fee to buy the challenge (USD); added to recovery target | `59.0` |
| `profit_target_pct` | float | % profit required to pass the challenge | `8.0` (= $400 on 5K) |
| `daily_drawdown_pct` | float | Daily loss limit as % of account size | `5.0` (= $250 on 5K) |
| `overall_drawdown_pct` | float | Overall loss limit as % of account size | `10.0` (= $500 on 5K) |
| `max_lots_allowed` | float | Hard cap on lot sizing (safety ceiling) | `5.0` |
| `profit_split_pct` | float | Profit share split % (informational for planning) | `80.0` |
| `leverage` | float | Margin leverage setting | `100.0` |
| `recovery_mode` | string | Scales hedge sizing: `conservative`, `balanced`, `aggressive` | `"balanced"` |

### Engine Derivations (What the Engine Calculates)

When you call **Compute**, the engine derives:

| Derived Value | Formula | Meaning |
|---------------|---------|---------|
| `target_dollar_amount` | `account_size * (profit_target_pct / 100)` | Total $ profit needed to pass |
| `max_daily_loss_allowed` | `account_size * (daily_drawdown_pct / 100)` | Max $ loss allowed per day |
| `max_overall_loss_allowed` | `account_size * (overall_drawdown_pct / 100)` | Max $ loss allowed overall |

### How to Set Challenge Configuration

1. **In Dashboard UI:**
   - Right Panel → Challenge / Strategy Config widget
   - Fill in the input fields (Account Size, Purchase Fee, Profit Target %, etc.)
   - Click **Compute** to generate hedge/funded lot sizes
   - (Optional) Click **Save Template** to persist for reuse

2. **Programmatically (for automation):**
   ```python
   from app.core.orchestrator import get_system
   
   system = get_system()
   
   summary = system.configure_prop_challenge({
       "account_size": 5000.0,
       "purchase_fee": 59.0,
       "profit_target_pct": 8.0,
       "daily_drawdown_pct": 5.0,
       "overall_drawdown_pct": 10.0,
       "max_lots_allowed": 5.0,
       "profit_split_pct": 80.0,
       "recovery_mode": "balanced"
   })
   
   print(summary["target_dollar_amount"])  # → 400.0
   print(summary["max_daily_loss_allowed"])  # → 250.0
   ```

### Saved Templates

Templates let you save and reuse challenge configurations:

```python
# Save current configuration as a template
system.save_challenge_template("Maven 5K Balanced")

# Templates are stored in config and can be reloaded by UI
# Next time, user selects "Maven 5K Balanced" from dropdown to restore
```

Templates are persisted in `data/config.json` under `prop_firm.saved_templates`.

---

## Recovery Modes

### What Do Recovery Modes Do?

Recovery modes **scale hedge lot sizing** to balance recovery speed vs. risk per trade.

| Mode | Multiplier | Behavior | Use Case |
|------|-----------|----------|----------|
| **Conservative** | **0.80** | Hedge lot = 80% of calculated | Low margin buffer, equity near limit, want safety |
| **Balanced** | **1.00** | Hedge lot = 100% of calculated (default) | Middle ground; most situations |
| **Aggressive** | **1.30** | Hedge lot = 130% of calculated | Ample margin, want fast recovery |

### How It Works in Calculation

The engine computes a **base hedge lot** using volatility, instrument profiles, and risk parameters. Then it applies the mode multiplier:

```
hedge_lot = base_hedge_lot * MODE_MULTIPLIER[recovery_mode]
```

### Example: 5K Account, US100, Balanced vs. Aggressive

**Inputs:**
- account_size = 5000
- daily_drawdown_pct = 5 (→ max loss allowed = $250)
- symbol = US100 (pip value = 1.0)
- stop_loss_pips = 20
- risk_per_trade_pct = 0.5

**Calculation steps:**
1. risk_budget = min(0.9 × 250 = 225, 5000 × 0.005 = 25) = **25**
2. funded_lot = 25 / (20 × 1) = **1.25 lots**
3. base_hedge_lot ≈ **1.70 lots** (before multiplier)

**Final hedge lot by mode:**
- Conservative: 1.70 × 0.80 = **1.36 lots**
- Balanced: 1.70 × 1.00 = **1.70 lots**
- Aggressive: 1.70 × 1.30 = **2.21 lots**

**Impact on recovery:**
- **Conservative (1.36):** Max loss per hedge trade = 1.36 × 20 × 1 = $27.20. Safer but takes more trades to recover.
- **Balanced (1.70):** Max loss per hedge trade = 1.70 × 20 × 1 = $34.00. Recommended default.
- **Aggressive (2.21):** Max loss per hedge trade = 2.21 × 20 × 1 = $44.20. Faster recovery but higher drawdown risk.

### When to Use Each

| Mode | Recommended When |
|------|-----------------|
| **Conservative** | Recovering after large loss; small account (<5K); margin buffer is tight; equity flagged as at-risk |
| **Balanced** | Default; standard account sizes (5K–50K); neutral risk appetite |
| **Aggressive** | Ample margin available; want to recover quickly; can tolerate larger per-trade losses |

---

## Account Types & Presets

### Preset Account Sizes

Marvel provides predefined account presets aligned with common Maven offerings:

| Preset | Size | Typical Profit Target | Daily Drawdown | Purchase Fee |
|--------|------|----------------------|-----------------|--------------|
| **2K** | $2,000 | $160 (8%) | $100 (5%) | $29–$39 |
| **5K** | $5,000 | $400 (8%) | $250 (5%) | $59 |
| **10K** | $10,000 | $800 (8%) | $500 (5%) | $99 |
| **25K** | $25,000 | $2,000 (8%) | $1,250 (5%) | $149 |
| **50K** | $50,000 | $4,000 (8%) | $2,500 (5%) | $249 |

See presets in `app/recovery_engine/prop_risk_engine.py` → `ACCOUNT_SIZE_PRESETS`.

### Trading Phases

Maven accounts are designated as **Phase 1** or **Phase 2**:
- **Phase 1:** Initial challenge; stricter rules; smaller max lots.
- **Phase 2:** Post-challenge; more relaxed limits; higher lot allowance.

The system tracks and reports phase segregation (e.g., `get_accounts_by_phase(TradingPhase.PHASE_1)`).

### How to Choose an Account Type

1. **Start with preset that matches your Maven purchase:** Look at your Maven order confirmation for account size.
2. **Set the default configuration in Challenge widget** using that preset name.
3. **Adjust drawdown/profit target % if Maven rules differ** from defaults.
4. **Save as a template** so you don't re-enter each time.

---

## Instruments & Pricing

### Instrument Categories

The engine has built-in profiles for **Indices**, **Forex**, and **Metals**:

#### Indices (Equities)
| Symbol | Pip Value | Margin/Lot | Volatility | Hedge Efficiency |
|--------|-----------|-----------|-----------|-----------------|
| US100 | 1.0 | $1,300 | 1.45 | 0.72 |
| USTECH | 1.0 | $1,300 | 1.50 | 0.72 |
| NAS100 | 1.0 | $1,300 | 1.45 | 0.72 |
| US30 | 1.0 | $1,600 | 1.30 | 0.69 |
| SPX500 | 1.0 | $1,200 | 1.10 | 0.75 |

**Why it matters:**
- **Pip value 1.0** → lot sizes will be larger for same risk budget vs. forex.
- **Higher margin/lot** → requires more free margin per lot opened.

#### Forex (Currency Pairs)
| Symbol | Pip Value | Margin/Lot | Volatility | Hedge Efficiency |
|--------|-----------|-----------|-----------|-----------------|
| EURUSD | 10.0 | $1,000 | 0.85 | 0.90 |
| GBPUSD | 10.0 | $1,000 | 0.95 | 0.88 |
| USDJPY | 9.2 | $1,000 | 0.90 | 0.89 |

**Why it matters:**
- **Pip value 10** → lot sizes ~10× smaller than indices for same risk.
- **Better hedge efficiency** (0.88–0.90) → hedge recovery per lot is higher.
- **Lower volatility** → less slippage, steadier moves.

#### Metals
| Symbol | Pip Value | Margin/Lot | Volatility | Hedge Efficiency |
|--------|-----------|-----------|-----------|-----------------|
| XAUUSD (Gold) | 10.0 | $1,800 | 1.35 | 0.78 |
| XAGUSD (Silver) | 50.0 | $1,400 | 1.25 | 0.76 |

**Why it matters:**
- **High pip value** → very small lot sizes for same risk.
- **High margin/lot** → expensive to open positions.

### How Pip Value Affects Lot Sizing

The engine calculates:
```
funded_lot = risk_budget / (stop_loss_pips × pip_value_per_lot)
```

**Example: Same $25 risk budget, different instruments**
- **US100** (pip_value=1): funded_lot = 25 / (20 × 1) = **1.25 lots**
- **EURUSD** (pip_value=10): funded_lot = 25 / (20 × 10) = **0.125 lots**
- **XAUUSD** (pip_value=10): funded_lot = 25 / (20 × 10) = **0.125 lots**

**Implication:** To trade Forex with same notional exposure as Indices, use ~10× larger lots (or accept much smaller positions).

---

## Example 1: Basic 5K Account Setup

### Scenario

You've purchased a **Maven 5K Challenge** account and want to set up Marvel to trade it with a hedge account.

### Step 1: Register the Maven Account (Slot 1)

```python
from app.core.orchestrator import get_system
from app.account_manager.fleet_manager import TradingPhase

system = get_system()

# Add Maven account to slot 1
system.add_maven_account(
    slot_id=1,
    account_number=123456,
    password="your_maven_password",
    server="FXOpen-MT5",
    phase=TradingPhase.PHASE_1
)

# Mark it active for trading
system.set_account_active(1, True)
```

### Step 2: Configure Challenge

```python
# Set the 5K challenge rules
summary = system.configure_prop_challenge({
    "account_size": 5000.0,
    "purchase_fee": 59.0,
    "profit_target_pct": 8.0,
    "daily_drawdown_pct": 5.0,
    "overall_drawdown_pct": 10.0,
    "max_lots_allowed": 5.0,
    "profit_split_pct": 80.0,
    "recovery_mode": "balanced"
})

print(f"Profit target: ${summary['target_dollar_amount']}")
# → Profit target: $400.0
print(f"Daily loss limit: ${summary['max_daily_loss_allowed']}")
# → Daily loss limit: $250.0

# Save as template for reuse
system.save_challenge_template("Maven 5K")
```

### Step 3: Compute Hedge Plan for US100

```python
# Compute recommended lot sizes
plan = system.calculate_dynamic_hedge_plan({
    "symbol": "US100",
    "stop_loss_pips": 20,
    "take_profit_pips": 10,
    "desired_surplus": 100.0,
    "risk_per_trade_pct": 0.5,
    "recovery_deficit": 0.0,
    "recovery_mode": "balanced"
})

print(f"Funded lot size: {plan['funded_lot_size']} lots")
# → Funded lot size: 1.25 lots
print(f"Hedge lot size: {plan['hedge_lot_size']} lots")
# → Hedge lot size: 1.7 lots
print(f"Max loss projection: ${plan['max_loss_projection']}")
# → Max loss projection: $59.0
print(f"Margin required: ${plan['margin_requirement']}")
# → Margin required: $3,870.0
print(f"Recovery efficiency: {plan['recovery_efficiency_pct']}%")
# → Recovery efficiency: 71.45%
```

### Step 4: Execute a Trade (via UI)

**In Dashboard:**
1. **Accounts Grid:** Verify slot 1 is shown and marked as active.
2. **Challenge Widget:** Confirm "Maven 5K" template is loaded; Compute shows funded_lot=1.25, hedge_lot=1.7.
3. **Trading Controls:**
   - Set **Execution Mode** → **Hedge + Funded**
   - Set **Volume/Lots** → **1.25** (funded lot)
   - Set **TP** → **10 pips**, **SL** → **20 pips**
   - Click **Buy** (or **Sell**)
4. **Execution flow:**
   - System validates spread and risk.
   - Sends **hedge trade** to MT5 hedge account (1.7 lots).
   - Waits ~20ms.
   - Sends **funded trade** to Maven slot 1 (1.25 lots).
   - Logs both trades to execution log and recovery ledger (if applicable).

### Step 5: Record a Hedge Loss (if needed)

If hedge trade closes with a loss:

```python
# Option A: Auto-fill from latest hedge trade
auto_result = system.auto_record_latest_hedge_loss()
print(auto_result)
# → {"recorded": True, "ticket": 987654, "account_number": 999888, "hedge_loss": 45.50}

# Option B: Manual record
system.record_hedge_loss(
    cycle_id="20260510_143022",
    account_number=999888,
    hedge_loss=45.50,
    fee=59.0
)
```

---

## Example 2: Multi-Slot Fleet Execution

### Scenario

You own **three Maven accounts** (3 slots, all Phase 1) and want to execute the same trade across all three simultaneously to diversify risk and scale exposure.

### Step 1: Register All Three Accounts

```python
from app.core.orchestrator import get_system
from app.account_manager.fleet_manager import TradingPhase

system = get_system()

# Slot 1: Maven 5K (Account A)
system.add_maven_account(
    slot_id=1,
    account_number=111111,
    password="pass_a",
    server="FXOpen-MT5",
    phase=TradingPhase.PHASE_1
)

# Slot 2: Maven 5K (Account B)
system.add_maven_account(
    slot_id=2,
    account_number=222222,
    password="pass_b",
    server="FXOpen-MT5",
    phase=TradingPhase.PHASE_1
)

# Slot 3: Maven 10K (Account C)
system.add_maven_account(
    slot_id=3,
    account_number=333333,
    password="pass_c",
    server="FXOpen-MT5",
    phase=TradingPhase.PHASE_1
)

# Mark all active
system.set_account_active(1, True)
system.set_account_active(2, True)
system.set_account_active(3, True)
```

### Step 2: Configure Challenge for Average Account (5K)

```python
summary = system.configure_prop_challenge({
    "account_size": 5000.0,
    "purchase_fee": 59.0,
    "profit_target_pct": 8.0,
    "daily_drawdown_pct": 5.0,
    "overall_drawdown_pct": 10.0,
    "max_lots_allowed": 5.0,
    "profit_split_pct": 80.0,
    "recovery_mode": "balanced"
})
```

### Step 3: Compute Hedge Plan

```python
plan = system.calculate_dynamic_hedge_plan({
    "symbol": "EURUSD",  # Forex example
    "stop_loss_pips": 50,
    "take_profit_pips": 25,
    "desired_surplus": 100.0,
    "risk_per_trade_pct": 0.5,
    "recovery_deficit": 0.0,
    "recovery_mode": "balanced",
    "active_accounts": [
        {"challenge_fee": 59.0},
        {"challenge_fee": 59.0},
        {"challenge_fee": 99.0}
    ]
})

print(f"Funded lot size per account: {plan['funded_lot_size']} lots")
# → Funded lot size per account: 0.125 lots (EURUSD is smaller)
print(f"Total funded exposure: {0.125 * 3} = 0.375 lots across 3 accounts")
print(f"Hedge lot size: {plan['hedge_lot_size']} lots")
# → Hedge lot size: 0.17 lots
```

### Step 4: Execute to All Three Slots (via UI or API)

**In Dashboard:**
1. **Accounts Grid:** Verify all 3 slots shown and marked active.
2. **Trading Controls:**
   - Set **Execution Mode** → **Hedge + Funded**
   - Set **Volume/Lots** → **0.125** (per-account funded lot)
   - Set **TP** → **25 pips**, **SL** → **50 pips**
   - Click **Buy**

**Execution flow:**
1. Hedge order placed: **0.17 lots** on MT5 hedge account.
2. Wait ~20ms.
3. Funded orders placed (parallel): **0.125 lots** on each of 3 Maven slots.
4. Total exposure: 0.375 lots funded, 0.17 lots hedged.

**Programmatic execution:**
```python
import asyncio

async def execute_multi_slot():
    success, results = await system.execute_buy_order(
        symbol="EURUSD",
        lot_size=0.125,
        use_hedge=True,
        use_maven=True,
        tp_pips=25,
        sl_pips=50
    )
    
    print(f"Execution success: {success}")
    print(f"Results: {results}")
    # → Hedge trade: ticket 987654, Maven trades: tickets [111111_slot1, 222222_slot2, 333333_slot3]

# Run async execution
asyncio.run(execute_multi_slot())
```

### Step 5: Recovery Ledger Management

After a few trades, check the Recovery Ledger for any recorded hedge losses:

```python
# Get latest hedge trade P&L
pnl = system.get_latest_hedge_trade_pnl()
print(f"Latest hedge trade P&L: ${pnl}")
# → Latest hedge trade P&L: -45.50 (loss)

# Auto-record if not already logged
result = system.auto_record_latest_hedge_loss()
print(result)
# → {"recorded": True, "ticket": 987654, ...}

# Or manually log a recovery execution
system.record_recovery_execution(
    cycle_id="RECOVERY_001",
    account_number=111111,
    hedge_lot=0.17,
    target=159.0,
    profit=162.50
)
```

---

## How to Execute Successfully

### Pre-Execution Checklist

| Item | Verification |
|------|---|
| **MT5 Hedge Instance** | Running and logged in to hedge account (via connection manager) |
| **MT5 Maven Instance** | Running and logged in (if using funded trades) |
| **Slots Configured** | Maven accounts registered in slots; check `list_accounts()` |
| **Slots Active** | Required slots marked `is_active=True` |
| **Challenge Configured** | Settings applied; Compute shows reasonable lot sizes |
| **Spread Check** | Market spread is acceptable (engine validates automatically) |
| **Margin Check** | Free margin on hedge and each Maven slot > margin_requirement |
| **Drawdown Safe** | Drawdown usage < 80% (check via `get_drawdown_guardrail()`) |

### Execution Modes (Which to Use)

| Mode | Send to | When to Use |
|------|---------|-----------|
| **Hedge + Funded** | Hedge (MT5) then Maven slots | Standard: reduces net exposure, requires both MT5 instances |
| **Funded Only** | Maven slots only | If hedge is unavailable; pure funded-side trading |
| **Hedge Only** | Hedge (MT5) only | Testing, or if Maven slots are being serviced |

### Step-by-Step Execution

1. **Load or Create Challenge Configuration**
   - Dashboard: Challenge widget → input account size, fees, limits.
   - Or: Load a saved template (e.g., "Maven 5K").

2. **Click Compute**
   - Engine calculates `funded_lot_size`, `hedge_lot_size`, margins, recovery target.
   - Review the results for reasonableness.

3. **Activate Required Maven Slots**
   - Dashboard: Accounts Grid → click to select/mark active.
   - Or: Programmatically `system.set_account_active(slot_id, True)`.

4. **Set Trading Parameters**
   - Trading Controls widget:
     - **Execution Mode** (dropdown)
     - **Volume/Lots** (set to `funded_lot_size` from Compute)
     - **TP (pips)** (e.g., 10)
     - **SL (pips)** (e.g., 20)
     - **Symbol** (e.g., US100)
     - **Comment** (optional)

5. **Check Trading Enabled**
   - Ensure **Set Trading Enabled** toggle is ON (not disabled).

6. **Execute**
   - Click **Buy** or **Sell**.
   - System validates:
     - Spread acceptable?
     - Margin sufficient?
     - Active accounts available?
   - If all OK:
     - Hedge order placed (if Hedge + Funded mode).
     - Wait ~20–50ms (configurable).
     - Maven orders placed (one per active slot).
     - All trades logged to execution log.

7. **Monitor**
   - Accounts Grid updates with latest P&L in real-time.
   - Recovery Ledger captures hedge losses (if applicable).
   - Status bar shows green (healthy) or yellow/red (issue) for Market Data and Execution Engine.

### Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Orders not placed to Maven | No active slots OR Maven instance not connected | Check Accounts Grid; ensure slots marked active; restart Maven MT5 |
| Hedge order fails | Hedge instance not running or logged in | Start hedge MT5; verify login credentials; check connection manager logs |
| Spread too wide | Market condition; no liquidity | Wait for better spread; try different symbol |
| Margin exceeded | Lot sizes too large OR account equity too low | Reduce lot size; use Conservative mode; ensure adequate funding |
| Drawdown limit triggered | Too many losing trades | Use Conservative mode; reduce lot sizes; check daily total loss |
| Trades logged but P&L not shown | Data feed delay or connection hiccup | Check Market Data indicator; restart if red; ensure MT5 is streaming |

---

## Code Reference

### Key Files & Functions

| Module | File | Key Functions |
|--------|------|---|
| **Orchestrator** | `app/core/orchestrator.py` | `configure_prop_challenge()`, `calculate_dynamic_hedge_plan()`, `execute_buy_order()`, `execute_sell_order()`, `record_hedge_loss()`, `get_drawdown_guardrail()` |
| **Fleet Manager** | `app/account_manager/fleet_manager.py` | `add_account()`, `set_account_active()`, `get_active_accounts()`, `get_account_credentials()`, `list_accounts()` |
| **Prop Risk Engine** | `app/recovery_engine/prop_risk_engine.py` | `configure_prop_challenge()`, `compute_dynamic_hedge()`, `save_template()`, `load_template()` |
| **Config** | `app/utils/config.py` | `get_config()`, `set()`, `get()` (dot notation) |
| **Constants** | `app/utils/constants.py` | `MAVEN_ACCOUNT_SLOTS`, `MAVEN_PHASE_1`, `MAVEN_PHASE_2` |
| **Execution Engine** | `app/execution_engine/sync_executor.py` | `execute_synchronized_trade()`, `close_all_positions()` |
| **Risk Manager** | `app/risk_management/safety_monitor.py` | `get_status()`, `validate_spread()`, `get_drawdown_guardrail()` |

### Quick API Examples

**Initialize system:**
```python
from app.core.orchestrator import get_system
system = get_system()
```

**Configure challenge:**
```python
summary = system.configure_prop_challenge({
    "account_size": 5000.0,
    "purchase_fee": 59.0,
    "profit_target_pct": 8.0,
    "daily_drawdown_pct": 5.0,
    "overall_drawdown_pct": 10.0,
    "max_lots_allowed": 5.0,
    "profit_split_pct": 80.0,
    "recovery_mode": "balanced"
})
```

**Compute hedge plan:**
```python
plan = system.calculate_dynamic_hedge_plan({
    "symbol": "US100",
    "stop_loss_pips": 20,
    "take_profit_pips": 10,
    "desired_surplus": 100.0,
    "risk_per_trade_pct": 0.5,
    "recovery_deficit": 0.0,
    "recovery_mode": "balanced"
})
```

**Add Maven account:**
```python
from app.account_manager.fleet_manager import TradingPhase
system.add_maven_account(
    slot_id=1,
    account_number=123456,
    password="pass",
    server="FXOpen-MT5",
    phase=TradingPhase.PHASE_1
)
system.set_account_active(1, True)
```

**Execute trade (async):**
```python
import asyncio
success, results = await system.execute_buy_order(
    symbol="US100",
    lot_size=1.25,
    use_hedge=True,
    use_maven=True,
    tp_pips=10,
    sl_pips=20
)
```

**Record hedge loss:**
```python
system.record_hedge_loss(
    cycle_id="20260510_loss_1",
    account_number=123456,
    hedge_loss=100.0,
    fee=59.0
)
```

---

## Summary

**Marvel Trading Dashboard** coordinates three core modules:

1. **Maven Fleet Slots:** Manage multiple funded accounts as a coordinated fleet. Each slot holds credentials and metadata.
2. **Challenge Configuration:** Define prop-firm rules (account size, profit target, drawdown limits) and derive dollar limits.
3. **Recovery Modes:** Scale hedge sizing (conservative/balanced/aggressive) to balance recovery speed vs. per-trade risk.

**Execution flow:**
- Set challenge configuration → Compute lot sizes → Activate slots → Execute trade (Hedge + Funded) → Monitor execution ledger → Record losses → Plan recovery.

**Examples provided:**
- **Example 1:** Single 5K account setup with US100 trades.
- **Example 2:** Multi-slot fleet (3 accounts) trading EURUSD.

Refer to [CODE_REFERENCE](#code-reference) for API details and see the `USER_GUIDE.md` for end-user workflows.

---

**Last Updated:** May 10, 2026

**Questions?** See `README.md` or contact the maintainer.
