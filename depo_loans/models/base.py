from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional, List, Dict

class InstrumentStatus(Enum):
    ACTIVE = "ACTIVE"
    MATURED = "MATURED"
    DEFAULTED = "DEFAULTED"
    RESTRUCTURED = "RESTRUCTURED"
    CANCELLED = "CANCELLED"

class RateType(Enum):
    FIXED = "FIXED"
    FLOATING = "FLOATING"
    STEP_UP = "STEP_UP"

class PaymentFrequency(Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    ANNUAL = "ANNUAL"

class DayCountConvention(Enum):
    ACT_360 = "ACT/360"
    ACT_365 = "ACT/365"
    THIRTY_360 = "30/360"
    ACT_ACT = "ACT/ACT"

@dataclass
class BaseInstrument:
    id: str
    name: str
    status: InstrumentStatus
    currency: str
    issue_date: date
    maturity_date: date
    counterparty_id: str
    counterparty_rating: Optional[str]
    booking_entity: str
    trading_book: str
    cost_center: str 