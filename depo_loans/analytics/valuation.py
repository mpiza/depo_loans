from datetime import date, timedelta
from typing import List, Dict
import numpy as np
from scipy.stats import norm
from dateutil.relativedelta import relativedelta
from ..models.base import BaseInstrument, RateType, PaymentFrequency, DayCountConvention
from ..models.deposits import TimeDeposit, InterestRate
from ..models.loans import TermLoan
from .day_count import DayCountCalculator

class CashFlow:
    def __init__(self, payment_date: date, amount: float, payment_type: str):
        self.payment_date = payment_date
        self.amount = amount
        self.payment_type = payment_type

class ValuationEngine:
    def __init__(self):
        self.day_count_calculator = DayCountCalculator()

    def calculate_present_value(self, instrument: BaseInstrument, valuation_date: date, 
                              discount_curve: Dict[str, float]) -> float:
        cashflows = self.project_cashflows(instrument)
        return self._discount_cashflows(cashflows, discount_curve, valuation_date)

    def project_cashflows(self, instrument: BaseInstrument) -> List[CashFlow]:
        if isinstance(instrument, TimeDeposit):
            return self._project_deposit_cashflows(instrument)
        elif isinstance(instrument, TermLoan):
            return self._project_loan_cashflows(instrument)
        else:
            raise ValueError(f"Unsupported instrument type: {type(instrument)}")

    def _project_deposit_cashflows(self, deposit: TimeDeposit) -> List[CashFlow]:
        cashflows = []
        current_date = deposit.issue_date
        
        # Generate payment dates
        payment_dates = self._generate_payment_dates(
            deposit.issue_date,
            deposit.maturity_date,
            deposit.payment_frequency
        )
        
        for i, payment_date in enumerate(payment_dates):
            # Calculate period interest rate considering caps and floors
            rate = self._calculate_period_rate(
                deposit.interest_rate,
                current_date,
                payment_date
            )
            
            # Calculate day count fraction
            dcf = self.day_count_calculator.calculate_dcf(
                current_date,
                payment_date,
                deposit.day_count_convention
            )
            
            # Calculate interest amount
            interest_amount = deposit.principal * rate * dcf
            
            # Add interest cashflow
            cashflows.append(CashFlow(
                payment_date=payment_date,
                amount=interest_amount,
                payment_type="INTEREST"
            ))
            
            # Add principal repayment at maturity
            if payment_date == deposit.maturity_date:
                cashflows.append(CashFlow(
                    payment_date=payment_date,
                    amount=deposit.principal,
                    payment_type="PRINCIPAL"
                ))
            
            current_date = payment_date
        
        return cashflows

    def _calculate_period_rate(self, interest_rate: InterestRate, 
                             start_date: date, end_date: date) -> float:
        rate = interest_rate.value
        
        if interest_rate.type == RateType.FLOATING:
            rate += interest_rate.spread or 0
            
        # Apply cap if exists and is applicable
        if interest_rate.cap and (not interest_rate.cap.start_date or 
            start_date >= interest_rate.cap.start_date) and (
            not interest_rate.cap.end_date or end_date <= interest_rate.cap.end_date):
            rate = min(rate, interest_rate.cap.cap_rate)
            
        # Apply floor if exists and is applicable
        if interest_rate.floor and (not interest_rate.floor.start_date or 
            start_date >= interest_rate.floor.start_date) and (
            not interest_rate.floor.end_date or end_date <= interest_rate.floor.end_date):
            rate = max(rate, interest_rate.floor.floor_rate)
            
        return rate

    def _discount_cashflows(self, cashflows: List[CashFlow], 
                          discount_curve: Dict[str, float], 
                          valuation_date: date) -> float:
        pv = 0.0
        for cf in cashflows:
            years = self._calculate_years_fraction(valuation_date, cf.payment_date)
            discount_rate = self._interpolate_rate(discount_curve, years)
            discount_factor = np.exp(-discount_rate * years)
            pv += cf.amount * discount_factor
        return pv

    def calculate_option_adjusted_value(self, deposit: TimeDeposit,
                                     valuation_date: date,
                                     discount_curve: Dict[str, float],
                                     volatility: float) -> float:
        if not deposit.is_callable or not deposit.call_schedule:
            return self.calculate_present_value(deposit, valuation_date, discount_curve)
            
        # Calculate straight PV
        straight_pv = self.calculate_present_value(deposit, valuation_date, discount_curve)
        
        # Calculate call option values
        total_option_value = 0
        for call_option in deposit.call_schedule:
            if call_option.call_date > valuation_date:
                option_value = self._calculate_call_option_value(
                    strike=call_option.call_price * deposit.principal,
                    maturity=call_option.call_date,
                    valuation_date=valuation_date,
                    discount_curve=discount_curve,
                    volatility=volatility,
                    forward_price=straight_pv
                )
                total_option_value += option_value
                
        return straight_pv - total_option_value

    def _calculate_call_option_value(self, strike: float, maturity: date,
                                   valuation_date: date, discount_curve: Dict[str, float],
                                   volatility: float, forward_price: float) -> float:
        T = self._calculate_years_fraction(valuation_date, maturity)
        if T <= 0:
            return 0
            
        r = self._interpolate_rate(discount_curve, T)
        
        d1 = (np.log(forward_price/strike) + (r + volatility**2/2) * T) / (volatility * np.sqrt(T))
        d2 = d1 - volatility * np.sqrt(T)
        
        return forward_price * norm.cdf(d1) - strike * np.exp(-r * T) * norm.cdf(d2) 

    def calculate_yield_to_maturity(self, instrument: BaseInstrument, 
                                  market_price: float, 
                                  initial_guess: float = 0.05) -> float:
        """Calculate yield to maturity using Newton-Raphson method"""
        def price_difference(ytm):
            return self._calculate_price_with_ytm(instrument, ytm) - market_price
            
        def price_derivative(ytm):
            delta = 0.0001
            return (price_difference(ytm + delta) - price_difference(ytm)) / delta
            
        # Newton-Raphson iteration
        ytm = initial_guess
        for _ in range(100):  # Max iterations
            diff = price_difference(ytm)
            if abs(diff) < 1e-6:
                break
            ytm = ytm - diff / price_derivative(ytm)
            
        return ytm

    def calculate_duration_convexity(self, instrument: BaseInstrument, 
                                   yield_rate: float) -> tuple:
        """Calculate modified duration and convexity"""
        price = self._calculate_price_with_ytm(instrument, yield_rate)
        delta_y = 0.0001
        
        price_up = self._calculate_price_with_ytm(instrument, yield_rate + delta_y)
        price_down = self._calculate_price_with_ytm(instrument, yield_rate - delta_y)
        
        modified_duration = -(price_up - price_down) / (2 * delta_y * price)
        convexity = (price_up + price_down - 2 * price) / (delta_y * delta_y * price)
        
        return modified_duration, convexity

    def calculate_z_spread(self, instrument: BaseInstrument, 
                          market_price: float,
                          discount_curve: Dict[str, float],
                          initial_guess: float = 0.01) -> float:
        """Calculate Z-spread using Newton-Raphson method"""
        def price_difference(z_spread):
            return self._calculate_price_with_spread(
                instrument, discount_curve, z_spread) - market_price
                
        # Newton-Raphson iteration
        z_spread = initial_guess
        for _ in range(100):
            diff = price_difference(z_spread)
            if abs(diff) < 1e-6:
                break
            derivative = (price_difference(z_spread + 0.0001) - diff) / 0.0001
            z_spread = z_spread - diff / derivative
            
        return z_spread 