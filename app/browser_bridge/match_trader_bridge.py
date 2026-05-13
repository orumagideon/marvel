"""
cTrader DOM-Aware Execution Bridge (Enhanced)

Provides advanced async Playwright-based controller for:
1. Field Discovery: Dynamically locate cTrader UI elements
2. Automated Injection: Type lot/TP/SL values with verification
3. Order Execution: Click Place Order button with confirmation
4. Account Detection: Read balance and challenge phase
5. Symbol Detection: Read active chart symbol

Requires: playwright and browser binaries (`playwright install`)
"""
from typing import Optional, Dict, Any, List
import asyncio
import time
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class CTraderDOMSelector:
    """Centralized DOM selector patterns for cTrader terminal"""
    
    # Input field selectors (multiple attempts with fallbacks)
    QUANTITY_INPUTS = [
        "input[id*='volume'], input[id*='quantity'], input[id*='lot']",
        "input[class*='volume'], input[class*='quantity']",
        "input[name='volume'], input[name='quantity']",
        "xpath=//input[@placeholder[contains(., 'Volume')] or @placeholder[contains(., 'Lot')]]",
        "xpath=//input[@placeholder[contains(., 'Quantity')]]",
    ]
    
    TP_INPUTS = [
        "input[id*='takeprofit'], input[id*='tp']",
        "input[class*='takeprofit'], input[class*='tp']",
        "input[name='tp'], input[name='takeprofit']",
        "xpath=//input[@placeholder[contains(., 'Take Profit')]]",
    ]
    
    SL_INPUTS = [
        "input[id*='stoploss'], input[id*='sl']",
        "input[class*='stoploss'], input[class*='sl']",
        "input[name='sl'], input[name='stoploss']",
        "xpath=//input[@placeholder[contains(., 'Stop Loss')]]",
    ]
    
    BUY_BUTTONS = [
        "button[id*='buy']", "button[class*='buy']",
        "xpath=//button[contains(., 'Buy')]",
        "xpath=//button[contains(@class, 'buy-btn')]",
    ]
    
    SELL_BUTTONS = [
        "button[id*='sell']", "button[class*='sell']",
        "xpath=//button[contains(., 'Sell')]",
        "xpath=//button[contains(@class, 'sell-btn')]",
    ]
    
    PLACE_ORDER_BUTTONS = [
        "button[id*='place'], button[id*='submit']",
        "xpath=//button[contains(., 'Place Order')]",
        "xpath=//button[contains(., 'Execute')]",
    ]
    
    ACCOUNT_BALANCE = [
        "xpath=//span[contains(., 'Balance')]/../following-sibling::*/span",
        "xpath=//div[contains(@class, 'balance')]",
        "xpath=//span[contains(@id, 'balance')]",
    ]
    
    SYMBOL_DISPLAY = [
        "xpath=//span[contains(@class, 'symbol')]",
        "xpath=//input[contains(@id, 'symbol')]",
    ]


class CTraderBridge:
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._is_active = False
        self._discovered_selectors: Dict[str, str] = {}
        self._last_injection_time: Optional[float] = None

    async def start(self, url: str, headless: bool = True, viewport: Dict[str, int] = None) -> Dict[str, Any]:
        """Start Playwright and open cTrader page.

        Args:
            url: cTrader URL to open
            headless: Whether to run headless
            viewport: Browser viewport size
        Returns:
            dict with success status and connection info
        """
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=headless)
            self._context = await self._browser.new_context(viewport=viewport)
            self._page = await self._context.new_page()
            await self._page.goto(url, wait_until="networkidle")
            self._is_active = True
            
            # Auto-discover field selectors
            await self._discover_field_selectors()
            
            return {"success": True, "url": url, "discovered_fields": len(self._discovered_selectors)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def shutdown(self) -> None:
        """Cleanly shutdown browser session"""
        try:
            self._is_active = False
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass

    def is_session_active(self) -> bool:
        return bool(self._is_active and self._page is not None)

    async def _discover_field_selectors(self) -> None:
        """Auto-discover working field selectors in cTrader DOM"""
        if not self.is_session_active():
            return
        
        page = self._page
        
        # Try to find quantity input
        for selector in CTraderDOMSelector.QUANTITY_INPUTS:
            elm = await page.query_selector(selector)
            if elm:
                self._discovered_selectors["quantity"] = selector
                break
        
        # Try to find TP input
        for selector in CTraderDOMSelector.TP_INPUTS:
            elm = await page.query_selector(selector)
            if elm:
                self._discovered_selectors["tp"] = selector
                break
        
        # Try to find SL input
        for selector in CTraderDOMSelector.SL_INPUTS:
            elm = await page.query_selector(selector)
            if elm:
                self._discovered_selectors["sl"] = selector
                break

    async def _find_element(self, selector_list: List[str]) -> Optional[Any]:
        """Try multiple selectors and return first matching element"""
        if not self.is_session_active():
            return None
        
        page = self._page
        for selector in selector_list:
            try:
                elm = await page.query_selector(selector)
                if elm:
                    return elm
            except Exception:
                continue
        
        return None

    async def _set_input_value(self, element: Any, value: Any, delay_ms: int = 50) -> bool:
        """Set input value with validation"""
        try:
            await element.fill("")
            await asyncio.sleep(delay_ms / 1000.0)
            await element.type(str(value))
            await asyncio.sleep(delay_ms / 1000.0)
            return True
        except Exception:
            return False

    async def inject_trade(self, lot: float, tp: float, sl: float) -> Dict[str, Any]:
        """
        Inject trading values into cTrader form fields
        
        Args:
            lot: Lot size (e.g., 8.4)
            tp: Take profit pips
            sl: Stop loss pips
        
        Returns:
            dict with success status and injection details
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}

        page = self._page
        start_time = time.perf_counter()
        injected = {}
        
        try:
            # Inject quantity
            qty_elm = await self._find_element(CTraderDOMSelector.QUANTITY_INPUTS)
            if qty_elm:
                success = await self._set_input_value(qty_elm, lot)
                injected["quantity"] = {"value": lot, "injected": success}
            
            # Inject TP
            tp_elm = await self._find_element(CTraderDOMSelector.TP_INPUTS)
            if tp_elm:
                success = await self._set_input_value(tp_elm, tp)
                injected["tp"] = {"value": tp, "injected": success}
            
            # Inject SL
            sl_elm = await self._find_element(CTraderDOMSelector.SL_INPUTS)
            if sl_elm:
                success = await self._set_input_value(sl_elm, sl)
                injected["sl"] = {"value": sl, "injected": success}
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._last_injection_time = latency_ms
            
            return {
                "success": True,
                "injected": injected,
                "latency_ms": latency_ms,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click_trade_button(self, direction: str) -> Dict[str, Any]:
        """
        Click Buy or Sell button
        
        Args:
            direction: "buy" or "sell"
        
        Returns:
            dict with click status
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}
        
        page = self._page
        start_time = time.perf_counter()
        
        try:
            if direction.lower() == "buy":
                btn = await self._find_element(CTraderDOMSelector.BUY_BUTTONS)
            elif direction.lower() == "sell":
                btn = await self._find_element(CTraderDOMSelector.SELL_BUTTONS)
            else:
                return {"success": False, "error": f"invalid_direction: {direction}"}
            
            if btn:
                await btn.click()
                latency_ms = (time.perf_counter() - start_time) * 1000
                return {"success": True, "direction": direction, "latency_ms": latency_ms}
            else:
                return {"success": False, "error": "button_not_found"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click_place_order(self) -> Dict[str, Any]:
        """
        Click Place Order or Execute button
        
        Returns:
            dict with click status
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}
        
        page = self._page
        start_time = time.perf_counter()
        
        try:
            btn = await self._find_element(CTraderDOMSelector.PLACE_ORDER_BUTTONS)
            if btn:
                await btn.click()
                latency_ms = (time.perf_counter() - start_time) * 1000
                return {"success": True, "latency_ms": latency_ms}
            else:
                return {"success": False, "error": "place_order_button_not_found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def read_account_balance(self) -> float:
        """
        Read account balance from cTrader DOM
        
        Returns:
            balance as float, or 0.0 if not found
        """
        if not self.is_session_active():
            return 0.0
        
        try:
            for selector in CTraderDOMSelector.ACCOUNT_BALANCE:
                element = await self._page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    # Parse balance from text (e.g., "$50,000.00")
                    value = "".join(c for c in text if c.isdigit() or c == ".")
                    if value:
                        return float(value)
            return 0.0
        except Exception:
            return 0.0

    async def read_challenge_phase(self) -> Dict[str, Any]:
        """
        Read challenge phase from cTrader account info
        
        Returns:
            dict with phase info, or empty dict if not found
        """
        if not self.is_session_active():
            return {}
        
        try:
            # Look for phase indicators in DOM
            xpath = "xpath=//span[contains(., 'Challenge')] | //span[contains(., 'Funded')]"
            elements = await self._page.query_selector_all(xpath)
            
            for elm in elements:
                text = await elm.text_content()
                if "Challenge 1" in text or "Phase 1" in text:
                    return {"name": "Challenge 1", "phase": 1, "target_pct": 8.0}
                elif "Challenge 2" in text or "Phase 2" in text:
                    return {"name": "Challenge 2", "phase": 2, "target_pct": 5.0}
                elif "Funded" in text:
                    return {"name": "Funded", "phase": 0, "target_pct": 0.0}
            
            return {}
        except Exception:
            return {}

    async def read_chart_symbol(self) -> Optional[str]:
        """
        Read the currently active chart symbol
        
        Returns:
            symbol string or None if not found
        """
        if not self.is_session_active():
            return None
        
        try:
            for selector in CTraderDOMSelector.SYMBOL_DISPLAY:
                element = await self._page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text:
                        return text.strip()
            return None
        except Exception:
            return None

    async def execute_full_trade(self,
                                  direction: str,
                                  lot: float,
                                  tp: float,
                                  sl: float,
                                  place_order_timeout_ms: int = 5000) -> Dict[str, Any]:
        """
        Execute complete trade workflow:
        1. Inject lot/TP/SL
        2. Click direction button (Buy/Sell)
        3. Click Place Order
        
        Args:
            direction: "buy" or "sell"
            lot: Lot size
            tp: Take profit pips
            sl: Stop loss pips
            place_order_timeout_ms: Timeout for Place Order confirmation
        
        Returns:
            dict with complete execution status
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}
        
        results = {
            "success": False,
            "direction": direction,
            "steps": {},
            "total_latency_ms": 0.0,
        }
        
        start_time = time.perf_counter()
        
        try:
            # Step 1: Inject values
            inject_result = await self.inject_trade(lot, tp, sl)
            results["steps"]["inject"] = inject_result
            if not inject_result.get("success"):
                return results
            
            # Step 2: Click direction button
            click_result = await self.click_trade_button(direction)
            results["steps"]["click_direction"] = click_result
            if not click_result.get("success"):
                return results
            
            # Small delay before clicking Place Order
            await asyncio.sleep(0.1)
            
            # Step 3: Click Place Order
            place_result = await self.click_place_order()
            results["steps"]["place_order"] = place_result
            if not place_result.get("success"):
                return results
            
            results["success"] = True
            results["total_latency_ms"] = (time.perf_counter() - start_time) * 1000
            return results
        
        except Exception as e:
            results["error"] = str(e)
            return results

            elapsed = (time.perf_counter() - start) * 1000
            return {"success": True, "injection_ms": elapsed}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def verify_values(self, expected: Dict[str, Any]) -> Dict[str, Any]:
        """Read back values from the page and compare to expected.

        Expected keys: 'lot', 'tp', 'sl'
        Returns dict with matched boolean and read values.
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}
        page = self._page
        read = {}
        try:
            for key in ("lot", "tp", "sl"):
                selector = f"input[name='{key}'], input[id*='{key}'], input[class*='{key}']"
                elm = await page.query_selector(selector)
                if not elm:
                    elm = await page.query_selector(f"xpath=//input[contains(@class,'{key}') or contains(@id,'{key}')]")
                if elm:
                    val = await elm.input_value()
                    try:
                        read[key] = float(val)
                    except Exception:
                        read[key] = val
                else:
                    read[key] = None

            matched = (
                float(read.get("lot", 0) or 0) == float(expected.get("lot", 0) or 0)
                and float(read.get("tp", 0) or 0) == float(expected.get("tp", 0) or 0)
                and float(read.get("sl", 0) or 0) == float(expected.get("sl", 0) or 0)
            )
            return {"success": True, "matched": matched, "read": read}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def click_trade(self, side: str = "buy") -> Dict[str, Any]:
        """Trigger the Buy or Sell button click on Match-Trader.

        side: 'buy' or 'sell'
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}
        try:
            page = self._page
            # heuristic selectors for buy/sell buttons
            buy_sel = "button[data-action='buy'], button.buy, button.btn-buy, button[title*='Buy']"
            sell_sel = "button[data-action='sell'], button.sell, button.btn-sell, button[title*='Sell']"
            sel = buy_sel if side.lower().startswith("b") else sell_sel
            btn = await page.query_selector(sel)
            if not btn:
                # fallback: try text content
                btn = await page.query_selector(f"xpath=//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{side.lower()}')]")
            if not btn:
                return {"success": False, "error": "button_not_found"}
            start = time.perf_counter()
            await btn.click()
            elapsed = (time.perf_counter() - start) * 1000
            return {"success": True, "click_ms": elapsed}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def inject_and_click(self, lot: float, tp: float, sl: float, side: str = "buy") -> Dict[str, Any]:
        """Convenience: inject values, verify, then click. Returns timings and verification.
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}
        t0 = time.perf_counter()
        inj = await self.inject_trade(lot, tp, sl)
        if not inj.get("success"):
            return {"success": False, "stage": "inject", "detail": inj}
        ver = await self.verify_values({"lot": lot, "tp": tp, "sl": sl})
        if not ver.get("success") or not ver.get("matched"):
            return {"success": False, "stage": "verify", "detail": ver}
        click = await self.click_trade(side)
        total_ms = (time.perf_counter() - t0) * 1000
        return {"success": click.get("success", False), "injection_ms": inj.get("injection_ms"), "click_ms": click.get("click_ms"), "total_ms": total_ms}
