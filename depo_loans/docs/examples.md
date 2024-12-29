# Examples

This document provides examples of analyzing different types of deposits and loans using the analytics library.

## 1. Simple Fixed Rate Deposit

```python
# Analyze a simple fixed rate deposit
from depo_loans.models.deposits import TimeDeposit, InterestRate
from depo_loans.analytics.valuation import ValuationEngine
from depo_loans.analytics.risk_metrics import RiskAnalytics
from datetime import date

# Market data
discount_curve = {
    "1M": 0.04,
    "3M": 0.045,
    "6M": 0.05,
    "1Y": 0.055
}

# Create and analyze deposit
deposit = TimeDeposit(
    id="DEP001",
    name="6M USD Fixed Deposit",
    status=InstrumentStatus.ACTIVE,
    currency="USD",
    issue_date=date(2023, 7, 1),
    maturity_date=date(2024, 1, 1),
    counterparty_id="CP001",
    counterparty_rating="A",
    booking_entity="BANK001",
    trading_book="BANKING",
    cost_center="CC001",
    principal=1000000.0,
    interest_rate=InterestRate(
        type=RateType.FIXED,
        value=0.05,
        floater_type=FloaterType.STANDARD
    ),
    payment_frequency=PaymentFrequency.QUARTERLY,
    day_count_convention=DayCountConvention.ACT_360,
    compounding_frequency=PaymentFrequency.QUARTERLY,
    allow_early_withdrawal=False
)

# Calculate metrics
valuation_engine = ValuationEngine()
present_value = valuation_engine.calculate_present_value(
    deposit, 
    date(2023, 7, 1), 
    discount_curve
)

# Project cashflows
cashflows = valuation_engine.project_cashflows(deposit)
for cf in cashflows:
    print(f"{cf.payment_date}: {cf.payment_type} - {cf.amount:,.2f}")

# Calculate risk metrics
risk_analytics = RiskAnalytics()
metrics = risk_analytics.calculate_risk_metrics(deposit)
print(f"Modified Duration: {metrics.modified_duration:.4f}")
print(f"Convexity: {metrics.convexity:.4f}")
```

## 2. Floating Rate Deposit with Caps and Floors

```python
# Analyze a floating rate deposit with caps and floors
from depo_loans.models.rate_features import RateCap, RateFloor

# Create deposit with caps and floors
capped_deposit = TimeDeposit(
    # ... basic parameters ...
    interest_rate=InterestRate(
        type=RateType.FLOATING,
        value=0.05,
        spread=0.015,
        reference_rate="SOFR",
        reset_frequency=PaymentFrequency.QUARTERLY,
        floater_type=FloaterType.STANDARD,
        cap=RateCap(
            cap_rate=0.07,
            start_date=date(2023, 7, 1),
            end_date=date(2024, 7, 1)
        ),
        floor=RateFloor(
            floor_rate=0.03,
            start_date=date(2023, 7, 1),
            end_date=date(2024, 7, 1)
        )
    )
)

# Calculate option-adjusted value
volatility = 0.2  # Interest rate volatility
oas_value = valuation_engine.calculate_option_adjusted_value(
    capped_deposit,
    date(2023, 7, 1),
    discount_curve,
    volatility
)
```

## 3. Callable Deposit

```python
# Analyze a callable deposit
from depo_loans.models.rate_features import CallOption

# Create callable deposit
callable_deposit = TimeDeposit(
    # ... basic parameters ...
    is_callable=True,
    call_schedule=[
        CallOption(
            call_date=date(2024, 7, 1),
            call_price=1.01,
            notice_days=30
        ),
        CallOption(
            call_date=date(2025, 1, 1),
            call_price=1.005,
            notice_days=30
        )
    ]
)

# Calculate option-adjusted value
oas_value = valuation_engine.calculate_option_adjusted_value(
    callable_deposit,
    date(2023, 7, 1),
    discount_curve,
    volatility=0.2
)

# Calculate yield metrics
ytm = valuation_engine.calculate_yield_to_maturity(
    callable_deposit,
    market_price=990000
)

z_spread = valuation_engine.calculate_z_spread(
    callable_deposit,
    market_price=990000,
    discount_curve=discount_curve
)
```

## 4. Inverse Floater

```python
# Analyze an inverse floater
from depo_loans.models.rate_features import InverseFloaterSpec

# Create inverse floater
inverse_floater = TimeDeposit(
    # ... basic parameters ...
    interest_rate=InterestRate(
        type=RateType.FLOATING,
        value=0.05,
        floater_type=FloaterType.INVERSE,
        inverse_spec=InverseFloaterSpec(
            reference_rate="SOFR",
            multiplier=-1.0,
            constant=0.10,
            cap=0.08,
            floor=0.02
        ),
        reset_frequency=PaymentFrequency.QUARTERLY
    )
)

# Calculate risk metrics with different rate scenarios
scenarios = {
    "base": {"SOFR": 0.05},
    "up": {"SOFR": 0.06},
    "down": {"SOFR": 0.04}
}

for scenario_name, rates in scenarios.items():
    value = valuation_engine.calculate_present_value(
        inverse_floater,
        date(2023, 7, 1),
        discount_curve,
        market_rates=rates
    )
    print(f"Scenario {scenario_name}: {value:,.2f}")
```

## 5. Complex Term Loan

```python
# Analyze a syndicated term loan
from depo_loans.models.loans import TermLoan, LoanParticipant, Covenant
from depo_loans.analytics.credit_risk import CreditRiskAnalytics

# Create syndicated loan
loan = TermLoan(
    # ... basic parameters ...
    facility_amount=10000000.0,
    outstanding_amount=10000000.0,
    amortization_type="SCHEDULED",
    interest_rate=InterestRate(
        type=RateType.FLOATING,
        value=0.05,
        spread=0.0225,
        reference_rate="SOFR",
        floor=RateFloor(floor_rate=0.0)
    ),
    participants=[
        LoanParticipant(
            participant_id="BANK001",
            participation_amount=4000000.0,
            participation_percentage=0.4,
            transferable=True,
            minimum_hold_amount=2000000.0
        )
        # ... other participants ...
    ],
    financial_covenants=[
        Covenant(
            type="LEVERAGE_RATIO",
            description="Net Debt to EBITDA",
            threshold=3.5,
            testing_frequency=PaymentFrequency.QUARTERLY,
            last_test_date=date(2023, 6, 30),
            last_test_result=True
        )
        # ... other covenants ...
    ]
)

# Calculate credit risk metrics
credit_analytics = CreditRiskAnalytics(
    rating_transition_matrix={
        "BBB": {
            "A": 0.05,
            "BBB": 0.85,
            "BB": 0.08,
            "DEFAULT": 0.02
        }
    },
    default_rates={"BBB": 0.02},
    recovery_rates={"BBB": 0.45}
)

credit_metrics = credit_analytics.calculate_credit_metrics(
    loan,
    market_data={
        "asset_value": 50000000,
        "asset_volatility": 0.3,
        "debt_value": 30000000,
        "risk_free_rate": 0.03
    }
)

print(f"Probability of Default: {credit_metrics.probability_of_default:.2%}")
print(f"Loss Given Default: {credit_metrics.loss_given_default:.2%}")
print(f"Expected Loss: {credit_metrics.expected_loss:,.2f}")
```

## Using the CLI

```bash
# Analyze a simple deposit
python -m depo_loans.cli analyze examples/01_simple_fixed_deposit.json \
    --valuation-date 2023-07-01 \
    --market-data-file market_data.json \
    --output results.json

# Project cashflows for a floating rate deposit
python -m depo_loans.cli cashflows examples/02_floating_rate_deposit.json \
    --start-date 2023-07-01 \
    --end-date 2024-07-01

# Analyze a complex loan
python -m depo_loans.cli analyze examples/06_complex_term_loan.json \
    --valuation-date 2023-07-01 \
    --market-data-file market_data.json \
    --output loan_results.json
``` 