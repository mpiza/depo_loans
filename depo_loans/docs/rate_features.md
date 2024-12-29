# Rate Features Documentation

## Caps and Floors

The application supports interest rate caps and floors for both deposits and loans. These features help manage interest rate risk by setting upper and lower bounds on the floating rate.

### Rate Cap
- Limits the maximum interest rate that can be applied
- Can be set for specific time periods
- Useful for borrowers to protect against rising rates

### Rate Floor
- Sets the minimum interest rate that will be applied
- Can be set for specific time periods
- Protects lenders against falling rates

## Call Options

Call options give the issuer the right to redeem the instrument before maturity.

### Features
- Multiple call dates can be specified
- Each call option has a call price (usually as % of principal)
- Notice period can be specified
- Option-adjusted valuation available

## Usage Example

```python
from depo_loans.models.deposits import TimeDeposit, InterestRate
from depo_loans.models.rate_features import RateCap, RateFloor, CallOption

# Create a deposit with cap, floor, and call option
deposit = TimeDeposit(
    # ... basic parameters ...
    interest_rate=InterestRate(
        type=RateType.FLOATING,
        value=0.05,
        spread=0.01,
        cap=RateCap(cap_rate=0.07),
        floor=RateFloor(floor_rate=0.02)
    ),
    is_callable=True,
    call_schedule=[
        CallOption(
            call_date=date(2024, 1, 1),
            call_price=1.01,
            notice_days=30
        )
    ]
)

# Calculate option-adjusted value
valuation_engine = ValuationEngine()
oas_value = valuation_engine.calculate_option_adjusted_value(
    deposit,
    valuation_date=date(2023, 1, 1),
    discount_curve=discount_curve,
    volatility=0.2
) 