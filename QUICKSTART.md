# Marvel Trading Dashboard - Quick Start Guide

## Installation (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run setup wizard
python setup_wizard.py

# 3. Verify installation
python diagnostics.py
python test_suite.py

# 4. Launch dashboard
python main.py
```

## Key Controls

### Trading
- **BUY**: Execute synchronized buy across active accounts + hedge
- **SELL**: Execute synchronized sell across active accounts + hedge  
- **CLOSE ALL**: Emergency close all positions immediately
- **Lot Size**: Set position size for all accounts

### Features
- **Hedge Enabled**: Toggle hedge account participation
- **Auto Recovery**: Toggle automatic recovery calculation
- **Account Checkboxes**: Select which accounts participate in next trade

### Status Indicators
- **Green ●**: Connected
- **Gray ●**: Disconnected
- **Orange ●**: Reconnecting
- **Red ●**: Error

## Account Management

```python
# Add Maven account (GUI or programmatic)
system.add_maven_account(
    slot_id=1,
    account_number=123456,
    password="your_password",
    server="MavenPropFirm-Live",
    phase=TradingPhase.PHASE_1
)

# Activate account for trading
system.set_account_active(1, True)

# Execute trade
await system.execute_buy_order("US100", 0.1)
```

## Recovery System

```python
# Record a hedge loss
system.record_hedge_loss(
    cycle_id="20260510_143022",
    account_number=123456,
    hedge_loss=100.0,
    fee=50.0
)

# Get recovery target for next cycle
lot_size, target = system.get_recovery_target([123456])
print(f"Target: ${target}, Hedge Lot: {lot_size}L")

# Record recovery execution
system.record_recovery_execution(
    cycle_id="20260510_143022",
    account_number=123456,
    hedge_lot_executed=0.1,
    target_amount=150.0,
    profit_achieved=155.0
)
```

## Risk Management

```python
# Check account health
health = system.get_account_health(123456)
print(f"Equity: ${health['equity']}, Drawdown: {health['drawdown_percentage']}%")

# Emergency close all
await system.close_all_emergency()
```

## Monitoring

### Logs Location
- **Main**: `/logs/marvel_YYYYMMDD.log`
- **Trades**: `/logs/trades.jsonl`
- **Recovery**: `/logs/recovery.jsonl`
- **Risk Events**: `/logs/risk_events.jsonl`

### View Recent Trades
```bash
tail -n 20 logs/trades.jsonl | python -m json.tool
```

### Check Recovery Status
```bash
python -c "import pandas as pd; print(pd.read_csv('data/recovery_log.csv').tail(10))"
```

## Configuration Files

- **`data/config.json`**: System settings (refresh rates, drawdown limits, etc.)
- **`data/accounts.json`**: Account metadata (no passwords)
- **`data/credentials.enc`**: Encrypted credentials vault
- **`data/recovery_log.csv`**: Recovery history ledger

## Troubleshooting

**MT5 won't connect**
- Verify terminal path in config.json
- Ensure terminal is running
- Check account credentials
- Run: `python diagnostics.py`

**Recovery not working**
- Confirm "Auto Recovery" checkbox is enabled
- Check recovery.jsonl in logs
- Verify hedge losses recorded: `data/recovery_log.csv`

**Trades not executing**
- Verify at least one account is checked
- Check spread isn't too wide
- Verify hedge connection (green light)
- Check free margin (Account Health gauge)

**High CPU/Memory**
- Reduce refresh rates in `data/config.json`
- Increase UI refresh interval
- Disable verbose logging

## Command Line Tools

```bash
# System diagnostics
python diagnostics.py

# Run unit tests
python test_suite.py

# Interactive setup
python setup_wizard.py

# Launch dashboard
python main.py
```

## Production Checklist

- [ ] All 5 Maven accounts configured
- [ ] Hedge account configured with high leverage
- [ ] Test trades executed successfully
- [ ] Recovery ledger has at least one cycle
- [ ] Emergency close tested
- [ ] Drawdown limits verified
- [ ] Logs folder accessible
- [ ] Backup credentials.enc.key to secure location

## Performance Tips

| Action | Impact |
|--------|--------|
| Reduce UI refresh rate | ↓ CPU |
| Enable market data cache | ↓ Network |
| Increase execution delays | ↓ Slippage |
| Disable verbose logging | ↓ Disk I/O |

---

**For detailed documentation, see:**
- `README.md` - Full feature overview
- `ARCHITECTURE.md` - System design
- `DEPLOYMENT.md` - Production deployment
