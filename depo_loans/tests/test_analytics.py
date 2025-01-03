import unittest
from datetime import date
from ..models.base import RateType, PaymentFrequency, DayCountConvention, InstrumentStatus
from ..models.deposits import TimeDeposit, InterestRate
from ..models.rate_features import RateCap, RateFloor, CallOption, StepUpRate, FloaterType
from ..analytics.valuation import ValuationEngine

class TestAnalytics(unittest.TestCase):
    def setUp(self):
        self.valuation_engine = ValuationEngine()
        self.discount_curve = {
            "1M": 0.04,
            "3M": 0.045,
            "6M": 0.05,
            "1Y": 0.055
        }

    def test_step_up_rates(self):
        deposit = TimeDeposit(
            id="TEST001",
            name="Test Step-up Deposit",
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
                type=RateType.STEP_UP,
                value=0.05,
                step_up_schedule=[
                    StepUpRate(date(2023, 7, 1), 0.06),
                    StepUpRate(date(2024, 1, 1), 0.07)
                ]
            ),
            payment_frequency=PaymentFrequency.QUARTERLY,
            day_count_convention=DayCountConvention.ACT_360,
            compounding_frequency=PaymentFrequency.QUARTERLY,
            allow_early_withdrawal=False
        )
        
        cashflows = self.valuation_engine.project_cashflows(deposit)
        
        # Verify step-up rates are applied correctly
        for cf in cashflows:
            if cf.payment_type == "INTEREST":
                if cf.payment_date < date(2023, 7, 1):
                    self.assertAlmostEqual(
                        cf.amount / deposit.principal / 0.25, 0.05, places=4
                    )
                elif cf.payment_date < date(2024, 1, 1):
                    self.assertAlmostEqual(
                        cf.amount / deposit.principal / 0.25, 0.06, places=4
                    )
                else:
                    self.assertAlmostEqual(
                        cf.amount / deposit.principal / 0.25, 0.07, places=4
                    )

    def create_test_deposit(self) -> TimeDeposit:
        """Helper method to create a test deposit"""
        return TimeDeposit(
            id="TEST002",
            name="Test Floating Deposit",
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
                floater_type=FloaterType.STANDARD
            ),
            payment_frequency=PaymentFrequency.QUARTERLY,
            day_count_convention=DayCountConvention.ACT_360,
            compounding_frequency=PaymentFrequency.QUARTERLY,
            allow_early_withdrawal=False
        )

    def test_ytm_calculation(self):
        deposit = self.create_test_deposit()
        market_price = 980000  # Assuming some discount to par
        
        ytm = self.valuation_engine.calculate_yield_to_maturity(
            deposit, market_price
        )
        
        # Calculate price using computed YTM
        calculated_price = self.valuation_engine._calculate_price_with_ytm(
            deposit, ytm
        )
        
        # Verify the price matches the market price
        self.assertAlmostEqual(calculated_price, market_price, places=2)

    def test_z_spread_calculation(self):
        deposit = self.create_test_deposit()
        market_price = 990000
        
        z_spread = self.valuation_engine.calculate_z_spread(
            deposit,
            market_price,
            self.discount_curve
        )
        
        # Calculate price using computed Z-spread
        calculated_price = self.valuation_engine._calculate_price_with_spread(
            deposit,
            self.discount_curve,
            z_spread
        )
        
        # Verify the price matches the market price
        self.assertAlmostEqual(calculated_price, market_price, places=2)

    def test_duration_convexity(self):
        deposit = self.create_test_deposit()
        yield_rate = 0.05
        
        duration, convexity = self.valuation_engine.calculate_duration_convexity(
            deposit, yield_rate
        )
        
        # Basic sanity checks
        self.assertGreater(duration, 0)
        self.assertGreater(convexity, 0)
        
        # For a 1-year instrument, duration should be less than 1
        self.assertLess(duration, 1.0) 