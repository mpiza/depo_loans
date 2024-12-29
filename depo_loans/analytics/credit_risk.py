from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np
from scipy.stats import norm
from datetime import date
from ..models.base import BaseInstrument

@dataclass
class CreditMetrics:
    probability_of_default: float
    loss_given_default: float
    exposure_at_default: float
    expected_loss: float
    unexpected_loss: float
    credit_var: float
    credit_rating_migration_probs: Dict[str, float]

class CreditRiskAnalytics:
    def __init__(self, rating_transition_matrix: Dict[str, Dict[str, float]],
                 default_rates: Dict[str, float],
                 recovery_rates: Dict[str, float]):
        self.rating_transition_matrix = rating_transition_matrix
        self.default_rates = default_rates
        self.recovery_rates = recovery_rates

    def calculate_credit_metrics(self, instrument: BaseInstrument,
                               market_data: Dict[str, float],
                               confidence_level: float = 0.99) -> CreditMetrics:
        # Calculate PD using Merton model
        pd = self._calculate_probability_of_default(
            instrument, market_data
        )
        
        # Calculate LGD based on seniority and collateral
        lgd = self._calculate_loss_given_default(instrument)
        
        # Calculate EAD
        ead = self._calculate_exposure_at_default(instrument)
        
        # Expected and unexpected loss
        el = pd * lgd * ead
        ul = np.sqrt(pd * (1 - pd)) * lgd * ead
        
        # Credit VaR
        credit_var = self._calculate_credit_var(
            pd, lgd, ead, confidence_level
        )
        
        # Rating migration probabilities
        migration_probs = self._calculate_rating_migration_probs(
            instrument.counterparty_rating
        )
        
        return CreditMetrics(
            probability_of_default=pd,
            loss_given_default=lgd,
            exposure_at_default=ead,
            expected_loss=el,
            unexpected_loss=ul,
            credit_var=credit_var,
            credit_rating_migration_probs=migration_probs
        )

    def _calculate_probability_of_default(self, 
                                        instrument: BaseInstrument,
                                        market_data: Dict[str, float]) -> float:
        """Calculate PD using Merton model"""
        asset_value = market_data.get('asset_value', 0)
        asset_volatility = market_data.get('asset_volatility', 0)
        debt_value = market_data.get('debt_value', 0)
        risk_free_rate = market_data.get('risk_free_rate', 0)
        time_horizon = 1.0  # 1 year

        if asset_value <= 0 or debt_value <= 0:
            return self.default_rates.get(instrument.counterparty_rating, 0.1)

        d1 = (np.log(asset_value/debt_value) + 
              (risk_free_rate + 0.5 * asset_volatility**2) * time_horizon) / \
             (asset_volatility * np.sqrt(time_horizon))
        d2 = d1 - asset_volatility * np.sqrt(time_horizon)
        
        return norm.cdf(-d2)

    def _calculate_loss_given_default(self, instrument: BaseInstrument) -> float:
        """Calculate LGD based on seniority and collateral"""
        base_recovery = self.recovery_rates.get(instrument.counterparty_rating, 0.4)
        
        # Adjust for collateral if available
        if hasattr(instrument, 'collateral_value'):
            collateral_coverage = getattr(instrument, 'collateral_value', 0) / \
                                instrument.principal
            return max(0, 1 - (base_recovery + 0.5 * collateral_coverage))
        
        return 1 - base_recovery

    def _calculate_exposure_at_default(self, instrument: BaseInstrument) -> float:
        """Calculate EAD including potential future exposure"""
        if isinstance(instrument, TimeDeposit):
            return instrument.principal
        elif isinstance(instrument, TermLoan):
            return instrument.outstanding_amount
        return 0

    def _calculate_credit_var(self, pd: float, lgd: float, 
                            ead: float, confidence_level: float) -> float:
        """Calculate Credit VaR using Monte Carlo simulation"""
        n_simulations = 10000
        losses = np.zeros(n_simulations)
        
        for i in range(n_simulations):
            default = np.random.random() < pd
            if default:
                loss_given_default = np.random.beta(2, 5) * lgd  # Random LGD
                losses[i] = loss_given_default * ead
                
        return np.percentile(losses, confidence_level * 100)

    def _calculate_rating_migration_probs(self, 
                                        current_rating: str) -> Dict[str, float]:
        """Calculate rating migration probabilities"""
        return self.rating_transition_matrix.get(current_rating, {}) 