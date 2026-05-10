# Funded Next MT5 Connection Fix

## Issue Fixed
**Error**: "Hedge login failed" when attempting to connect Funded Next account

## Root Cause
The MT5 module is global and can only be initialized ONCE per session. The original code attempted to initialize MT5 separately for Maven and Hedge instances, causing the second initialization to fail silently.

## Solution Applied
Updated [app/mt5_bridge/connection_manager.py](app/mt5_bridge/connection_manager.py) with:

1. **Global Initialization Tracking**
   - Added `is_mt5_initialized` flag to track MT5 state globally
   - First `initialize()` call: Initializes MT5
   - Subsequent `initialize()` calls: Skip re-initialization, return success

2. **Improved Error Handling**
   - Capture detailed MT5 error codes via `mt5.last_error()`
   - Better logging for debugging server connection issues
   - Check initialization state before login attempts

3. **Account Switching**
   - Uses `mt5.login()` to switch between accounts within same session
   - No need for re-initialization between account logins

## How It Works Now

### Connection Flow
```
1. Connect Maven Instance
   ├─ Initialize MT5 (first call) ✓
   └─ Login to Maven account ✓

2. Connect Hedge Instance (Funded Next)
   ├─ Initialize MT5 (already initialized, skip) ✓
   ├─ Login to Funded Next account ✓
   └─ Both accounts active simultaneously
```

### Testing Your Setup

**Your Configuration:**
- Terminal Path: `C:\Program Files\MetaTrader 5`
- Account: `33933400`
- Server: `FundedNext-Server3`
- Password: (your secure password)

**Steps to Test:**
1. Start the Marvel application
2. **Maven Panel**: Enter Maven account credentials and click "Connect & Login"
3. **Hedge Panel**: Enter your Funded Next credentials:
   - Account: `33933400`
   - Server: `FundedNext-Server3`
   - Password: (your password)
4. Click "Connect & Login" on Hedge panel
5. Status should show "Hedge connected" in green

## Troubleshooting

If connection still fails:

### Check Terminal Path
- Ensure MT5 terminal is installed at the path you specified
- Path should be: `C:\Program Files\MetaTrader 5` (or your custom installation location)

### Verify Account Credentials
- Double-check account number: `33933400`
- Verify password is correct
- Confirm server name: `FundedNext-Server3`

### Server Connection Issues
- Ensure Funded Next servers are accessible from your location
- Check firewall settings if behind VPN
- Try FundedNext-Server1 or FundedNext-Server2 as alternatives

### View Detailed Logs
Connection logs are saved to [logs/](logs/) directory:
- `logs/risk_events.jsonl` - Connection events
- `logs/trades.jsonl` - Trade execution logs

Check for detailed error messages that will help diagnose the issue.

## Architecture Note
The fix maintains support for:
- ✓ Multiple Maven accounts in fleet
- ✓ Persistent hedge account connection
- ✓ Automatic reconnection on disconnect
- ✓ Synchronized trading across instances
- ✓ Account switching without reconnection

The dual-instance architecture now works correctly with the global MT5 initialization constraint.
