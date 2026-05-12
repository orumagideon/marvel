"""
Match-Trader DOM-Aware Execution Bridge

Provides an async Playwright-based controller to inject lot/TP/SL values
into the Match-Trader web terminal and trigger Buy/Sell clicks. This is
best-effort and requires the local environment to have `playwright` and
the browser binaries installed (`playwright install`).

Selectors used here are heuristics and should be tuned to the Match-Trader
DOM structure used by your provider. The bridge exposes a small safe API
the execution engine can call.
"""
from typing import Optional, Dict, Any
import asyncio
import time
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


class MatchTraderBridge:
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._is_active = False

    async def start(self, url: str, headless: bool = True, viewport: Dict[str, int] = None) -> Dict[str, Any]:
        """Start Playwright and open Match-Trader page.

        Args:
            url: Match-Trader URL to open and attach to.
            headless: Whether to run headless.
        Returns:
            dict with success and page info
        """
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=headless)
            self._context = await self._browser.new_context(viewport=viewport)
            self._page = await self._context.new_page()
            await self._page.goto(url)
            self._is_active = True
            return {"success": True, "url": url}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def shutdown(self) -> None:
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

    async def inject_trade(self, lot: float, tp: float, sl: float) -> Dict[str, Any]:
        """Inject values into the Match-Trader input fields.

        NOTE: The CSS selectors below are generic placeholders. Update them to
        match the real Match-Trader DOM.
        """
        if not self.is_session_active():
            return {"success": False, "error": "session_inactive"}

        page = self._page
        start = time.perf_counter()
        try:
            # Lot/volume input
            # try common selectors - users should adapt to the real site
            selectors = {
                "lot": "input[name='volume'], input[id*='volume'], input[class*='volume']",
                "tp": "input[name='tp'], input[id*='tp'], input[class*='tp']",
                "sl": "input[name='sl'], input[id*='sl'], input[class*='sl']",
            }

            # Set value by focusing and using keyboard (works for many widgets)
            for key, selector in selectors.items():
                try:
                    elm = await page.query_selector(selector)
                    if not elm:
                        # try more permissive query
                        elm = await page.query_selector(f"xpath=//input[contains(@class,'{key}') or contains(@id,'{key}')]")
                    if elm:
                        await elm.fill("")
                        if key == "lot":
                            await elm.type(f"{lot}")
                        elif key == "tp":
                            await elm.type(f"{tp}")
                        elif key == "sl":
                            await elm.type(f"{sl}")
                except Exception:
                    # continue to next selector without failing entire injection
                    continue

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
