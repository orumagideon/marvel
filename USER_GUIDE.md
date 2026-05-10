**Marvel Trading Dashboard — Quick Start Guide**

This short guide helps a new user get comfortable with Marvel Trading Dashboard and explains the UI, core features, and typical workflows.

**Overview:**
- **Purpose:**: A desktop trading dashboard that coordinates a hedge terminal (MT5) and Funded Next (Maven) accounts, provides a Prop Firm rules engine, and maintains a Recovery Ledger for recorded hedge losses and recovery actions.
- **Platform note:**: Built for Windows with an MT5 terminal installed; some features require the `MetaTrader5` Python package and Windows runtime.

**Main Window Layout**
- **Top Status Bar:**: Shows connection status to MT5, active account name, and quick indicator lights for Market Data and Execution Engine. Green = connected/healthy, yellow = degraded, red = disconnected.
- **Left Panel — Accounts Grid:**: Lists connected Maven (Funded) accounts and local hedge account(s). Columns show account name, balance, equity, P/L, and last update time. Click an account row to make it the primary target for UI actions.
- **Center Panel — Trading Controls:**: Core trading widget where you:
  - Select **Execution Mode** (dropdown): **Hedge + Funded**, **Funded Only**, **Hedge Only**. This determines which systems receive orders.
  - Set order parameters: Volume/Lots, TP, SL, and comment. Use the **Buy**, **Sell**, and **Close** buttons to execute.
  - Use **Set Trading Enabled** toggle to disable all trade buttons while making configuration changes.
- **Right Panel — Challenge / Strategy Config & Logs:**: Scrollable area containing the Prop Firm Challenge inputs, templates, compute results, and system logs. Use the Compute button to preview dynamic hedge and funded sizes based on challenge rules.
- **Bottom Panel — Recovery Ledger:**: A live, filterable list of recorded hedge losses and recovery actions. Use Export to save CSV or JSON for audits.

**Challenge / Prop Firm Rules Widget**
- **Inputs:**: Account size, purchase fee, profit target, daily/overall drawdown limits, max lots, profit split, TP/SL defaults, and optional template name.
- **Compute Dynamic Plan:**: Runs the Prop Firm rules engine and hedge calculator and returns recommended funded lot size, hedge lot size, and the recovery target needed to return to compliance.
- **Auto-Fill Hedge Loss:**: Reads the latest hedge trade P/L (best-effort) and fills the recorded loss field so you can quickly record it to the Recovery Ledger.
- **Record Hedge Loss:**: Persist a manual or auto-filled hedge loss to the Recovery Ledger. Duplicates by trade ticket are ignored.

**Execution Modes Explained**
- **Hedge + Funded:**: Orders are sent first to the hedge account (MT5), then to the Maven Funded accounts. This synchronization reduces net exposure as required by the strategy.
- **Funded Only:**: Orders go only to the funded accounts managed by Maven.
- **Hedge Only:**: Orders are sent only to the hedge (your MT5) account.

**How Trading Works (internals, simple)**
- The orchestrator coordinates subsystems: MT5 connection manager, market data provider, execution engine, prop-firm rules engine, and recovery ledger.
- When you press Buy/Sell, the system constructs a normalized order and routes it through the synchronized executor which optionally executes the hedge trade first, waits a short, configurable delay, then executes the funded account trades.
- All executions are logged to the structured trade log and the Recovery Ledger when applicable.

**Recovery Ledger**
- **Purpose:**: Track realized negative hedge P/L and subsequent recovery executions so you can demonstrate compliance with prop-firm rules and manage reconciliation.
- **Fields:**: timestamp, account, trade ticket (if available), symbol, P/L, recorded-by, action taken, notes, and status.
- **Filters & Export:**: Apply filters (date range, account, status) and export CSV/JSON for reporting.

**Common Workflows**
- **Connect to MT5:**: Ensure MT5 terminal is running. Open the app; it will try to attach to an existing terminal. If the terminal is not attached, use the connection settings in the right panel to supply the MT5 terminal path and click Connect.
- **Load Challenge Template:**: Select a saved template from Challenge widget, adjust parameters as needed, and click Compute to preview plan outputs.
- **Record Hedge Loss Quickly:**: After a losing hedge trade, click Auto-Fill Hedge Loss, review the value, then Record Hedge Loss to persist it to the ledger.
- **Execute Recovery Plan:**: Use Compute to determine recommended hedge and funded sizes, then use Trading Controls to place the recovery trade in the appropriate Execution Mode.

**Troubleshooting & Tips**
- If MT5 login fails with "Hedge login failed", verify MT5 is running and that the app is attaching to the same terminal instance. Restart MT5 if needed and try Connect again.
- If builds or the EXE fail on Windows with permission errors, close any running MarvelTradingDashboard.exe, ensure antivirus isn't blocking, and retry the build. Logs are stored in your AppData folder to avoid packaging locks.
- If orders do not place to funded accounts, verify your Maven API credentials in `data/config.json` and check the Accounts Grid for connection status.
- For missing or stale market data, check the Market Data indicator in the top bar and restart the app if it stays red.

**Security & Data**
- Sensitive credentials are stored encrypted; do not commit `data/credentials.enc` to remote storage unprotected.
- Recovery Ledger and trade logs are persisted under the project `data/` and `logs/` directories (or AppData in packaged builds). Exported files contain financial data — secure them appropriately.

**Where to Look for More**
- Code and advanced docs: See the repository root files (README.md and QUICKSTART.md) for developer-oriented setup and Windows packaging instructions.
- If you need to run the app as a packaged EXE, follow the build instructions in `BUILD_EXE_GUIDE.md` and test on a Windows machine with MT5 installed.

**Quick Reference Commands (developer/testing)**
To run a quick smoke test locally (python environment):

```
python3 main.py
```

To compile Python files for a syntax check:

```
python3 -m py_compile app/core/orchestrator.py app/ui/dashboard.py
```

**Support**
- For issues please open an issue in the project's issue tracker or contact the maintainer listed in `README.md`.

Thank you for trying Marvel — start with a demo account, confirm connectivity, and use the Recovery Ledger to keep an auditable trail of your hedge recovery workflow.
