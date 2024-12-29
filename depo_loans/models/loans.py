from dataclasses import dataclass
from datetime import date
from typing import Optional, List
from .base import BaseInstrument, RateType, PaymentFrequency, DayCountConvention

@dataclass
class LoanParticipant:
    participant_id: str
    participation_amount: float
    participation_percentage: float
    transferable: bool
    minimum_hold_amount: float

@dataclass
class Covenant:
    type: str
    description: str
    threshold: float
    testing_frequency: PaymentFrequency
    last_test_date: date
    last_test_result: bool

@dataclass
class TermLoan(BaseInstrument):
    facility_amount: float
    outstanding_amount: float
    amortization_type: str
    interest_rate: InterestRate
    default_spread: float
    payment_frequency: PaymentFrequency
    upfront_fee: float
    commitment_fee: float
    agent_fee: float
    participants: List[LoanParticipant]
    agent_bank: str
    financial_covenants: List[Covenant] 