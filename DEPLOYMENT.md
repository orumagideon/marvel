"""
Marvel Trading System - Deployment Guide
Instructions for production deployment on Windows VPS
"""

DEPLOYMENT_GUIDE = """
# MARVEL TRADING DASHBOARD - DEPLOYMENT GUIDE

## Pre-Deployment Checklist

### System Requirements
- [ ] Windows Server 2016 or later
- [ ] Python 3.12+ installed
- [ ] MetaTrader5 installed (2 instances recommended)
- [ ] 4GB+ RAM available
- [ ] Stable internet connection
- [ ] Administrator access

### Setup Validation
- [ ] All accounts configured in setup wizard
- [ ] MT5 terminal paths verified
- [ ] Credentials encrypted and stored
- [ ] Test trades executed successfully
- [ ] Recovery ledger initialized
- [ ] Logs directory writable

## Installation Steps

### 1. Prepare VPS Environment
```powershell
# Create application directory
New-Item -ItemType Directory -Path C:\\Trading\\Marvel

# Install Python dependencies
pip install -r requirements.txt

# Verify MetaTrader5
python -c "import MetaTrader5; print(MetaTrader5.__version__)"
```

### 2. Build Executable
```powershell
# Generate PyInstaller executable
pyinstaller --onefile --windowed `
  --icon=marvel.ico `
  --name=MarvelTrading `
  --distpath=.\\dist `
  main.py

# Verify executable
.\\dist\\MarvelTrading.exe --version
```

### 3. Deploy to VPS
```powershell
# Copy executable and data
xcopy dist\\MarvelTrading.exe C:\\Trading\\Marvel\\
xcopy data C:\\Trading\\Marvel\\data\\ /E
xcopy logs C:\\Trading\\Marvel\\logs\\ /E
```

### 4. Initial Configuration
```powershell
# Run setup wizard
python setup_wizard.py

# Run diagnostics
python diagnostics.py

# Run tests
python test_suite.py
```

### 5. Configure as Service (Optional)
```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "C:\\Trading\\Marvel\\MarvelTrading.exe"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "MarvelTrading"
```

## Production Operations

### Daily Startup
1. Verify both MT5 terminal instances are running
2. Launch MarvelTrading.exe
3. Confirm both instance connections (status indicators green)
4. Verify account balances and equity
5. Check for any error alerts

### During Trading
- Monitor drawdown gauge continuously
- Watch for critical equity warnings
- Review execution logs in real-time
- Keep CLOSE ALL button accessible
- Never leave unattended for extended periods

### Daily Shutdown
1. Close all open positions (manual or CLOSE ALL)
2. Record day's profit/loss
3. Check recovery ledger updates
4. Review logs for any errors
5. Gracefully shut down application
6. Verify both MT5 instances properly closed

## Monitoring and Troubleshooting

### Log Analysis
```powershell
# Real-time log monitoring
Get-Content -Path logs\\marvel_*.log -Tail 50 -Wait

# Search for errors
Select-String -Path logs\\*.jsonl -Pattern "error"

# Review recovery ledger
Import-Csv data\\recovery_log.csv | Format-Table
```

### Common Issues

**MT5 Connection Failed**
- Verify terminal path in config.json
- Confirm terminal is running and authorized
- Check network connectivity
- Review connection manager logs

**Recovery Not Triggering**
- Verify auto recovery is enabled (checkbox)
- Confirm hedge losses recorded in recovery.jsonl
- Check recovery_log.csv for entries
- Review recovery engine logs

**Drawdown Triggering Too Early**
- Verify daily_drawdown_limit in config.json
- Confirm equity calculations in account health widget
- Review risk_events.jsonl for threshold details
- Re-check account balance starting point

### Performance Optimization

**Reduce CPU Usage**
- Increase UI refresh rate (ui.refresh_rate_ms)
- Disable verbose logging for production
- Use market data caching

**Reduce Memory Usage**
- Limit log file size (logging.max_file_size_mb)
- Clear cache periodically
- Monitor for memory leaks

**Improve Latency**
- Ensure VPS has stable internet
- Use wired connection if possible
- Monitor MT5 latency in status panel
- Consider broker proximity

## Backup and Recovery

### Critical Files to Backup
```
data/
├── credentials.enc           # Encrypted credentials
├── credentials.enc.key       # Encryption key
├── accounts.json            # Account configuration
├── recovery_log.csv         # Recovery history
└── config.json              # System configuration
```

### Backup Strategy
```powershell
# Daily backup (run as scheduled task)
$source = "C:\\Trading\\Marvel\\data"
$dest = "D:\\Backups\\Marvel_$(Get-Date -Format 'yyyyMMdd')\\"
Copy-Item -Path $source -Destination $dest -Recurse
```

### Disaster Recovery
1. Restore credentials.enc and credentials.enc.key
2. Restore accounts.json
3. Restore recovery_log.csv
4. Verify all accounts in setup wizard
5. Run test suite before trading

## Security Hardening

### File Permissions
```powershell
# Restrict key file access
icacls "C:\\Trading\\Marvel\\data\\credentials.enc.key" /grant:r "%USERNAME%:F" /inheritance:r
```

### Firewall Rules
- Restrict outbound to MT5 broker servers only
- Allow inbound only for remote management (if needed)
- Monitor for unauthorized access attempts

### Credential Management
- Never share credentials.enc key
- Rotate passwords periodically
- Use strong, unique passwords for each account
- Keep recovery seed in secure location

## VPS-Specific Considerations

### Network Configuration
- Ensure static IP or dynamic DNS
- Configure VPN if accessing remotely
- Test connection stability regularly
- Monitor bandwidth usage

### Resource Allocation
- Allocate 2+ CPU cores
- Assign 4-8GB RAM
- Use SSD for logs directory
- Monitor disk space regularly

### Remote Access
```powershell
# Enable Remote Desktop for VPS access
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# Or use terminal via SSH
# Configure OpenSSH server
```

## Performance Benchmarks

### Expected Performance
- Trade execution latency: 50-150ms
- Market data refresh: 100-200ms
- UI responsiveness: <100ms
- System overhead: 15-25% CPU, 200-400MB RAM

### Performance Tuning
| Parameter | Conservative | Aggressive |
|-----------|--------------|-----------|
| Refresh Rate (ms) | 500 | 50 |
| Market Feed (ms) | 500 | 100 |
| Log Level | INFO | DEBUG |
| Execution Delay (ms) | 50 | 10 |

## Support and Escalation

### Diagnostics Command
```powershell
python diagnostics.py  # Full system health check
```

### Log Collection for Support
```powershell
# Gather all relevant logs
$logs = Get-ChildItem logs\\*.* | Where-Object {$_.LastWriteTime -gt (Get-Date).AddDays(-1)}
Compress-Archive -Path $logs -DestinationPath support_logs.zip
```

### Emergency Contacts
- MetaTrader5 Support: support@metaquotes.net
- Broker Support: [Your Broker]
- Maven Support: [Your Support Channel]

---

**Version**: 1.0.0
**Last Updated**: May 2026
**Status**: Production Ready
"""

if __name__ == "__main__":
    print(DEPLOYMENT_GUIDE)
