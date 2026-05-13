"""
Multi-Asset Symbol Registry and Profile Management
Dynamically maps symbols to pip values, margin requirements, and challenge parameters
"""

from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
from enum import Enum


class AssetCategory(Enum):
    """Asset categories"""
    INDICES = "indices"
    METALS = "metals"
    FOREX = "forex"


@dataclass
class AssetProfile:
    """Comprehensive profile for each tradeable asset"""
    symbol: str
    category: AssetCategory
    pip_value_per_lot: float  # USD per pip per lot
    margin_per_lot: float  # USD margin requirement per lot
    avg_volatility_score: float  # 0.5-2.0, higher = more volatile
    spread_profile: str  # tight, medium, wide
    min_lot_size: float = 0.01
    max_lot_size: float = 100.0
    hedge_efficiency: float = 0.75  # How effective hedging this asset is
    correlation_coefficient: float = 0.0  # Correlation to USD

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['category'] = self.category.value
        return data


class AssetRegistry:
    """
    Central registry for all tradeable assets
    Provides dynamic symbol selection, profile lookup, and pip/margin calculations
    """

    # Primary assets for Kenya-optimized trading
    PRIMARY_SYMBOLS = ["USTECH", "NAS100", "XAUUSD", "US30", "GER40"]

    def __init__(self):
        self.assets: Dict[str, AssetProfile] = self._initialize_asset_profiles()
        self.selected_symbol: Optional[str] = None
        self.last_update_time: Optional[float] = None

    def _initialize_asset_profiles(self) -> Dict[str, AssetProfile]:
        """Initialize default asset profiles with realistic market data"""
        return {
            # Indices - Primary Trading Symbols
            "USTECH": AssetProfile(
                symbol="USTECH",
                category=AssetCategory.INDICES,
                pip_value_per_lot=1.0,  # 1.0 USD per pip
                margin_per_lot=1300.0,  # 1:100 leverage
                avg_volatility_score=1.50,
                spread_profile="wide",
                hedge_efficiency=0.72,
                correlation_coefficient=0.65,
            ),
            "NAS100": AssetProfile(
                symbol="NAS100",
                category=AssetCategory.INDICES,
                pip_value_per_lot=1.0,
                margin_per_lot=1300.0,
                avg_volatility_score=1.45,
                spread_profile="wide",
                hedge_efficiency=0.72,
                correlation_coefficient=0.64,
            ),
            "US30": AssetProfile(
                symbol="US30",
                category=AssetCategory.INDICES,
                pip_value_per_lot=1.0,
                margin_per_lot=1600.0,
                avg_volatility_score=1.30,
                spread_profile="medium",
                hedge_efficiency=0.69,
                correlation_coefficient=0.61,
            ),
            "GER40": AssetProfile(
                symbol="GER40",
                category=AssetCategory.INDICES,
                pip_value_per_lot=0.5,
                margin_per_lot=1700.0,
                avg_volatility_score=1.35,
                spread_profile="medium",
                hedge_efficiency=0.68,
                correlation_coefficient=0.55,
            ),
            "SPX500": AssetProfile(
                symbol="SPX500",
                category=AssetCategory.INDICES,
                pip_value_per_lot=1.0,
                margin_per_lot=1200.0,
                avg_volatility_score=1.10,
                spread_profile="medium",
                hedge_efficiency=0.75,
                correlation_coefficient=0.58,
            ),
            # Metals
            "XAUUSD": AssetProfile(
                symbol="XAUUSD",
                category=AssetCategory.METALS,
                pip_value_per_lot=10.0,  # 10.0 USD per pip (Gold specific!)
                margin_per_lot=1800.0,
                avg_volatility_score=1.35,
                spread_profile="medium",
                hedge_efficiency=0.78,
                correlation_coefficient=0.54,
            ),
            "XAGUSD": AssetProfile(
                symbol="XAGUSD",
                category=AssetCategory.METALS,
                pip_value_per_lot=50.0,
                margin_per_lot=1400.0,
                avg_volatility_score=1.25,
                spread_profile="medium",
                hedge_efficiency=0.76,
                correlation_coefficient=0.50,
            ),
            # Forex
            "EURUSD": AssetProfile(
                symbol="EURUSD",
                category=AssetCategory.FOREX,
                pip_value_per_lot=10.0,
                margin_per_lot=1000.0,
                avg_volatility_score=0.85,
                spread_profile="tight",
                hedge_efficiency=0.90,
                correlation_coefficient=0.40,
            ),
            "GBPUSD": AssetProfile(
                symbol="GBPUSD",
                category=AssetCategory.FOREX,
                pip_value_per_lot=10.0,
                margin_per_lot=1000.0,
                avg_volatility_score=0.95,
                spread_profile="tight",
                hedge_efficiency=0.88,
                correlation_coefficient=0.45,
            ),
            "USDJPY": AssetProfile(
                symbol="USDJPY",
                category=AssetCategory.FOREX,
                pip_value_per_lot=9.2,
                margin_per_lot=1000.0,
                avg_volatility_score=0.90,
                spread_profile="tight",
                hedge_efficiency=0.89,
                correlation_coefficient=0.42,
            ),
        }

    def get_asset_profile(self, symbol: str) -> Optional[AssetProfile]:
        """Retrieve asset profile by symbol"""
        return self.assets.get(symbol)

    def select_symbol(self, symbol: str) -> bool:
        """
        Select active symbol for trading session
        Returns True if symbol exists, False otherwise
        """
        if symbol in self.assets:
            self.selected_symbol = symbol
            return True
        return False

    def get_selected_symbol(self) -> Optional[str]:
        """Get currently selected symbol"""
        return self.selected_symbol

    def get_selected_profile(self) -> Optional[AssetProfile]:
        """Get profile of currently selected symbol"""
        if self.selected_symbol:
            return self.assets.get(self.selected_symbol)
        return None

    def get_pip_value(self, symbol: str) -> float:
        """Get pip value for symbol"""
        profile = self.get_asset_profile(symbol)
        return profile.pip_value_per_lot if profile else 1.0

    def get_margin_requirement(self, symbol: str) -> float:
        """Get margin requirement per lot for symbol"""
        profile = self.get_asset_profile(symbol)
        return profile.margin_per_lot if profile else 1000.0

    def get_primary_symbols(self) -> List[str]:
        """Get list of primary trading symbols"""
        return self.PRIMARY_SYMBOLS.copy()

    def get_all_symbols(self) -> List[str]:
        """Get all available symbols"""
        return sorted(list(self.assets.keys()))

    def get_symbols_by_category(self, category: AssetCategory) -> List[str]:
        """Get symbols in a specific category"""
        return sorted([
            symbol for symbol, profile in self.assets.items()
            if profile.category == category
        ])

    def calculate_position_margin(self, symbol: str, lot_size: float) -> float:
        """Calculate total margin required for a position"""
        profile = self.get_asset_profile(symbol)
        if not profile:
            return 0.0
        return profile.margin_per_lot * lot_size

    def calculate_pip_risk(self, symbol: str, lot_size: float, pips: float) -> float:
        """Calculate USD risk in pips"""
        pip_value = self.get_pip_value(symbol)
        return pip_value * lot_size * pips

    def get_asset_info_display(self, symbol: str) -> Dict[str, str]:
        """Get formatted asset info for UI display"""
        profile = self.get_asset_profile(symbol)
        if not profile:
            return {}
        return {
            "symbol": symbol,
            "category": profile.category.value,
            "pip_value": f"${profile.pip_value_per_lot:.2f}",
            "margin_per_lot": f"${profile.margin_per_lot:.0f}",
            "volatility": f"{profile.avg_volatility_score:.2f}",
            "spread": profile.spread_profile,
            "efficiency": f"{profile.hedge_efficiency * 100:.1f}%",
        }

    def list_all_assets_info(self) -> List[Dict]:
        """List all assets with their profiles"""
        return [self.get_asset_info_display(symbol) for symbol in self.get_all_symbols()]
