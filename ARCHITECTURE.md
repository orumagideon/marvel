"""
Marvel Architecture and Design Documentation
Technical specification for trading system
"""

ARCHITECTURE_DOC = """
# MARVEL TRADING SYSTEM - ARCHITECTURE

## System Design Overview

```
┌─────────────────────────────────────────────────────────┐
│                   MARVEL DASHBOARD (UI)                 │
│  CustomTkinter - Professional Dark Theme Interface      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌────────┐  ┌──────────┐  ┌──────────┐
    │ Cmd    │  │ Market   │  │ Health   │
    │ Bus    │  │ Feed     │  │ Monitor  │
    └───┬────┘  └─────┬────┘  └────┬─────┘
        │             │            │
        └─────────────┼────────────┘
                      │
        ┌─────────────▼──────────────┐
        │   MARVEL CORE SYSTEM       │
        │   (Orchestrator)           │
        │                            │
        │  ┌──────────────────────┐  │
        │  │ Session Management   │  │
        │  └──────────────────────┘  │
        └─┬──────┬──────┬──────┬─────┘
          │      │      │      │
    ┌─────▼─┐┌──▼──┐┌──▼──┐┌──▼──┐
    │ MT5   ││Acct │││Risk ││Exe  │
    │Bridge ││Mgr  ││Mgmt  ││cution│
    └──┬────┘└──┬──┘└──┬──┘└──┬───┘
       │         │      │      │
       │    ┌────▼───┐  │      │
       │    │Recovery│  │      │
       │    │Engine  │  │      │
       │    └────┬───┘  │      │
       │         │      │      │
       ▼         ▼      ▼      ▼
    ┌──────────────────────────────┐
    │   Persistent Storage Layer   │
    │  (Encrypted + JSON + CSV)    │
    └──────────────────────────────┘
        │           │           │
        ▼           ▼           ▼
    ┌────────┐ ┌────────┐ ┌──────────┐
    │Accounts│ │Recovery│ │Config    │
    │        │ │Ledger  │ │Settings  │
    └────────┘ └────────┘ └──────────┘
```

## Module Architecture

### 1. Core Orchestrator (orchestrator.py)
**Responsibility**: Central system coordinator
- Session management
- Component lifecycle
- Cross-module communication
- State synchronization

**Key Methods**:
```python
- initialize_maven_instance()
- initialize_hedge_instance()
- execute_buy_order() / execute_sell_order()
- close_all_emergency()
- get_system_status()
```

### 2. MT5 Bridge (mt5_bridge/)
**Responsibility**: Dual MT5 terminal management

**Components**:
- `connection_manager.py`: Connection lifecycle and state
- `market_data.py`: Real-time data fetching

**Architecture**:
```
MT5ConnectionManager
├── Instance A (Maven Fleet)
│   ├── Connection State
│   ├── Auto-Reconnect
│   └── Account Switching
└── Instance B (Hedge Account)
    ├── Persistent Connection
    ├── Silent Reconnect
    └── Isolated Session
```

### 3. Account Manager (account_manager/)
**Responsibility**: Maven fleet configuration

**Features**:
- 5+ account slots
- Secure credential storage (Fernet encryption)
- Account metadata persistence
- Dynamic activation

**Data Model**:
```
MavenAccount
├── slot_id: int
├── account_number: int
├── password: str (encrypted)
├── server: str
├── phase: TradingPhase
├── is_active: bool
└── display_name: str
```

### 4. Recovery Engine (recovery_engine/)
**Responsibility**: Hedge calculation and loss tracking

**Recovery Formula**:
```
TargetProfit = ∑(ActiveFees) + DesiredSurplus + OutstandingLosses

HedgeLot = TargetProfit / (DrawdownDistance × PipValue)
```

**Persistence**:
- CSV ledger for historical tracking
- JSON for outstanding losses
- Automatic cycle-to-cycle carryover

### 5. Execution Engine (execution_engine/)
**Responsibility**: Synchronized trade execution

**Execution Sequence**:
```
1. Validate trade (spread, margin, drawdown)
2. Execute hedge trade (if enabled)
3. Wait 10ms (latency guard)
4. Execute Maven fleet orders (parallel per account)
5. Log execution with latency metrics
6. Update recovery tracking
```

**Key Features**:
- Asynchronous execution queue
- Slippage monitoring
- Duplicate prevention
- Execution history logging

### 6. Risk Management (risk_management/)
**Responsibility**: Safety and emergency protection

**Protection Layers**:
1. Drawdown Monitoring
   - Real-time tracking
   - Critical threshold alerts
   - Auto-stop at limit

2. Equity Safeguards
   - Free margin validation
   - Ratio-based limits
   - Liquidation prevention

3. Trade Validation
   - Spread checks
   - Maximum slippage guards
   - Lot size validation

4. Emergency Systems
   - CLOSE ALL button
   - Emergency stop flag
   - Audit logging

### 7. UI Dashboard (ui/)
**Responsibility**: Professional trading interface

**Components**:
- `MarketFeedWidget`: Live bid/ask/spread
- `AccountHealthWidget`: Drawdown gauge
- `StatusIndicatorWidget`: Connection lights
- `TradingControlsWidget`: BUY/SELL/CLOSE
- `AccountGridWidget`: Fleet management

## Data Flow

### Trade Execution Flow
```
User clicks BUY
    ↓
UI validates input
    ↓
Core.execute_buy_order()
    ↓
RiskManager.validate_trade_execution()
    ↓
ExecutionEngine.execute_synchronized_trade()
    ├─→ Hedge trade (Instance B)
    ├─→ Wait 10ms
    └─→ Maven trades (Instance A, parallel)
    ↓
Logger.log_trade() → trade.jsonl
    ↓
Recovery tracking if hedge loses
    ↓
UI updates with results
```

### Recovery Cycle Flow
```
Maven account passes
    ↓
Hedge account has loss
    ↓
Recovery.record_hedge_loss()
    ↓
Loss persisted in recovery_log.csv
    ↓
Next trade cycle starts
    ↓
Recovery.estimate_next_recovery_lot()
    ↓
Calculate new hedge lot size
    ↓
Execute recovery with larger lot
    ↓
Recovery.record_recovery_execution()
    ↓
Update ledger status
```

## Encryption and Security

### Credential Storage
```
MavenAccount credentials
    ↓
Fernet cipher (AES-256)
    ↓
Encrypted JSON → credentials.enc
    ↓
Key stored separately → credentials.enc.key
    └─→ File permissions: 0o600 (owner read-only)
```

### Never Stored Unencrypted
- Account passwords
- Server addresses (in accounts DB)
- Hedge account credentials
- Trading logs with sensitive data

## Logging Strategy

### Log Types
1. **Trade Logs** (trade.jsonl)
   - Symbol, type, lot, price, slippage, latency
   - Account numbers, timestamps
   - Execution status

2. **Recovery Logs** (recovery.jsonl)
   - Hedge losses recorded
   - Recovery targets calculated
   - Lot sizes determined
   - Recovery executions

3. **Risk Events** (risk_events.jsonl)
   - Drawdown exceeded
   - Critical equity breached
   - Emergency closes
   - Protection triggers

4. **Main Logs** (marvel_YYYYMMDD.log)
   - Connection events
   - System errors
   - Debug information
   - Audit trail

## Performance Characteristics

### Latency Budget
```
User input          : <50ms
Risk validation     : ~5ms
Hedge trade exec    : 50-150ms (MT5)
Latency guard       : 10ms
Maven trades        : 50-200ms per account
UI update           : <100ms
Total               : 200-400ms typical
```

### Resource Usage
```
Memory:   200-400MB (baseline)
CPU:      15-25% (idle)
Network:  <1Mbps average
Disk:     ~50MB/day logs
```

## Scalability Considerations

### Current Design
- 5-20 Maven account slots
- 2 MT5 instances (configurable)
- Asynchronous execution (non-blocking)

### Future Expansion
- Multi-symbol support (currently US100)
- Multiple hedge accounts
- Distributed MT5 bridges
- Cloud-based ledger sync
- Multi-user dashboard instances

## Security Considerations

### Implemented
- Encrypted credential storage
- No hardcoded credentials
- Structured exception handling
- Connection state validation
- Trade audit logging

### Recommended (Future)
- Multi-factor authentication
- IP whitelisting for remote access
- SSL/TLS for any remote connections
- Hardware security module integration
- Cryptographic signing of ledgers

---

**Architecture Version**: 1.0.0
**Last Updated**: May 2026
"""

if __name__ == "__main__":
    print(ARCHITECTURE_DOC)
