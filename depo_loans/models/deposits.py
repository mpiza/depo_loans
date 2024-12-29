from dataclasses import dataclass
from datetime import date
from typing import Optional, List
from .base import BaseInstrument, RateType, PaymentFrequency, DayCountConvention
from .rate_features import RateCap, RateFloor, CallOption

@dataclass
class InterestRate:
    type: RateType
    value: float
    spread: Optional[float] = None
    reference_rate: Optional[str] = None
    reset_frequency: Optional[PaymentFrequency] = None
    cap: Optional[RateCap] = None
    floor: Optional[RateFloor] = None

@dataclass
class TimeDeposit(BaseInstrument):
    principal: float
    interest_rate: InterestRate
    payment_frequency: PaymentFrequency
    day_count_convention: DayCountConvention
    compounding_frequency: PaymentFrequency
    allow_early_withdrawal: bool
    early_withdrawal_penalty: Optional[float] = None
    is_callable: bool = False
    call_schedule: Optional[List[CallOption]] = None 