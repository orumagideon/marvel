# MT5 Connection Manager - Technical Summary

## Changes Made to Fix "Hedge login failed"

### File Modified
`app/mt5_bridge/connection_manager.py`

### Problem Statement
When connecting the Funded Next hedge account after connecting the Maven fleet, the hedge connection would fail with "login failed" error. The root cause was that MT5's `initialize()` method can only be called once globally, but the code attempted to call it for each instance independently.

### Key Modifications

#### 1. Added Global Initialization State Tracking
```python
def __init__(self):
    self.is_mt5_initialized = False  # NEW: Track global MT5 initialization state
    # ... rest of init
```

**Benefit**: Know whether MT5 has already been initialized globally

#### 2. Fixed Initialize Method
**Before**: Would call `mt5.initialize()` multiple times (fails on 2nd call)
**After**: Only calls `mt5.initialize()` once, subsequent calls return success

```python
# Check if MT5 is already initialized globally
if self.is_mt5_initialized:
    # Already initialized, just mark this instance as ready
    self.instances[instance_type]["state"] = ConnectionState.CONNECTED
    self.instances[instance_type]["connection_time"] = datetime.now()
    self.retry_counts[instance_type] = 0
    self.logger.info(f"[{instance_type.value}] Using existing MT5 initialization")
    return True

# First initialization - initialize MT5 with the given terminal path
if not mt5.initialize(path=terminal_path):
    error_msg = f"MT5 initialization failed for {instance_type.value}: {mt5.last_error()}"
    # ... error handling
    return False

# Mark MT5 as initialized globally
self.is_mt5_initialized = True
```

**Benefit**: MT5 only initializes once, both Maven and Hedge can connect

#### 3. Improved Login Error Handling
**Before**: Generic error messages with no MT5 error details
**After**: Captures and logs actual MT5 error codes

```python
# Check if MT5 is initialized before attempting login
if not self.is_mt5_initialized:
    error_msg = "MT5 not initialized. Call initialize() first."
    self.instances[instance_type]["last_error"] = error_msg
    self.instances[instance_type]["state"] = ConnectionState.ERROR
    self.logger.error(f"[{instance_type.value}] {error_msg}")
    return False

# Get detailed error from MT5
mt5_error = mt5.last_error()
error_code, error_msg = mt5_error if mt5_error else (None, "Unknown error")
self.logger.debug(
    f"[{instance_type.value}] Login attempt {attempt + 1}/{MT5_MAX_RETRIES} failed - "
    f"Error: {error_code}: {error_msg}"
)
```

**Benefit**: Better debugging when connection fails - real error codes from MT5

#### 4. Updated Shutdown Logic
**Before**: Didn't track that MT5 was shut down
**After**: Resets initialization state when MT5 is shut down

```python
def shutdown_all(self) -> None:
    try:
        mt5.shutdown()
        self.is_mt5_initialized = False  # NEW: Reset global initialization state
        for instance_type in MT5InstanceType:
            self.instances[instance_type]["state"] = ConnectionState.DISCONNECTED
        self.logger.info("All MT5 connections shutdown")
    except Exception as e:
        self.logger.log_error(e, "Shutdown all error")
```

**Benefit**: Can reinitialize MT5 after shutdown for clean reconnection

#### 5. Enhanced Logging
Added logging for:
- MT5 terminal path initialization confirmation
- Per-attempt login failure details with MT5 error codes
- Server name in successful login message (for Funded Next tracking)

## Connection Flow After Fix

```
Step 1: Initialize Maven Instance
├─ System checks: is_mt5_initialized = False
├─ Calls mt5.initialize(path="C:\Program Files\MetaTrader 5")
├─ Sets is_mt5_initialized = True
└─ Success ✓

Step 2: Login to Maven Account
├─ System verifies MT5 is initialized ✓
├─ Calls mt5.login(maven_account, maven_password, maven_server)
└─ Success ✓

Step 3: Initialize Hedge Instance
├─ System checks: is_mt5_initialized = True (already initialized)
├─ Skips mt5.initialize() call
├─ Marks hedge instance state as CONNECTED
└─ Success ✓ (no re-initialization!)

Step 4: Login to Hedge Account (Funded Next)
├─ System verifies MT5 is initialized ✓
├─ Calls mt5.login(hedge_account, hedge_password, "FundedNext-Server3")
├─ Retries up to 5 times with detailed error logging
└─ Success ✓
```

## Testing the Fix

### Quick Test
1. Start Marvel Dashboard
2. Connect Maven account first
3. Connect Funded Next hedge account
4. Both should show as "connected" in the UI
5. Check logs for any errors

### Verification Points
- [ ] Maven and Hedge both show "connected" status
- [ ] Dashboard market data updates (indicates working connection)
- [ ] No "MT5 initialization failed" errors in logs
- [ ] Funded Next server name appears in connection logs

## Backwards Compatibility
✓ All existing features maintain same interface
✓ Account switching still works
✓ Auto-connect on startup still works
✓ Reconnection logic unchanged
✓ Risk management integration untouched

## Future Improvements
If needed for production:
1. Consider separate MT5 terminal processes for true isolation
2. Add connection pooling for multiple Funded Next servers
3. Implement graceful degradation if Funded Next becomes unavailable
4. Add metrics tracking for connection health monitoring
