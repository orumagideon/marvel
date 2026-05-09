"""
Diagnostic and Health Check Utility
Validates system configuration and connectivity
"""

import sys
from pathlib import Path
from typing import Dict, Any
from app.utils.logger import get_logger
from app.utils.config import get_config
from app.mt5_bridge.connection_manager import MT5ConnectionManager, MT5InstanceType


class SystemDiagnostics:
    """System health and diagnostic checks"""
    
    def __init__(self):
        self.logger = get_logger()
        self.results = {}
    
    def check_configuration(self) -> bool:
        """Check configuration file"""
        try:
            config = get_config()
            maven_path = config.get('mt5.maven_terminal_path')
            hedge_path = config.get('mt5.hedge_terminal_path')
            
            checks = {
                "config_exists": True,
                "maven_path_set": bool(maven_path),
                "hedge_path_set": bool(hedge_path)
            }
            
            self.results['configuration'] = checks
            return all(checks.values())
        except Exception as e:
            self.logger.debug(f"Config check error: {str(e)}")
            return False
    
    def check_paths(self) -> bool:
        """Check MT5 paths are accessible"""
        try:
            config = get_config()
            maven_path = Path(config.get('mt5.maven_terminal_path', ''))
            hedge_path = Path(config.get('mt5.hedge_terminal_path', ''))
            
            checks = {
                "maven_path_exists": maven_path.exists() if maven_path.name else False,
                "hedge_path_exists": hedge_path.exists() if hedge_path.name else False
            }
            
            self.results['paths'] = checks
            return any(checks.values())
        except Exception as e:
            self.logger.debug(f"Path check error: {str(e)}")
            return False
    
    def check_directories(self) -> bool:
        """Check required directories exist"""
        try:
            dirs = {
                "data": Path("data"),
                "logs": Path("logs")
            }
            
            checks = {}
            for name, path in dirs.items():
                path.mkdir(exist_ok=True)
                checks[f"{name}_dir"] = path.exists()
            
            self.results['directories'] = checks
            return all(checks.values())
        except Exception as e:
            self.logger.debug(f"Directory check error: {str(e)}")
            return False
    
    def check_accounts(self) -> bool:
        """Check account configuration"""
        try:
            from app.account_manager.fleet_manager import AccountManager
            mgr = AccountManager()
            accounts = mgr.list_accounts()
            
            self.results['accounts'] = {
                "configured_count": len(accounts),
                "accounts": [acc['account_number'] for acc in accounts]
            }
            return len(accounts) > 0
        except Exception as e:
            self.logger.debug(f"Account check error: {str(e)}")
            self.results['accounts'] = {"error": str(e)}
            return False
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all diagnostic checks"""
        print("\n" + "=" * 60)
        print("MARVEL SYSTEM DIAGNOSTICS")
        print("=" * 60 + "\n")
        
        checks = [
            ("Configuration", self.check_configuration),
            ("Paths", self.check_paths),
            ("Directories", self.check_directories),
            ("Accounts", self.check_accounts)
        ]
        
        for name, check_func in checks:
            try:
                result = check_func()
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{name:.<40} {status}")
            except Exception as e:
                print(f"{name:.<40} ✗ ERROR: {str(e)}")
        
        print("\n" + "=" * 60)
        print("DETAILED RESULTS")
        print("=" * 60)
        
        for section, results in self.results.items():
            print(f"\n{section.upper()}:")
            for key, value in results.items():
                print(f"  {key}: {value}")
        
        return self.results


def main():
    """Run diagnostics"""
    diagnostics = SystemDiagnostics()
    results = diagnostics.run_all_checks()
    
    print("\n")


if __name__ == "__main__":
    main()
