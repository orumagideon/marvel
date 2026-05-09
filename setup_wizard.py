#!/usr/bin/env python3
"""
Marvel Setup Wizard
Interactive setup for initial configuration
"""

import sys
from pathlib import Path
from app.utils.logger import get_logger
from app.utils.config import get_config
from app.account_manager.fleet_manager import AccountManager, TradingPhase


def print_header():
    """Print setup header"""
    print("\n" + "=" * 60)
    print("MARVEL TRADING DASHBOARD - SETUP WIZARD")
    print("=" * 60 + "\n")


def setup_mt5_paths():
    """Configure MT5 terminal paths"""
    print("MT5 TERMINAL CONFIGURATION")
    print("-" * 40)
    
    config = get_config()
    
    maven_path = input("Enter Maven MT5 terminal path (default: C:\\Program Files\\MetaTrader 5): ").strip()
    if not maven_path:
        maven_path = "C:\\Program Files\\MetaTrader 5"
    config.set('mt5.maven_terminal_path', maven_path)
    
    hedge_path = input("Enter Hedge MT5 terminal path (separate instance recommended): ").strip()
    if hedge_path:
        config.set('mt5.hedge_terminal_path', hedge_path)
    
    print("✓ MT5 paths configured\n")


def setup_accounts():
    """Configure Maven accounts"""
    print("MAVEN ACCOUNT SETUP")
    print("-" * 40)
    
    mgr = AccountManager()
    
    while True:
        slot = input("Enter slot number (1-5) or 'skip': ").strip().lower()
        
        if slot == 'skip':
            break
        
        if not slot.isdigit() or not (1 <= int(slot) <= 5):
            print("Invalid slot number")
            continue
        
        slot = int(slot)
        account = input("Account number: ").strip()
        password = input("Account password: ").strip()
        server = input("Server name: ").strip()
        phase = input("Phase (1 or 2): ").strip()
        
        phase_enum = TradingPhase.PHASE_1 if phase == "1" else TradingPhase.PHASE_2
        
        if mgr.add_account(int(slot), int(account), password, server, phase_enum):
            print(f"✓ Account added to slot {slot}\n")
        else:
            print(f"✗ Failed to add account\n")


def setup_risk_parameters():
    """Configure risk management"""
    print("RISK MANAGEMENT SETUP")
    print("-" * 40)
    
    config = get_config()
    
    drawdown = input("Daily drawdown limit ($, default 400): ").strip()
    if drawdown:
        config.set('risk_management.daily_drawdown_limit', float(drawdown))
    
    surplus = input("Recovery target surplus ($, default 100): ").strip()
    if surplus:
        config.set('recovery.desired_surplus', float(surplus))
    
    print("✓ Risk parameters configured\n")


def main():
    """Run setup wizard"""
    logger = get_logger()
    
    try:
        print_header()
        
        print("This wizard will help you configure Marvel Trading Dashboard\n")
        
        # Step 1: MT5 Paths
        setup_mt5_paths()
        
        # Step 2: Accounts
        setup_accounts()
        
        # Step 3: Risk Parameters
        setup_risk_parameters()
        
        print("=" * 60)
        print("SETUP COMPLETE")
        print("=" * 60)
        print("\nConfiguration saved. You can now launch the dashboard:")
        print("  python main.py")
        print()
        
        logger.info("Setup wizard completed successfully")
        
    except KeyboardInterrupt:
        print("\n\nSetup cancelled")
        sys.exit(1)
    except Exception as e:
        logger.log_error(e, "Setup wizard error")
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
