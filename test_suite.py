"""
Unit Tests for Marvel Trading System
Validates core components and functionality
"""

import unittest
import sys
from pathlib import Path
from app.utils.logger import get_logger
from app.utils.crypto import CredentialVault
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine
from app.account_manager.fleet_manager import AccountManager, TradingPhase


class TestCredentialVault(unittest.TestCase):
    """Test encryption and credential management"""
    
    def setUp(self):
        self.vault = CredentialVault("test_vault.enc")
    
    def test_encrypt_decrypt(self):
        """Test credential encryption/decryption"""
        creds = {"password": "test123", "server": "server1"}
        self.vault.encrypt_credentials({"accounts": {"test": creds}})
        
        decrypted = self.vault.decrypt_credentials()
        self.assertIsNotNone(decrypted)
        self.assertEqual(decrypted["accounts"]["test"]["password"], "test123")
    
    def tearDown(self):
        # Cleanup
        try:
            Path("test_vault.enc").unlink()
            Path("test_vault.enc.key").unlink()
        except:
            pass


class TestRecoveryEngine(unittest.TestCase):
    """Test hedge and recovery calculations"""
    
    def setUp(self):
        self.engine = HedgeRecoveryEngine("test_recovery.csv")
    
    def test_recovery_target_calculation(self):
        """Test recovery target formula"""
        fees = [50.0, 75.0]
        target = self.engine.calculate_recovery_target(fees, desired_surplus=100.0)
        
        expected = 50.0 + 75.0 + 100.0  # 225.0
        self.assertEqual(target, expected)
    
    def test_hedge_lot_calculation(self):
        """Test hedge lot sizing"""
        target = 225.0
        lot = self.engine.calculate_hedge_lot_size(target, max_drawdown=400.0, pip_value=10.0)
        
        expected = target / (400.0 * 10.0)  # 0.0563 rounded to 0.06
        self.assertAlmostEqual(lot, expected, places=2)
    
    def test_record_and_recover_loss(self):
        """Test loss recording and recovery"""
        success = self.engine.record_hedge_loss("test_cycle", 123456, 100.0, 50.0)
        self.assertTrue(success)
        
        # Loss should be in outstanding
        self.assertTrue(any("test_cycle_123456" in k for k in self.engine.outstanding_losses.keys()))
    
    def tearDown(self):
        try:
            Path("test_recovery.csv").unlink()
        except:
            pass


class TestAccountManager(unittest.TestCase):
    """Test account fleet management"""
    
    def setUp(self):
        self.mgr = AccountManager("test_accounts.json", "test_creds.enc")
    
    def test_add_account(self):
        """Test adding account"""
        success = self.mgr.add_account(
            1, 123456, "password", "server", TradingPhase.PHASE_1
        )
        self.assertTrue(success)
        
        account = self.mgr.get_account(1)
        self.assertIsNotNone(account)
        self.assertEqual(account.account_number, 123456)
    
    def test_set_account_active(self):
        """Test account activation"""
        self.mgr.add_account(1, 123456, "password", "server", TradingPhase.PHASE_1)
        
        self.mgr.set_account_active(1, True)
        account = self.mgr.get_account(1)
        self.assertTrue(account.is_active)
    
    def test_get_active_accounts(self):
        """Test retrieving active accounts"""
        self.mgr.add_account(1, 111111, "p1", "s1", TradingPhase.PHASE_1)
        self.mgr.add_account(2, 222222, "p2", "s2", TradingPhase.PHASE_2)
        
        self.mgr.set_account_active(1, True)
        active = self.mgr.get_active_accounts()
        
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].account_number, 111111)
    
    def tearDown(self):
        try:
            Path("test_accounts.json").unlink()
            Path("test_creds.enc").unlink()
            Path("test_creds.enc.key").unlink()
        except:
            pass


class TestRiskManagement(unittest.TestCase):
    """Test risk management system"""
    
    def setUp(self):
        from app.risk_management.safety_monitor import RiskManagementSystem
        self.risk_mgr = RiskManagementSystem(max_daily_drawdown=400.0)
    
    def test_initialize_equity(self):
        """Test equity tracking"""
        self.risk_mgr.initialize_account_equity(123456, 10000.0)
        self.assertEqual(self.risk_mgr.session_start_equity[123456], 10000.0)
    
    def test_reset_daily_metrics(self):
        """Test daily metrics reset"""
        self.risk_mgr.daily_trades = 10
        self.risk_mgr.reset_daily_metrics()
        
        self.assertEqual(self.risk_mgr.daily_trades, 0)
        self.assertEqual(self.risk_mgr.daily_wins, 0)
        self.assertEqual(self.risk_mgr.daily_losses, 0)


def run_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MARVEL TESTING SUITE")
    print("=" * 60 + "\n")
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestCredentialVault))
    suite.addTests(loader.loadTestsFromTestCase(TestRecoveryEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManagement))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60 + "\n")
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
