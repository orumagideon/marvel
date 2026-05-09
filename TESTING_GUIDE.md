"""
MARVEL TRADING DASHBOARD - TESTING GUIDE
Complete testing procedures and validation steps
"""

# ============================================================================
# LEVEL 1: DIAGNOSTIC TESTING (No Dependencies Required)
# ============================================================================

DIAGNOSTIC_TEST = """
COMMAND: python3 diagnostics.py

This checks:
  ✓ Configuration file setup
  ✓ Required directories exist
  ✓ Account configuration
  ✓ File permissions
  ✓ Data directory structure

EXPECTED OUTPUT:
  Configuration............ ✓ PASS
  Paths..................... ✓ PASS (or PARTIAL if MT5 not installed)
  Directories.............. ✓ PASS
  Accounts................. ✓ PASS (or INFO if none configured)
"""

# ============================================================================
# LEVEL 2: UNIT TESTING (Core Components)
# ============================================================================

UNIT_TEST = """
COMMAND: python3 test_suite.py

Tests:
  ✓ Credential encryption/decryption
  ✓ Recovery target calculations
  ✓ Hedge lot sizing
  ✓ Account management
  ✓ Account activation
  ✓ Loss recording
  ✓ Risk management basics

EXPECTED OUTPUT:
  Ran 9 tests
  ✓ 7 PASSED (encryption, recovery, accounts)
  ✗ 2 ERRORS (risk management - requires MT5)

NOTE: MetaTrader5 module not available on Linux development machine
      Tests pass on Windows with MT5 installed
"""

# ============================================================================
# LEVEL 3: CONFIGURATION TESTING
# ============================================================================

CONFIGURATION_TEST = """
COMMAND: python3 -c "from app.utils.config import get_config; c = get_config(); print(c.config)"

Tests:
  ✓ Configuration file creation
  ✓ Default values loaded
  ✓ JSON persistence
  ✓ Dot notation access
  ✓ Section accessors

EXAMPLE OUTPUT:
{
  'mt5': {'maven_terminal_path': '', 'hedge_terminal_path': '', ...},
  'accounts': {'default_slots': 5, ...},
  'trading': {'primary_symbol': 'US100', ...},
  'recovery': {'desired_surplus': 100.0, ...},
  ...
}
"""

# ============================================================================
# LEVEL 4: COMPONENT TESTING (Individual Modules)
# ============================================================================

COMPONENT_TEST = """
ENCRYPTION TEST:
  python3 -c "
from app.utils.crypto import CredentialVault
vault = CredentialVault('test.enc')
vault.encrypt_credentials({'test': {'pwd': 'secret'}})
data = vault.decrypt_credentials()
print('Encryption OK' if data else 'FAILED')
"

LOGGER TEST:
  python3 -c "
from app.utils.logger import get_logger
logger = get_logger()
logger.info('Test message')
logger.log_trade({'action': 'test'})
print('Logging OK')
"

CONFIG TEST:
  python3 -c "
from app.utils.config import get_config
config = get_config()
config.set('test.value', 123)
result = config.get('test.value')
print(f'Config OK: {result}')
"

RECOVERY TEST:
  python3 -c "
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
engine = HedgeRecoveryEngine('test_recovery.csv')
target = engine.calculate_recovery_target([50, 75], 100)
lot = engine.calculate_hedge_lot_size(target)
print(f'Recovery OK: Target={target}, Lot={lot}')
"

ACCOUNT MANAGER TEST:
  python3 -c "
from app.account_manager.fleet_manager import AccountManager, TradingPhase
mgr = AccountManager('test_acct.json')
mgr.add_account(1, 123456, 'pwd', 'srv', TradingPhase.PHASE_1)
acc = mgr.get_account(1)
print(f'Account Manager OK: {acc.account_number}')
"
"""

# ============================================================================
# LEVEL 5: INTEGRATION TESTING (On Windows with MT5)
# ============================================================================

INTEGRATION_TEST = """
WINDOWS ONLY (Requires MetaTrader5 installed):

1. SETUP TEST:
   python setup_wizard.py
   - Configure MT5 paths
   - Add test Maven account
   - Verify configuration saved

2. CONNECTION TEST:
   python3 -c "
from app.core.orchestrator import get_system
system = get_system()
status = system.get_system_status()
print(status)
"
   Expected: System initialized, instances disconnected

3. LOGIN TEST:
   python3 -c "
from app.core.orchestrator import get_system
system = get_system()
system.initialize_maven_instance('C:\\\\Program Files\\\\MetaTrader 5')
success = system.login_maven_account(YOUR_ACCOUNT, 'PASSWORD', 'SERVER')
print(f'Login: {success}')
"

4. MARKET DATA TEST:
   python3 -c "
from app.core.orchestrator import get_system
system = get_system()
data = system.get_market_data('US100')
if data:
    print(f'US100 - Bid: {data[\"bid\"]}, Ask: {data[\"ask\"]}')
"

5. TRADE EXECUTION TEST:
   python3 -c "
import asyncio
from app.core.orchestrator import get_system
system = get_system()
success, results = asyncio.run(system.execute_buy_order('US100', 0.01))
print(f'Trade result: {success}')
"

6. UI TEST:
   python main.py
   - Verify dashboard loads
   - Check status indicators
   - Test BUY/SELL buttons
   - Verify logs created
"""

# ============================================================================
# QUICK TEST CHECKLIST
# ============================================================================

QUICK_CHECKLIST = """
✓ Step 1: File Structure
  python3 -c "import os; print(len([f for f in os.walk('app') if f[2]]))"
  Expected: Should show multiple directories

✓ Step 2: Imports
  python3 -c "from app.core.orchestrator import get_system; print('Import OK')"

✓ Step 3: Configuration
  python3 -c "from app.utils.config import get_config; c = get_config(); print('Config OK')"

✓ Step 4: Logging
  python3 -c "from app.utils.logger import get_logger; logger = get_logger(); logger.info('OK')"

✓ Step 5: Encryption
  python3 -c "from app.utils.crypto import CredentialVault; v = CredentialVault(); print('Crypto OK')"

✓ Step 6: Recovery
  python3 -c "from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine; e = HedgeRecoveryEngine(); print('Recovery OK')"

✓ Step 7: Accounts
  python3 -c "from app.account_manager.fleet_manager import AccountManager; m = AccountManager(); print('Accounts OK')"

✓ Step 8: Diagnostics
  python3 diagnostics.py

✓ Step 9: Unit Tests
  python3 test_suite.py

✓ Step 10: Setup Wizard
  python3 setup_wizard.py
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

TROUBLESHOOTING = """
PROBLEM: ImportError: No module named 'MetaTrader5'
SOLUTION: This is normal on Linux. MT5 only available on Windows with terminal.
          Tests that don't require MT5 will pass (7/9 tests should pass)

PROBLEM: FileNotFoundError: [Errno 2] No such file or directory: 'data/...'
SOLUTION: Run: mkdir -p data logs
          Directories should auto-create but can create manually

PROBLEM: PermissionError when writing logs
SOLUTION: Run: chmod 755 logs data
          Ensure write permissions on directories

PROBLEM: JSON decode error
SOLUTION: data/config.json or accounts.json corrupted
          Delete and let system regenerate:
          rm data/config.json data/accounts.json

PROBLEM: Encryption key not found
SOLUTION: Delete test encryption files and regenerate:
          rm data/credentials.enc*

PROBLEM: Tests fail with "Cannot connect to MT5"
SOLUTION: Normal on Linux. Only test on Windows with MT5 installed.
          Focus on non-MT5 tests (encryption, recovery, accounts)
"""

# ============================================================================
# RUNNING TESTS IN DIFFERENT ENVIRONMENTS
# ============================================================================

ENVIRONMENT_TESTS = """
LINUX DEVELOPMENT MACHINE:
  ✓ Diagnostics (basic structure check)
  ✓ Unit tests (7 of 9 pass - encryption, recovery, accounts)
  ✓ Configuration testing
  ✓ Logger testing
  ✓ Crypto testing
  ✗ MT5 connection tests (no terminal available)
  ✗ Dashboard UI testing (no Tkinter display)

  COMMAND: python3 test_suite.py

WINDOWS DEVELOPMENT MACHINE:
  ✓ ALL unit tests (9/9)
  ✓ Diagnostics
  ✓ Configuration
  ✓ Component testing
  ✓ MT5 connection tests (if terminal installed)
  ✓ Dashboard launch (if display available)

  COMMAND: python3 test_suite.py && python3 main.py

WINDOWS VPS DEPLOYMENT:
  ✓ ALL unit tests
  ✓ Diagnostics
  ✓ Setup wizard validation
  ✓ MT5 instance initialization
  ✓ Account login verification
  ✓ Market data retrieval
  ✓ Trade execution (paper trading first)
  ✓ Recovery ledger creation
  ✓ Risk protection activation
  ✓ Emergency close functionality

  STEPS:
    1. python3 setup_wizard.py
    2. python3 diagnostics.py
    3. python3 test_suite.py
    4. python3 main.py
    5. Execute test trades
    6. Verify logs
"""

# ============================================================================
# VALIDATION CHECKLIST AFTER TESTING
# ============================================================================

VALIDATION_CHECKLIST = """
AFTER RUNNING TESTS, VERIFY:

✓ Logs Created:
  ls -la logs/
  Should show: marvel_YYYYMMDD.log

✓ Configuration Generated:
  ls -la data/config.json
  Should show JSON with settings

✓ Encryption Working:
  ls -la data/*.enc* (if you ran encryption tests)
  Should show encrypted vault and key

✓ Recovery Ledger:
  ls -la data/recovery_log.csv (if you ran recovery tests)
  Should show CSV with headers

✓ Test Coverage:
  python3 test_suite.py 2>&1 | grep "Ran"
  Should show: Ran 9 tests

✓ All Modules Import:
  python3 -c "
from app.core.orchestrator import get_system
from app.mt5_bridge.connection_manager import MT5ConnectionManager
from app.account_manager.fleet_manager import AccountManager
from app.execution_engine.sync_executor import SynchronizedExecutionEngine
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
from app.risk_management.safety_monitor import RiskManagementSystem
from app.utils.logger import get_logger
from app.utils.crypto import CredentialVault
from app.utils.config import get_config
print('✓ ALL MODULES IMPORT SUCCESSFULLY')
"

✓ Documentation Generated:
  ls -la *.md
  Should show: README, QUICKSTART, ARCHITECTURE, DEPLOYMENT, etc.
"""

# ============================================================================
# MANUAL TESTING SCENARIOS
# ============================================================================

MANUAL_SCENARIOS = """
SCENARIO 1: Account Management
  1. Run: python3 setup_wizard.py
  2. Add test account to slot 1
  3. Verify: python3 -c "from app.account_manager.fleet_manager import AccountManager; m = AccountManager(); print(m.list_accounts())"
  Expected: Shows account in slot 1

SCENARIO 2: Recovery Calculation
  1. python3 -c "
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
engine = HedgeRecoveryEngine()
target = engine.calculate_recovery_target([50.0, 75.0], 100.0)
print(f'Target for fees 50+75 with surplus 100: ${target}')
expected_target = 50 + 75 + 100  # 225
print(f'Expected: ${expected_target}, Match: {target == expected_target}')
"
  Expected: Target=$225.00, Match: True

SCENARIO 3: Encryption/Decryption
  1. python3 -c "
from app.utils.crypto import CredentialVault
vault = CredentialVault('test.enc')
test_data = {'accounts': {'test_acc': {'password': 'secret123', 'server': 'test_server'}}}
vault.encrypt_credentials(test_data)
decrypted = vault.decrypt_credentials()
print(f'Encryption OK: {decrypted == test_data}')
print(f'Password stored: {decrypted[\"accounts\"][\"test_acc\"][\"password\"]}')
"
  Expected: Encryption OK: True, Password correctly encrypted/decrypted

SCENARIO 4: Configuration Persistence
  1. python3 -c "
from app.utils.config import get_config
config1 = get_config()
config1.set('test.param', 'value123')
"
  2. python3 -c "
from app.utils.config import get_config
config2 = get_config()
value = config2.get('test.param')
print(f'Config persisted: {value}')
"
  Expected: Config persisted: value123

SCENARIO 5: Logging System
  1. python3 -c "
from app.utils.logger import get_logger
logger = get_logger()
logger.log_trade({'action': 'test_buy', 'symbol': 'US100', 'account': 123456})
logger.log_recovery({'action': 'test_recovery', 'target': 225.0})
logger.log_risk_event('TEST_EVENT', {'detail': 'test'})
print('Logs written')
"
  2. Verify logs created:
     ls -la logs/
     cat logs/trades.jsonl | head -1
  Expected: JSON entries in logs/trades.jsonl and logs/recovery.jsonl
"""

if __name__ == "__main__":
    print("""
    MARVEL TRADING DASHBOARD - TESTING GUIDE
    ========================================
    
    """)
    print(DIAGNOSTIC_TEST)
    print("\n" + "="*70 + "\n")
    print(UNIT_TEST)
    print("\n" + "="*70 + "\n")
    print(QUICK_CHECKLIST)
