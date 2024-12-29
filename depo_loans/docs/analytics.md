# Analytics Documentation

## Valuation Methods

### Yield to Maturity (YTM)
The yield to maturity is calculated using the Newton-Raphson method, which iteratively finds the yield that makes the present value of all cash flows equal to the market price.

```python
ytm = valuation_engine.calculate_yield_to_maturity(instrument, market_price)
```

### Z-Spread
The Z-spread is the parallel spread that needs to be added to the zero curve to match the market price. It's calculated using the Newton-Raphson method.

```python
z_spread = valuation_engine.calculate_z_spread(
    instrument, market_price, discount_curve
)
```

### Duration and Convexity
Modified duration and convexity are calculated using finite differences:
- Modified Duration measures the price sensitivity to yield changes
- Convexity measures the curvature of the price-yield relationship

```python
duration, convexity = valuation_engine.calculate_duration_convexity(
    instrument, yield_rate
)
```

## Rate Features

### Step-Up Rates
Step-up rates allow for predefined rate increases at specific dates:

```python
deposit = TimeDeposit(
    interest_rate=InterestRate(
        type=RateType.STEP_UP,
        value=0.05,
        step_up_schedule=[
            StepUpRate(date(2023, 7, 1), 0.06),
            StepUpRate(date(2024, 1, 1), 0.07)
        ]
    )
)
```

### Caps and Floors with Time Windows
Caps and floors can be applied for specific time periods:

```python
interest_rate = InterestRate(
    type=RateType.FLOATING,
    value=0.05,
    cap=RateCap(
        cap_rate=0.07,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    ),
    floor=RateFloor(
        floor_rate=0.02,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31)
    )
)
``` 