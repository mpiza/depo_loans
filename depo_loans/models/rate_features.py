from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
from datetime import date
from .base import RateType, PaymentFrequency

@dataclass
class RateCap:
    cap_rate: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None

@dataclass
class RateFloor:
    floor_rate: float
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class FloaterType(Enum):
    STANDARD = "STANDARD"
    INVERSE = "INVERSE"
    RANGE = "RANGE"

@dataclass
class StepUpRate:
    effective_date: date
    rate: float

@dataclass
class InverseFloaterSpec:
    reference_rate: str
    multiplier: float  # Typically negative for inverse floaters
    constant: float    # The fixed component
    cap: Optional[float] = None
    floor: Optional[float] = None

@dataclass
class InterestRate:
    type: RateType
    value: float
    spread: Optional[float] = None
    reference_rate: Optional[str] = None
    reset_frequency: Optional[PaymentFrequency] = None
    cap: Optional[RateCap] = None
    floor: Optional[RateFloor] = None
    step_up_schedule: Optional[List[StepUpRate]] = None
    floater_type: FloaterType = FloaterType.STANDARD
    inverse_spec: Optional[InverseFloaterSpec] = None 