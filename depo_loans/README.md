# Deposits and Loans Analytics

A Python application for analyzing deposits and loans, providing risk metrics, valuation, and performance analytics.

## Features

- Support for Time Deposits and Term Loans
- Risk Analytics (duration, convexity, credit metrics)
- Valuation Engine with cash flow projection
- Performance Analytics for portfolio management
- Covenant tracking and monitoring

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```python
from depo_loans.models.deposits import TimeDeposit, InterestRate
from depo_loans.analytics.risk_metrics import RiskAnalytics
from depo_loans.analytics.valuation import ValuationEngine

# Create a deposit
deposit = TimeDeposit(
    id="DEP001",
    name="3M USD Deposit",
    # ... other parameters
)

# Calculate risk metrics
risk_analytics = RiskAnalytics()
metrics = risk_analytics.calculate_risk_metrics(deposit)

# Calculate present value
valuation_engine = ValuationEngine()
pv = valuation_engine.calculate_present_value(deposit, valuation_date, discount_curve)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 