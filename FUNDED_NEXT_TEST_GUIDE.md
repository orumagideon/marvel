# Quick Start: Funded Next Connection Testing

## Before You Start
✓ Ensure MetaTrader 5 is installed at: `C:\Program Files\MetaTrader 5`
✓ Your Funded Next account credentials are ready:
  - Account: 33933400
  - Password: (your password)
  - Server: FundedNext-Server3

## Step-by-Step Connection Test

### 1. Start the Marvel Application
```bash
python main.py
```

Wait for the dashboard to fully load (about 2-3 seconds).

### 2. Connect Maven Fleet First (If Testing Both)
In the **"MAVEN FLEET LOGIN"** panel:
- Terminal Path: `C:\Program Files\MetaTrader 5`
- Account: (your Maven account number)
- Password: (your Maven password)
- Server: (your Maven server)
- ✓ Check "Remember credentials"
- Click **"Connect & Login"**

Wait for status to show: **"Maven connected"** in green

### 3. Connect Funded Next Hedge Account
In the **"PERSONAL HEDGE LOGIN"** panel:
- Terminal Path: `C:\Program Files\MetaTrader 5`
- Account: **33933400**
- Password: (your Funded Next password)
- Server: **FundedNext-Server3**
- ✓ Check "Remember credentials"
- Click **"Connect & Login"**

### 4. Verify Successful Connection
Look for:
- ✓ Status shows: **"Hedge connected"** in green
- ✓ Account number displays: **"Acct 33933400"**
- ✓ Balance shows (e.g., "$5000.00")
- ✓ Market data updates (bid/ask prices changing)

### 5. Check Logs (If Something Goes Wrong)
1. Look in the `logs/` folder:
   - `logs/risk_events.jsonl` - Connection events
   - `logs/trades.jsonl` - Trade execution logs

2. Search for your account (33933400) in the logs

3. Look for any error messages starting with:
   - "MT5 initialization failed"
   - "Login failed"
   - "Error code:" (from MT5)

## Expected Success Indicators

### In Dashboard
- Hedge panel shows green status
- Account information displays correctly
- Market feed shows live bid/ask prices

### In Logs
Look for lines like:
```
[HEDGE_ACCOUNT] Login successful - Account: 33933400, Server: FundedNext-Server3, Latency: 45.23ms
```

### Connection Status Details
Right-click on connection status to view detailed state:
- Connection state: CONNECTED
- Latency: (should be < 500ms)
- Last error: (should be None)

## Troubleshooting

### Problem: "MT5 initialization failed"
**Solution:**
- Verify MetaTrader 5 is installed at `C:\Program Files\MetaTrader 5`
- Check if MT5 is already running - close it first
- Restart the application

### Problem: "Login failed after 5 attempts"
**Check:**
1. Is the account number correct? (33933400)
2. Is the password correct?
3. Is the server name exact? (FundedNext-Server3)
4. Try alternative servers:
   - FundedNext-Server1
   - FundedNext-Server2
   - FundedNext-Server4

### Problem: "Connection refused by server"
**Check:**
- Firewall is not blocking MT5
- VPN (if using) allows Funded Next servers
- Your internet connection is stable
- Funded Next servers are online (check their status page)

### Problem: Application crashes after "Hedge connected"
- Check system RAM (should have at least 2GB free)
- Restart application in safe mode
- Report crash details from logs

## Testing Both Maven and Hedge Simultaneously

Once both are connected:

1. **Verify independence:**
   - Disconnect Maven → Hedge should stay connected
   - Disconnect Hedge → Maven should stay connected

2. **Test synchronized trading** (if available):
   - Click "Execute Buy" or similar trading button
   - Should execute on both Maven and Hedge accounts

3. **Monitor risk dashboard:**
   - Should show combined margin from both accounts
   - Should show total balance, equity, and P&L

## Common Server Issues with Funded Next

### FundedNext Server List
- `FundedNext-Server1` - Primary (recommended)
- `FundedNext-Server2` - Backup
- `FundedNext-Server3` - High-volume
- `FundedNext-Server4` - Regional

### Try This If Stuck:
1. Stop the application
2. Open MT5 manually and try to login there
3. If MT5 manual login works → Issue is with Marvel
4. If MT5 manual login fails → Issue is with Funded Next account/servers

## Getting Help

If connection still fails after these steps:

1. **Collect diagnostic info:**
   ```bash
   python diagnostics.py
   ```

2. **Check logs for detailed error:**
   ```bash
   cat logs/risk_events.jsonl | grep -i "error\|failed"
   ```

3. **Note down:**
   - Exact error message shown
   - Error code from MT5 (if visible)
   - Timestamp when error occurred
   - Your system: Windows version, MT5 version

4. **Review documentation:**
   - [TECHNICAL_FIX_SUMMARY.md](TECHNICAL_FIX_SUMMARY.md) - Technical details
   - [FUNDED_NEXT_CONNECTION_FIX.md](FUNDED_NEXT_CONNECTION_FIX.md) - Full fix documentation
   - [API_REFERENCE.md](API_REFERENCE.md) - Connection API details

## Success Checklist

After successful connection:
- [ ] Dashboard shows both Maven and Hedge as connected
- [ ] Market prices update in real-time
- [ ] Credentials saved (shows on next launch)
- [ ] Logs show successful connections
- [ ] Can execute test trades (if enabled)
- [ ] Account balances display correctly

**You're ready to trade!** 🚀
