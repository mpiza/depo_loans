from datetime import date
from typing import Dict, List
import numpy as np
from dateutil.relativedelta import relativedelta
from ..models.base import PaymentFrequency

class CurveUtils:
    @staticmethod
    def interpolate_rate(curve: Dict[str, float], target_tenor: float) -> float:
        """Linear interpolation of rates"""
        tenors = sorted([(CurveUtils._tenor_to_years(k), v) for k, v in curve.items()])
        
        # Find surrounding points
        for i in range(len(tenors)-1):
            if tenors[i][0] <= target_tenor <= tenors[i+1][0]:
                x1, y1 = tenors[i]
                x2, y2 = tenors[i+1]
                return y1 + (y2-y1) * (target_tenor-x1)/(x2-x1)
                
        # Extrapolate if outside range
        if target_tenor < tenors[0][0]:
            return tenors[0][1]
        return tenors[-1][1]

    @staticmethod
    def _tenor_to_years(tenor: str) -> float:
        """Convert tenor string to years"""
        value = float(tenor[:-1])
        unit = tenor[-1].upper()
        
        if unit == 'D':
            return value/365
        elif unit == 'W':
            return value/52
        elif unit == 'M':
            return value/12
        elif unit == 'Y':
            return value
        raise ValueError(f"Invalid tenor format: {tenor}")

    @staticmethod
    def generate_schedule(start_date: date, end_date: date, 
                         frequency: PaymentFrequency) -> List[date]:
        """Generate payment schedule"""
        dates = []
        current = start_date
        
        freq_map = {
            PaymentFrequency.MONTHLY: relativedelta(months=1),
            PaymentFrequency.QUARTERLY: relativedelta(months=3),
            PaymentFrequency.SEMI_ANNUAL: relativedelta(months=6),
            PaymentFrequency.ANNUAL: relativedelta(years=1)
        }
        
        delta = freq_map.get(frequency)
        if not delta:
            raise ValueError(f"Unsupported frequency: {frequency}")
            
        while current <= end_date:
            dates.append(current)
            current += delta
            
        if dates[-1] != end_date:
            dates.append(end_date)
            
        return dates 