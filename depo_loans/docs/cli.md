# Command Line Interface Documentation

The application provides a command-line interface for analyzing deposits and loans.

## Commands

### Analyze Instrument

Analyze a deposit or loan instrument, calculating valuation and risk metrics:

```bash
python -m depo_loans.cli analyze instrument.json \
    --valuation-date 2023-07-01 \
    --market-data-file market_data.json \
    --output results.json
```

### Project Cashflows

Project cashflows for an instrument within a specified date range:

```bash
python -m depo_loans.cli cashflows instrument.json \
    --start-date 2023-01-01 \
    --end-date 2023-12-31
```

## Input File Formats

### Instrument JSON

Example of an inverse floater deposit:

```json
{
    "type": "TimeDeposit",
    "id": "INV001",
    "name": "1Y USD Inverse Floater",
    "status": "ACTIVE",
    "currency": "USD",
    "issue_date": "2023-01-01",
    "maturity_date": "2024-01-01",
    "counterparty_id": "CP001",
    "counterparty_rating": "A",
    "booking_entity": "BANK001",
    "trading_book": "BANKING",
    "cost_center": "CC001",
    "principal": 1000000.0,
    "interest_rate": {
        "type": "FLOATING",
        "value": 0.05,
        "floater_type": "INVERSE",
        "inverse_spec": {
            "reference_rate": "LIBOR",
            "multiplier": -1.0,
            "constant": 0.10,
            "cap": 0.08,
            "floor": 0.02
        },
        "reset_frequency": "QUARTERLY"
    },
    "payment_frequency": "QUARTERLY",
    "day_count_convention": "ACT_360",
    "compounding_frequency": "QUARTERLY"
}
```

### Market Data JSON

Example market data file:

```json
{
    "discount_curve": {
        "1M": 0.04,
        "3M": 0.045,
        "6M": 0.05,
        "1Y": 0.055
    },
    "rating_transitions": {
        "A": {
            "AA": 0.05,
            "A": 0.85,
            "BBB": 0.08,
            "DEFAULT": 0.02
        }
    },
    "default_rates": {
        "AA": 0.01,
        "A": 0.02,
        "BBB": 0.05
    },
    "recovery_rates": {
        "AA": 0.6,
        "A": 0.5,
        "BBB": 0.4
    }
}
``` 