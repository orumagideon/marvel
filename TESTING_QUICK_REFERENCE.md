# MARVEL TESTING - QUICK REFERENCE CARD

## 🚀 START HERE: One-Command Test

```bash
cd /home/oruma/marvel
python3 quick_test.py
```

**Expected Output:**
- ✓ PASS - Project Structure
- ✓ PASS - Configuration
- ✓ PASS - Logging System
- ✓ PASS - Recovery Engine
- ✓ PASS - Account Manager
- ✓ PASS - Unit Tests
- Total: 6/8 test groups passed (MT5 tests expected to fail on Linux)

---

## 📋 Testing Commands by Level

### LEVEL 1: Immediate Checks (30 seconds each)

| Test | Command | Expected |
|------|---------|----------|
| **Structure** | `ls -la app/ logs/ data/` | All directories exist |
| **Imports** | `python3 -c "from app.utils.config import get_config; print('OK')"` | Prints "OK" |
| **Config** | `python3 -c "from app.utils.config import get_config; c = get_config(); print(c.get('trading.primary_symbol'))"` | Prints "US100" |
| **Logger** | `python3 -c "from app.utils.logger import get_logger; get_logger().info('test'); print('OK')"` | Prints "OK" + creates log |
| **Files** | `cat data/config.json \| python3 -m json.tool \| head -10` | Valid JSON |

---

### LEVEL 2: Component Tests (1 minute)

#### Encryption Test
```bash
python3 -c "
from app.utils.crypto import CredentialVault
vault = CredentialVault('test.enc')
vault.encrypt_credentials({'test': {'pwd': 'secret123'}})
data = vault.decrypt_credentials()
print(f'✓ Encryption: {data[\"test\"][\"pwd\"] == \"secret123\"}')
"
```

#### Recovery Engine Test
```bash
python3 -c "
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
engine = HedgeRecoveryEngine()
target = engine.calculate_recovery_target([50.0, 75.0], 100.0)
lot = engine.calculate_hedge_lot_size(target, 400.0)
print(f'✓ Target: \${target} (expected \$225.0)')
print(f'✓ Lot: {lot:.2f}L (expected 0.06L)')
"
```

#### Account Manager Test
```bash
python3 -c "
from app.account_manager.fleet_manager import AccountManager, TradingPhase
mgr = AccountManager('test.json')
mgr.add_account(1, 123456, 'pwd', 'srv', TradingPhase.PHASE_1)
acc = mgr.get_account(1)
print(f'✓ Account: {acc.account_number}')
"
```

#### Configuration Persistence Test
```bash
python3 -c "
from app.utils.config import get_config
config = get_config()
config.set('test.xyz', 'value123')
"
python3 -c "
from app.utils.config import get_config
config = get_config()
result = config.get('test.xyz')
print(f'✓ Persistence: {result == \"value123\"}')
"
```

---

### LEVEL 3: Full Test Suite (2 minutes)

```bash
# Run all unit tests
python3 test_suite.py

# Expected output:
# Ran 9 tests
# ✓ 7 PASSED (encryption, recovery, accounts)
# ✗ 2 ERRORS (MT5-dependent on Linux)
```

---

### LEVEL 4: Diagnostics (1 minute)

```bash
# Full system diagnostic
python3 diagnostics.py

# Expected: All checks pass or show helpful warnings
```

---

### LEVEL 5: View Generated Files

```bash
# Configuration
cat data/config.json | python3 -m json.tool

# Application logs
tail -20 logs/marvel_*.log

# Trade logs
cat logs/trades.jsonl | python3 -m json.tool

# Recovery logs
cat logs/recovery.jsonl | python3 -m json.tool

# Accounts
cat data/accounts.json | python3 -m json.tool
```

---

## ✅ Test Verification Checklist

After running tests, verify:

```bash
# Logs created?
ls -lh logs/marvel_*.log logs/*.jsonl

# Config created?
ls -la data/config.json

# Python files present?
find app -name "*.py" | wc -l    # Should be 22

# Can import core modules?
python3 -c "
from app.account_manager.fleet_manager import AccountManager
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
from app.utils.logger import get_logger
from app.utils.config import get_config
from app.utils.crypto import CredentialVault
print('✓ All core modules import')
"

# Configuration values correct?
python3 -c "
from app.utils.config import get_config
c = get_config()
assert c.get('trading.primary_symbol') == 'US100'
assert c.get('accounts.default_slots') == 5
assert c.get('risk_management.daily_drawdown_limit') == 400.0
print('✓ Configuration correct')
"

# Recovery calculations work?
python3 -c "
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
engine = HedgeRecoveryEngine()
target = engine.calculate_recovery_target([50.0, 75.0], 100.0)
lot = engine.calculate_hedge_lot_size(target, 400.0)
assert abs(target - 225.0) < 0.01
assert 0.05 < lot < 0.07
print('✓ Recovery engine verified')
"
```

---

## 🐛 Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| `ImportError: No module 'MetaTrader5'` | Normal on Linux - MT5 is Windows-only |
| `FileNotFoundError: logs/` | `mkdir -p logs data` |
| `PermissionError` | `chmod 755 logs data` |
| `JSON decode error` | `rm data/config.json` (system will regenerate) |
| `Encryption key missing` | `rm data/*.enc*` (will regenerate) |
| `Tests hang` | Kill terminal with Ctrl+C, restart |

---

## 📊 Expected Results Summary

### Linux Development Environment
```
✓ 7/9 unit tests pass
✓ 6/8 test groups pass in quick_test.py
✓ All non-MT5 components work
✗ MT5 modules fail to import (expected)
```

### Windows Development Environment
```
✓ 9/9 unit tests pass
✓ 8/8 test groups pass in quick_test.py
✓ All components including MT5 work
✓ Dashboard launches and functions
```

### Windows VPS (After Deployment)
```
✓ All tests pass
✓ MT5 instances connect
✓ Accounts login successfully
✓ Market data flows
✓ Trade execution works
✓ Recovery engine logs
✓ Risk protection active
✓ Dashboard operational
```

---

## 🎯 Next Steps After Testing

### If All Tests Pass ✓
1. Review [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
2. Follow [QUICKSTART.md](QUICKSTART.md) for first use
3. Read [API_REFERENCE.md](API_REFERENCE.md) for detailed API

### If Some Tests Fail ✗
1. Check [Troubleshooting](#-troubleshooting-quick-fixes) above
2. Run `python3 diagnostics.py` for detailed error info
3. Review specific component test output for error messages

### For Windows Deployment
1. Copy all files to Windows VPS
2. Run `python3 setup_wizard.py`
3. Run `python3 test_suite.py` to verify
4. Run `python3 main.py` to launch dashboard

---

## 📖 Documentation Files

- **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** - Detailed testing procedures
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing scenarios
- **[README.md](README.md)** - Project overview and features
- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide

---

## 🔧 Files for Reference

| File | Purpose |
|------|---------|
| `quick_test.py` | One-command comprehensive test |
| `test_suite.py` | Unit tests for all components |
| `diagnostics.py` | System health check |
| `setup_wizard.py` | Initial configuration |
| `main.py` | Launch dashboard (Windows only) |
| `data/config.json` | System configuration |
| `logs/marvel_*.log` | Application logs |
| `logs/trades.jsonl` | Trade execution logs |
| `logs/recovery.jsonl` | Recovery engine logs |

---

**Last Updated:** 2026-05-10  
**Status:** ✓ All testing infrastructure complete and operational
