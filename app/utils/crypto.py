"""
Encryption utilities for secure credential storage
AES-256 encryption for account passwords and sensitive data
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import os


class CredentialVault:
    """Secure encryption/decryption for trading credentials"""
    
    def __init__(self, vault_path: str = "data/credentials.enc"):
        self.vault_path = Path(vault_path)
        self.key_path = Path(vault_path).parent / ".key"
        self._initialize_vault()
    
    def _initialize_vault(self) -> None:
        """Initialize encryption key if not exists"""
        if not self.key_path.exists():
            key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(key)
            os.chmod(self.key_path, 0o600)  # Read-only for owner
    
    def _get_cipher(self) -> Fernet:
        """Load cipher for encryption/decryption"""
        with open(self.key_path, 'rb') as f:
            key = f.read()
        return Fernet(key)
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> None:
        """Encrypt and store credentials"""
        cipher = self._get_cipher()
        data_json = json.dumps(credentials)
        encrypted = cipher.encrypt(data_json.encode())
        
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.vault_path, 'wb') as f:
            f.write(encrypted)
    
    def decrypt_credentials(self) -> Optional[Dict[str, Any]]:
        """Decrypt and retrieve credentials"""
        if not self.vault_path.exists():
            return None
        
        try:
            cipher = self._get_cipher()
            with open(self.vault_path, 'rb') as f:
                encrypted = f.read()
            decrypted = cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {str(e)}")
    
    def add_account(self, account_id: str, credentials: Dict[str, str]) -> None:
        """Add a new account to vault"""
        vault_data = self.decrypt_credentials() or {"accounts": {}}
        vault_data["accounts"][account_id] = credentials
        self.encrypt_credentials(vault_data)

    def remove_account(self, account_id: str) -> bool:
        """Remove a specific account from the vault."""
        try:
            vault_data = self.decrypt_credentials() or {"accounts": {}}
            accounts = vault_data.get("accounts", {})
            if account_id not in accounts:
                return False

            del accounts[account_id]
            vault_data["accounts"] = accounts
            self.encrypt_credentials(vault_data)
            return True
        except Exception:
            return False

    def clear_accounts(self) -> None:
        """Remove every saved account from the vault."""
        self.encrypt_credentials({"accounts": {}})
    
    def get_account(self, account_id: str) -> Optional[Dict[str, str]]:
        """Retrieve specific account credentials"""
        vault_data = self.decrypt_credentials()
        if vault_data and "accounts" in vault_data:
            return vault_data["accounts"].get(account_id)
        return None
    
    def list_accounts(self) -> list:
        """List all stored account IDs"""
        vault_data = self.decrypt_credentials()
        if vault_data and "accounts" in vault_data:
            return list(vault_data["accounts"].keys())
        return []
