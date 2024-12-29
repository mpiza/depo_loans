import unittest
from datetime import date
from ..models.deposits import TimeDeposit, InterestRate
from ..models.rate_features import RateCap, RateFloor, CallOption
from ..models.base import RateType, PaymentFrequency, DayCountConvention, InstrumentStatus
from ..analytics.valuation import ValuationEngine

class TestValuation(unittest.TestCase):
    def setUp(self):
        self.valuation_engine = ValuationEngine()
        self.test_deposit = TimeDeposit(
            id="TEST001",
            name="Test Deposit",
            status=InstrumentStatus.ACTIVE,
            currency="USD",
            issue_date=date(2023, 1, 1),
            maturity_date=date(2024, 1, 1),
            counterparty_id="CP001",
            counterparty_rating="A",
            booking_entity="BANK001",
            trading_book="BANKING",
            cost_center="CC001",
            principal=1000000.0,
            interest_rate=InterestRate(
                type=RateType.FLOATING,
                value=0.05,
                spread=0.01,
                reference_rate="LIBOR",
                reset_frequency=PaymentFrequency.QUARTERLY,
                cap=RateCap(cap_rate=0.07),
                floor=RateFloor(floor_rate=0.02)
            ),
            payment_frequency=PaymentFrequency.QUARTERLY,
            day_count_convention=DayCountConvention.ACT_360,
            compounding_frequency=PaymentFrequency.QUARTERLY,
            allow_early_withdrawal=False,
            is_callable=True,
            call_schedule=[
                CallOption(
                    call_date=date(2023, 7, 1),
                    call_price=1.01,
                    notice_days=30
                )
            ]
        )

    def test_cashflow_projection(self):
        cashflows = self.valuation_engine.project_cashflows(self.test_deposit)
        self.assertTrue(len(cashflows) > 0)
        
        # Verify interest payments
        interest_cfs = [cf for cf in cashflows if cf.payment_type == "INTEREST"]
        self.assertEqual(len(interest_cfs), 4)  # Quarterly payments for 1 year
        
        # Verify principal payment
        principal_cfs = [cf for cf in cashflows if cf.payment_type == "PRINCIPAL"]
        self.assertEqual(len(principal_cfs), 1)
        self.assertEqual(principal_cfs[0].amount, self.test_deposit.principal)

    def test_rate_caps_and_floors(self):
        # Test with rate above cap
        high_rate_deposit = self.test_deposit
        high_rate_deposit.interest_rate.value = 0.08
        cashflows = self.valuation_engine.project_cashflows(high_rate_deposit)
        interest_cf = next(cf for cf in cashflows if cf.payment_type == "INTEREST")
        self.assertLess(interest_cf.amount, 
                       high_rate_deposit.principal * 0.08 * 0.25)  # Quarterly payment

        # Test with rate below floor
        low_rate_deposit = self.test_deposit
        low_rate_deposit.interest_rate.value = 0.01
        cashflows = self.valuation_engine.project_cashflows(low_rate_deposit)
        interest_cf = next(cf for cf in cashflows if cf.payment_type == "INTEREST")
        self.assertGreater(interest_cf.amount, 
                          low_rate_deposit.principal * 0.01 * 0.25)

    def test_option_adjusted_value(self):
        discount_curve = {
            "1M": 0.04,
            "3M": 0.045,
            "6M": 0.05,
            "1Y": 0.055
        }
        
        # Calculate straight PV and OAS PV
        straight_pv = self.valuation_engine.calculate_present_value(
            self.test_deposit, date(2023, 1, 1), discount_curve
        )
        oas_pv = self.valuation_engine.calculate_option_adjusted_value(
            self.test_deposit, date(2023, 1, 1), discount_curve, volatility=0.2
        )
        
        # OAS value should be less than straight PV due to call option
        self.assertLess(oas_pv, straight_pv) 