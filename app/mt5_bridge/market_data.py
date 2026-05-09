"""
MT5 Market Data Provider
Real-time market data fetching with caching and refresh management
"""

import MetaTrader5 as mt5
from typing import Optional, Dict, List, Any
from datetime import datetime
import asyncio
from app.utils.logger import get_logger
from app.utils.constants import MT5_SYMBOL_PRIMARY
from app.mt5_bridge.connection_manager import MT5InstanceType


class MarketDataProvider:
    """Provides real-time market data for primary symbol and hedging"""
    
    def __init__(self):
        self.logger = get_logger()
        self.primary_symbol = MT5_SYMBOL_PRIMARY
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamp: Dict[str, datetime] = {}
    
    def get_live_tick(self, symbol: str = MT5_SYMBOL_PRIMARY) -> Optional[Dict[str, Any]]:
        """
        Get live tick data for symbol
        
        Returns:
            Dict with bid, ask, spread, time
        """
        try:
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None
            
            spread_pips = self._calculate_spread_pips(symbol, tick.ask - tick.bid)
            
            data = {
                "symbol": symbol,
                "bid": tick.bid,
                "ask": tick.ask,
                "spread_pips": spread_pips,
                "time": tick.time,
                "timestamp": datetime.now()
            }
            
            # Cache the result
            self.cache[symbol] = data
            self.cache_timestamp[symbol] = datetime.now()
            
            return data
            
        except Exception as e:
            self.logger.debug(f"Failed to get tick for {symbol}: {str(e)}")
            return None
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol properties (pip value, lot size, etc)"""
        try:
            info = mt5.symbol_info(symbol)
            if not info:
                return None
            
            return {
                "symbol": symbol,
                "digits": info.digits,
                "point": info.point,
                "bid": info.bid,
                "ask": info.ask,
                "volume_min": info.volume_min,
                "volume_max": info.volume_max,
                "volume_step": info.volume_step,
                "trade_mode": info.trade_mode,
                "session_deals": info.session_deals,
                "session_buy_orders": info.session_buy_orders,
                "session_sell_orders": info.session_sell_orders,
                "volume": info.volume,
                "volumehigh": info.volumehigh,
                "volumelow": info.volumelow
            }
        except Exception as e:
            self.logger.debug(f"Failed to get symbol info for {symbol}: {str(e)}")
            return None
    
    def get_cached_tick(self, symbol: str, max_age_seconds: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get cached tick if available and fresh enough
        Reduces API calls in high-frequency scenarios
        """
        if symbol not in self.cache:
            return None
        
        age = (datetime.now() - self.cache_timestamp.get(symbol, datetime.now())).total_seconds()
        if age <= max_age_seconds:
            return self.cache[symbol]
        
        return None
    
    def _calculate_spread_pips(self, symbol: str, spread: float) -> float:
        """Convert spread to pips (accounts for JPY pairs)"""
        if symbol.endswith("JPY"):
            return spread / 0.01
        else:
            return spread / 0.0001
    
    def validate_symbol(self, symbol: str) -> bool:
        """Verify symbol is available on account"""
        try:
            return mt5.symbol_select(symbol, True)
        except Exception as e:
            self.logger.debug(f"Symbol validation failed for {symbol}: {str(e)}")
            return False
    
    def get_multiple_ticks(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Batch retrieve ticks for multiple symbols"""
        results = {}
        for symbol in symbols:
            tick = self.get_live_tick(symbol)
            if tick:
                results[symbol] = tick
        return results
    
    def clear_cache(self) -> None:
        """Clear cached market data"""
        self.cache.clear()
        self.cache_timestamp.clear()
