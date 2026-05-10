"""
Dynamic Prop Firm Risk & Hedge Intelligence Engine

Provides:
- Challenge rule normalization
- Instrument volatility profiles
- Dynamic funded + hedge lot recommendations
- Recovery scaling modes
- Risk and margin projections
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List


@dataclass
class PropFirmChallengeConfig:
    account_size: float
    purchase_fee: float
    profit_target_pct: float
    daily_drawdown_pct: float
    overall_drawdown_pct: float
    max_lots_allowed: float
    profit_split_pct: float
    leverage: float = 100.0

    @property
    def target_dollar_amount(self) -> float:
        return self.account_size * (self.profit_target_pct / 100.0)

    @property
    def max_daily_loss_allowed(self) -> float:
        return self.account_size * (self.daily_drawdown_pct / 100.0)

    @property
    def max_overall_loss_allowed(self) -> float:
        return self.account_size * (self.overall_drawdown_pct / 100.0)


@dataclass
class InstrumentProfile:
    symbol: str
    category: str
    pip_value_per_lot: float
    avg_volatility_score: float
    spread_profile: str
    correlation_coefficient: float
    hedge_efficiency: float
    margin_per_lot: float


@dataclass
class HedgeComputationResult:
    funded_lot_size: float
    hedge_lot_size: float
    recovery_target: float
    max_loss_projection: float
    potential_hedge_recovery: float
    risk_reward_ratio: float
    margin_requirement: float
    recovery_efficiency_pct: float
    hedge_exposure_ratio: float
    risk_mode: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PropFirmRiskEngine:
    """Quant engine for dynamic challenge-aware hedge sizing."""

    ACCOUNT_SIZE_PRESETS: Dict[str, float] = {
        "2K": 2000.0,
        "5K": 5000.0,
        "10K": 10000.0,
        "25K": 25000.0,
        "50K": 50000.0,
    }

    MODE_MULTIPLIER: Dict[str, float] = {
        "conservative": 0.80,
        "balanced": 1.00,
        "aggressive": 1.30,
    }

    def __init__(self) -> None:
        self.instrument_profiles = self._default_instrument_profiles()
        self.current_config = PropFirmChallengeConfig(
            account_size=5000.0,
            purchase_fee=59.0,
            profit_target_pct=8.0,
            daily_drawdown_pct=5.0,
            overall_drawdown_pct=10.0,
            max_lots_allowed=5.0,
            profit_split_pct=80.0,
            leverage=100.0,
        )
        self.saved_templates: Dict[str, Dict[str, Any]] = {}

    def _default_instrument_profiles(self) -> Dict[str, InstrumentProfile]:
        return {
            "USTECH": InstrumentProfile("USTECH", "indices", 1.0, 1.50, "wide", 0.65, 0.72, 1300.0),
            "US100": InstrumentProfile("US100", "indices", 1.0, 1.45, "wide", 0.64, 0.72, 1300.0),
            "NAS100": InstrumentProfile("NAS100", "indices", 1.0, 1.45, "wide", 0.64, 0.72, 1300.0),
            "US30": InstrumentProfile("US30", "indices", 1.0, 1.30, "medium", 0.61, 0.69, 1600.0),
            "SPX500": InstrumentProfile("SPX500", "indices", 1.0, 1.10, "medium", 0.58, 0.75, 1200.0),
            "XAUUSD": InstrumentProfile("XAUUSD", "metals", 10.0, 1.35, "medium", 0.54, 0.78, 1800.0),
            "XAGUSD": InstrumentProfile("XAGUSD", "metals", 50.0, 1.25, "medium", 0.50, 0.76, 1400.0),
            "EURUSD": InstrumentProfile("EURUSD", "forex", 10.0, 0.85, "tight", 0.40, 0.90, 1000.0),
            "GBPUSD": InstrumentProfile("GBPUSD", "forex", 10.0, 0.95, "tight", 0.45, 0.88, 1000.0),
            "USDJPY": InstrumentProfile("USDJPY", "forex", 9.2, 0.90, "tight", 0.42, 0.89, 1000.0),
            "GBPJPY": InstrumentProfile("GBPJPY", "forex", 9.0, 1.05, "medium", 0.48, 0.84, 1100.0),
            "EURJPY": InstrumentProfile("EURJPY", "forex", 9.1, 0.98, "medium", 0.46, 0.85, 1100.0),
        }

    def list_supported_instruments(self) -> List[str]:
        return sorted(self.instrument_profiles.keys())

    def set_challenge_config(self, config: PropFirmChallengeConfig) -> None:
        self.current_config = config

    def save_template(self, template_name: str, config: Optional[PropFirmChallengeConfig] = None) -> None:
        source = config or self.current_config
        self.saved_templates[template_name] = asdict(source)

    def load_template(self, template_name: str) -> Optional[PropFirmChallengeConfig]:
        data = self.saved_templates.get(template_name)
        if not data:
            return None
        return PropFirmChallengeConfig(**data)

    def get_challenge_summary(self, config: Optional[PropFirmChallengeConfig] = None) -> Dict[str, float]:
        cfg = config or self.current_config
        return {
            "account_size": cfg.account_size,
            "purchase_fee": cfg.purchase_fee,
            "profit_target_pct": cfg.profit_target_pct,
            "target_dollar_amount": cfg.target_dollar_amount,
            "daily_drawdown_pct": cfg.daily_drawdown_pct,
            "max_daily_loss_allowed": cfg.max_daily_loss_allowed,
            "overall_drawdown_pct": cfg.overall_drawdown_pct,
            "max_overall_loss_allowed": cfg.max_overall_loss_allowed,
            "max_lots_allowed": cfg.max_lots_allowed,
            "profit_split_pct": cfg.profit_split_pct,
        }

    def compute_dynamic_hedge(
        self,
        symbol: str,
        stop_loss_pips: float,
        take_profit_pips: float,
        recovery_deficit: float,
        desired_surplus: float,
        risk_per_trade_pct: float,
        recovery_mode: str = "balanced",
        config: Optional[PropFirmChallengeConfig] = None,
    ) -> HedgeComputationResult:
        cfg = config or self.current_config
        profile = self.instrument_profiles.get(symbol.upper(), self.instrument_profiles["US100"])

        sl_pips = max(stop_loss_pips, 1.0)
        tp_pips = max(take_profit_pips, 1.0)
        risk_pct = max(min(risk_per_trade_pct, 2.5), 0.10)

        risk_budget = min(
            cfg.max_daily_loss_allowed * 0.90,
            cfg.account_size * (risk_pct / 100.0),
        )

        funded_lot = risk_budget / (sl_pips * profile.pip_value_per_lot)
        funded_lot = max(0.01, round(funded_lot, 2))
        if cfg.max_lots_allowed > 0:
            funded_lot = min(funded_lot, cfg.max_lots_allowed)

        recovery_target = max(0.0, recovery_deficit) + cfg.purchase_fee + max(0.0, desired_surplus)

        mode_key = (recovery_mode or "balanced").strip().lower()
        mode_multiplier = self.MODE_MULTIPLIER.get(mode_key, 1.0)

        instrument_risk_factor = profile.avg_volatility_score
        denominator = max(recovery_target + desired_surplus, 1.0)
        hedge_exposure_ratio = (instrument_risk_factor * cfg.max_daily_loss_allowed) / denominator

        base_hedge_lot = funded_lot * hedge_exposure_ratio * (1.0 - (profile.hedge_efficiency - 0.65) * 0.35)
        hedge_lot = max(0.01, round(base_hedge_lot * mode_multiplier, 2))

        if cfg.max_lots_allowed > 0:
            hedge_lot = min(hedge_lot, cfg.max_lots_allowed)

        max_loss_projection = round((funded_lot + hedge_lot) * sl_pips * profile.pip_value_per_lot, 2)
        potential_hedge_recovery = round(hedge_lot * tp_pips * profile.pip_value_per_lot * profile.hedge_efficiency, 2)
        risk_reward_ratio = round(tp_pips / sl_pips, 3)
        margin_requirement = round((funded_lot + hedge_lot) * profile.margin_per_lot, 2)
        recovery_efficiency = round((potential_hedge_recovery / max(recovery_target, 1.0)) * 100.0, 2)

        return HedgeComputationResult(
            funded_lot_size=funded_lot,
            hedge_lot_size=hedge_lot,
            recovery_target=round(recovery_target, 2),
            max_loss_projection=max_loss_projection,
            potential_hedge_recovery=potential_hedge_recovery,
            risk_reward_ratio=risk_reward_ratio,
            margin_requirement=margin_requirement,
            recovery_efficiency_pct=recovery_efficiency,
            hedge_exposure_ratio=round(hedge_exposure_ratio, 4),
            risk_mode=mode_key,
        )
