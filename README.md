# Marvel Trading Dashboard Configuration

## Technology Stack
- **Backend**: Python 3.12+, MetaTrader5 API, asyncio
- **Frontend**: CustomTkinter (dark modern UI)
- **Storage**: SQLite encryption, encrypted JSON for credentials
- **Packaging**: PyInstaller for Windows VPS deployment

## Project Structure

```
marvel/
├── app/
│   ├── core/                    # System orchestrator
│   │   └── orchestrator.py
│   ├── ui/                      # CustomTkinter dashboard
│   │   ├── dashboard.py
│   │   └── components.py
│   ├── mt5_bridge/              # Dual MT5 instance management
│   │   ├── connection_manager.py
│   │   └── market_data.py
│   ├── account_manager/         # Maven fleet management
│   │   └── fleet_manager.py
│   ├── execution_engine/        # Synchronized trade execution
│   │   └── sync_executor.py
│   ├── recovery_engine/         # Hedge recovery calculations
│   │   └── hedge_calculator.py
│   ├── risk_management/         # Safety & emergency protection
│   │   └── safety_monitor.py
│   └── utils/                   # Utilities & helpers
│       ├── logger.py
│       ├── crypto.py
│       └── constants.py
├── data/                        # Persistent storage
│   ├── recovery_log.csv
│   ├── accounts.json
│   └── credentials.enc
├── logs/                        # Application logs
├── main.py                      # Entry point
└── requirements.txt
```

## Key Features

### 1. Dual MT5 Instance Bridge
- **Instance A**: Maven Fleet (multiple accounts with dynamic switching)
- **Instance B**: Persistent High-Leverage Hedge Account
- Automatic reconnection with retry logic
- Latency monitoring and connection state tracking

### 2. Fleet Management System
- Support for 5+ trading account slots
- Secure encrypted credential storage
- Dynamic account activation for trades
- Phase management (Phase 1, Phase 2)
- Per-account configuration and status

### 3. Synchronized Execution Engine
- Hedge trade execution BEFORE Maven orders (latency guard)
- Synchronized logging with execution timestamps
- Slippage monitoring and validation
- Duplicate trade prevention
- Asynchronous order queuing

### 4. Intelligent Recovery Engine
- Mathematical calculation of recovery targets
- **Formula**: TargetProfit = Fees + Surplus + OutstandingLosses
- Dynamic hedge lot sizing with broker limit validation
- Persistent recovery ledger (CSV) across trading cycles
- Loss tracking and recovery status monitoring

### 5. Risk Management Layer
- Real-time drawdown monitoring (daily limits)
- Equity protection with critical threshold alerts
- Automatic emergency close on drawdown breach
- Free margin validation (minimum ratio checks)
- Spread validation and max slippage guards
- Trade cooldown windows for safety

### 6. Professional SaaS Dashboard
- **Modern Dark UI**: Glassmorphism aesthetic with CustomTkinter
- **Real-Time Indicators**: 
  - Live market feed (bid/ask/spread)
  - Account health gauge (color-coded risk meter)
  - Connection status indicators
- **Trading Controls**: BUY/SELL/CLOSE ALL buttons
- **Fleet Grid**: Account slots with activation checkboxes
- **Recovery Tracking**: Hedge lot size display
- **Responsive Layout**: Optimized for VPS deployment

### 7. Comprehensive Logging
- Structured JSON logging for trades and recovery
- Separate trade.jsonl, recovery.jsonl, risk_events.jsonl logs
- Daily rotating log files
- Execution latency tracking
- Audit trail for compliance

## Installation

### Prerequisites
- Windows OS (for VPS deployment)
- Python 3.12 or higher
- MetaTrader5 installed and configured
- At least 2 separate MT5 terminal instances recommended

### Setup

1. **Clone and Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure MT5 Paths**
Edit settings in the dashboard to point to your MT5 terminal installations.

3. **Launch Dashboard**
```bash
python main.py
```

## Usage

### Initial Setup
1. Launch application: `python main.py`
2. Configure Maven MT5 terminal path (Instance A)
3. Configure Personal Hedge MT5 terminal path (Instance B)
4. Add Maven account credentials (slots 1-5+)
5. Login to both MT5 instances via dashboard

### Trading Workflow
1. Select active Maven accounts (checkboxes)
2. Set lot size
3. Press BUY or SELL
4. Hedge trade executes first (if enabled)
5. Maven orders execute after 10ms latency guard
6. Recovery losses auto-tracked for next cycle

### Risk Management
- Monitor drawdown gauge in real-time
- System auto-stops at daily limit
- Emergency CLOSE ALL button always available
- Critical equity alerts when approaching limits

## API Reference

### Core System
```python
from app.core.orchestrator import get_system

system = get_system()
system.initialize_maven_instance("/path/to/mt5")
system.initialize_hedge_instance("/path/to/mt5")
await system.execute_buy_order("US100", 0.1)
```

### Account Management
```python
from app.account_manager.fleet_manager import AccountManager, TradingPhase

mgr = AccountManager()
mgr.add_account(1, 123456, "pass", "server", TradingPhase.PHASE_1)
mgr.set_account_active(1, True)
```

### Recovery Engine
```python
from app.recovery_engine.hedge_calculator import HedgeRecoveryEngine

recovery = HedgeRecoveryEngine()
target = recovery.calculate_recovery_target([50.0, 75.0])  # Fees
lot = recovery.calculate_hedge_lot_size(target)
recovery.record_hedge_loss("cycle_001", 123456, 100.0, 50.0)
```

### Risk Management
```python
from app.risk_management.safety_monitor import RiskManagementSystem

risk = RiskManagementSystem(max_daily_drawdown=400.0)
risk.initialize_account_equity(123456, 10000.0)
metrics = risk.get_current_metrics(123456)
```

## Deployment

### PyInstaller Packaging
```bash
pyinstaller --onefile --windowed \
  --icon=marvel.ico \
  --name=MarvelTrading \
  --distpath=./dist \
  main.py
```

### VPS Deployment
- Copy executable to Windows VPS
- Configure MT5 terminal paths
- Set up credential vault on VPS
- Run as scheduled task or persistent service
- Monitor logs in `/logs` directory

## Security

### Credential Management
- All passwords encrypted with Fernet (AES-256)
- Encryption keys stored separately with restricted permissions (0o600)
- Never logged or exposed in console output
- Vault re-encrypted on each write

### Account Protection
- No hardcoded credentials in source
- Credentials only loaded when needed
- Secure memory handling (best effort)
- All transactions logged with timestamps

## Performance Optimization

### Low Latency
- Asynchronous trade execution
- Minimal polling overhead
- Fast MT5 connection reconnection
- Efficient market data caching

### Resource Efficiency
- Lightweight UI framework (CustomTkinter)
- Single-threaded async event loop
- Minimal memory footprint for VPS
- Rotating log files to prevent disk bloat

## Troubleshooting

### MT5 Connection Issues
- Verify terminal paths in config
- Check terminal installations are running
- Confirm account credentials are correct
- Review connection logs in `/logs/marvel_*.log`

### Hedge Account Not Connecting
- Ensure second terminal instance is separate
- Verify hedge account has sufficient balance
- Check server name matches account setup
- Review hedge connection status indicator

### Recovery Not Triggering
- Verify Auto Recovery toggle is enabled
- Check recovery ledger in `/data/recovery_log.csv`
- Confirm hedge losses are properly recorded
- Review recovery.jsonl in logs directory

## Support & Maintenance

- Review logs regularly: `/logs/marvel_*.log`
- Monitor recovery ledger: `/data/recovery_log.csv`
- Backup credential vault: `/data/credentials.enc`
- Test emergency close weekly
- Review equity metrics daily

---
**Version**: 1.0.0
**Last Updated**: May 2026
**License**: Proprietary - Maven Prop Firm Trading System
