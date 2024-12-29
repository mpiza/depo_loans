from datetime import date
from ..models.base import DayCountConvention

class DayCountCalculator:
    def calculate_dcf(self, start_date: date, end_date: date, 
                     convention: DayCountConvention) -> float:
        if convention == DayCountConvention.ACT_360:
            return self._actual_days(start_date, end_date) / 360
        elif convention == DayCountConvention.ACT_365:
            return self._actual_days(start_date, end_date) / 365
        elif convention == DayCountConvention.THIRTY_360:
            return self._thirty_360_days(start_date, end_date) / 360
        elif convention == DayCountConvention.ACT_ACT:
            return self._actual_actual(start_date, end_date)
        else:
            raise ValueError(f"Unsupported day count convention: {convention}")

    def _actual_days(self, start_date: date, end_date: date) -> int:
        return (end_date - start_date).days

    def _thirty_360_days(self, start_date: date, end_date: date) -> int:
        y1, m1, d1 = start_date.year, start_date.month, start_date.day
        y2, m2, d2 = end_date.year, end_date.month, end_date.day
        
        # Adjust day counts
        if d1 == 31:
            d1 = 30
        if d2 == 31 and d1 >= 30:
            d2 = 30
            
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) 