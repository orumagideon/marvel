# MARVEL TRADING DASHBOARD - TESTING CHECKLIST

## Quick Start: Test Everything in 5 Minutes

```bash
# Run all tests with one command
python3 quick_test.py

# Run comprehensive system tests
python3 test_suite.py

# Run diagnostics
python3 diagnostics.py

# View logs
tail -f logs/marvel_*.log
```

---

## Test Level 1: Immediate Validation (2 minutes)

### Quick Verification Commands

```bash
# 1. Verify project structure
ls -la app/ data/ logs/
# Expected: Should show all 11 directories

# 2. Test imports
python3 -c "
from app.utils.config import get_config
from app.utils.logger import get_logger
from app.account_manager.fleet_manager import AccountManager
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
print('✓ All core modules import successfully')
"

# 3. Verify configuration
python3 -c "
from app.utils.config import get_config
config = get_config()
print(f'✓ Config loaded: {config.get_trading_config()}')
"

# 4. Test logging
python3 -c "
from app.utils.logger import get_logger
logger = get_logger()
logger.info('Test message')
print('✓ Logging system working')
"

# 5. Verify logs created
ls -lh logs/
# Expected: marvel_YYYYMMDD.log, trades.jsonl, recovery.jsonl
```

### Expected Results
- ✓ All imports successful
- ✓ Configuration loaded from data/config.json
- ✓ Log files created in logs/ directory
- ✓ No errors in output

---

## Test Level 2: Unit Tests (3 minutes)

### Run Full Test Suite

```bash
python3 test_suite.py
```

### Expected Output
```
Ran 9 tests

✓ test_encrypt_decrypt ...................... PASS
✓ test_invalid_credentials .................. PASS
✓ test_recovery_calculation ................. PASS
✓ test_hedge_lot_sizing ..................... PASS
✓ test_account_creation ..................... PASS
✓ test_account_activation ................... PASS
✓ test_hedge_loss_recording ................. PASS
✗ test_equity_tracking ...................... ERROR (MT5 not available on Linux)
✗ test_drawdown_monitoring .................. ERROR (MT5 not available on Linux)

Ran 9 tests - 7 PASSED, 2 ERRORS (expected on Linux)
OK
```

### Pass Criteria
- ✓ At least 7 of 9 tests pass
- ✓ Failures are only MT5-related (expected on non-Windows)
- ✓ No critical module errors

---

## Test Level 3: Component Testing (5 minutes)

### 3.1 Encryption System

```bash
python3 -c "
from app.utils.crypto import CredentialVault
vault = CredentialVault('test.enc')
vault.encrypt_credentials({'test': {'pwd': 'secret123'}})
data = vault.decrypt_credentials()
assert data['test']['pwd'] == 'secret123'
print('✓ Encryption working')
"
```

### 3.2 Recovery Engine

```bash
python3 -c "
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
engine = HedgeRecoveryEngine()
target = engine.calculate_recovery_target([50.0, 75.0], 100.0)
lot = engine.calculate_hedge_lot_size(target, 400.0)
print(f'✓ Recovery target: \${target} (expected \$225.00)')
print(f'✓ Hedge lot: {lot:.2f}L (expected 0.06L)')
assert abs(target - 225.0) < 0.01
assert 0.05 < lot < 0.07
"
```

### 3.3 Account Manager

```bash
python3 -c "
from app.account_manager.fleet_manager import AccountManager, TradingPhase
mgr = AccountManager('test_acct.json')
mgr.add_account(1, 123456, 'pwd', 'srv', TradingPhase.PHASE_1, 'Test')
acc = mgr.get_account(1)
assert acc.account_number == 123456
mgr.set_account_active(1, True)
active = mgr.get_active_accounts()
assert len(active) == 1
print('✓ Account management working')
"
```

### 3.4 Configuration Persistence

```bash
python3 -c "
from app.utils.config import get_config
config = get_config()
config.set('test.param', 'value123')
assert config.get('test.param') == 'value123'
print('✓ Configuration persistence working')
"
```

### 3.5 Logging Output

```bash
python3 -c "
from app.utils.logger import get_logger
logger = get_logger()
logger.log_trade({'symbol': 'US100', 'type': 'buy'})
logger.log_recovery({'action': 'test'})
logger.log_risk_event('TEST', {})
print('✓ All log types working')
"
```

### Pass Criteria
- ✓ All component tests complete without errors
- ✓ Recovery calculations match expected values
- ✓ Configuration persists across invocations
- ✓ Log files created with proper entries

---

## Test Level 4: Diagnostics & Validation (2 minutes)

```bash
# Run system diagnostics
python3 diagnostics.py

# Expected output:
# ✓ Configuration...................... PASS
# ✓ Project structure.................. PASS
# ✓ Required directories............... PASS
# ✓ Permissions....................... PASS (or PARTIAL)
# ✓ Python modules.................... PASS
# ✓ Encryption system................. PASS
# ✓ Recovery engine................... PASS
# ✓ Account manager................... PASS
# ✓ Logging system.................... PASS
```

### Verify Generated Files

```bash
# Check configuration
ls -l data/config.json
cat data/config.json | python3 -m json.tool | head -20

# Check logs
ls -lh logs/
cat logs/marvel_*.log | head -5

# Check accounts (if created)
cat data/accounts.json | python3 -m json.tool
```

---

## Test Level 5: Integration Testing (Windows Only)

> **Note**: These tests require Windows with MetaTrader5 installed

### 5.1 Setup Wizard

```bash
python3 setup_wizard.py
# Follow prompts to:
#   1. Configure MT5 terminal paths
#   2. Add test Maven account
#   3. Set risk parameters
```

### 5.2 MT5 Connection Test

```bash
python3 -c "
from app.core.orchestrator import get_system
system = get_system()
status = system.get_system_status()
print(status)
# Expected: System initialized, instances disconnected
"
```

### 5.3 Account Login Test

```bash
python3 -c "
from app.core.orchestrator import get_system
system = get_system()
system.initialize_maven_instance('C:\\\\Program Files\\\\MetaTrader 5')
success = system.login_maven_account(YOUR_ACCOUNT, 'PASSWORD', 'SERVER')
print(f'Login success: {success}')
"
```

### 5.4 Market Data Test

```bash
python3 -c "
from app.core.orchestrator import get_system
system = get_system()
data = system.get_market_data('US100')
print(f'US100 - Bid: {data[\"bid\"]}, Ask: {data[\"ask\"]}')
"
```

### 5.5 Dashboard Test

```bash
python3 main.py
# Expected:
#   - Dashboard window opens
#   - Status indicators show connection state
#   - Market data displayed
#   - BUY/SELL/CLOSE buttons functional
```

---

## Automated Test Runner

### One-Command Test Suite

```bash
python3 quick_test.py
```

This runs all 8 test groups:
1. Project Structure
2. Core Imports
3. Configuration
4. Logging System
5. Recovery Engine
6. Account Management
7. Encryption
8. Unit Tests

Expected output shows test results and summary.

---

## Test Result Summary Template

After running tests, fill out this checklist:

```
Date: _______________
Environment: [ ] Linux [ ] Windows [ ] VPS
Python Version: _______

CORE TESTS:
[ ] ✓ Project structure verified
[ ] ✓ All modules import successfully
[ ] ✓ Configuration system working
[ ] ✓ Logging system functional
[ ] ✓ Recovery engine calculations correct
[ ] ✓ Account manager working
[ ] ✓ Encryption system secure
[ ] ✓ 7/9 unit tests pass (or 9/9 on Windows)

FILE VERIFICATION:
[ ] ✓ logs/marvel_YYYYMMDD.log exists
[ ] ✓ logs/trades.jsonl exists
[ ] ✓ logs/recovery.jsonl exists
[ ] ✓ data/config.json exists
[ ] ✓ data/accounts.json created (if accounts added)
[ ] ✓ All 22 Python modules present

MANUAL TESTS (if running on Windows with MT5):
[ ] ✓ MT5 instances initialize
[ ] ✓ Account login succeeds
[ ] ✓ Market data retrieves correctly
[ ] ✓ Test trade executes
[ ] ✓ Recovery ledger logs correctly
[ ] ✓ Dashboard UI launches

OVERALL STATUS:
[ ] All tests PASSED - System ready for deployment
[ ] Some tests FAILED - See troubleshooting below
```

---

## Troubleshooting

### Problem: ImportError: No module named 'MetaTrader5'
**Solution**: Normal on Linux. MT5 module only available on Windows with MetaTrader5 terminal installed.
- Linux development: 7/9 tests should pass
- Windows with MT5: All 9 tests should pass

### Problem: FileNotFoundError in logs or data directories
**Solution**: Create directories manually
```bash
mkdir -p logs data
```

### Problem: PermissionError writing to logs or data
**Solution**: Fix directory permissions
```bash
chmod 755 logs data
chmod 644 data/*
```

### Problem: JSON decode error in config
**Solution**: Reset configuration
```bash
rm data/config.json
# System will regenerate on next run
python3 diagnostics.py
```

### Problem: Encryption test fails
**Solution**: Delete test encryption files
```bash
rm data/*.enc*
rm test*.enc*
```

### Problem: Unit tests timeout or hang
**Solution**: Run with explicit test
```bash
python3 -m pytest test_suite.py -v --tb=short
# or
python3 test_suite.py -k "not risk" # Skip risk management tests
```

---

## Performance Benchmarks

After testing, you should see:
- ✓ Test suite runs in < 10 seconds (excluding MT5 connection tests)
- ✓ Quick test completes in < 5 seconds
- ✓ Diagnostics runs in < 2 seconds
- ✓ Configuration loads in < 100ms
- ✓ Logger writes in < 10ms

---

## Next Steps After Successful Tests

If all tests pass:

1. **View Documentation**
   ```bash
   cat README.md              # Feature overview
   cat QUICKSTART.md          # 5-minute setup
   cat ARCHITECTURE.md        # System design
   cat API_REFERENCE.md       # Complete API
   ```

2. **Deploy to Windows VPS**
   - Follow DEPLOYMENT.md procedures
   - Run setup_wizard.py
   - Configure MT5 terminals
   - Test with paper trading

3. **Monitor in Production**
   - Watch logs in real-time: `tail -f logs/marvel_*.log`
   - Check recovery ledger: `tail recovery.jsonl`
   - Verify risk events: `tail logs/risk_events.jsonl`

---

## Test Documentation

- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Comprehensive testing procedures
- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API documentation
