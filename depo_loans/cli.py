import click
import json
from datetime import datetime
from typing import Dict
from .models.base import (
    BaseInstrument, 
    RateType, 
    PaymentFrequency, 
    DayCountConvention,
    InstrumentStatus
)
from .models.deposits import TimeDeposit, InterestRate
from .models.rate_features import (
    RateCap, 
    RateFloor, 
    InverseFloaterSpec, 
    FloaterType
)
from .analytics.valuation import ValuationEngine
from .analytics.credit_risk import CreditRiskAnalytics

@click.group()
def cli():
    """Deposits and Loans Analytics CLI"""
    pass

@cli.command()
@click.argument('instrument_file', type=click.Path(exists=True))
@click.option('--valuation-date', type=click.DateTime(), default=str(datetime.now().date()))
@click.option('--market-data-file', type=click.Path(exists=True))
@click.option('--output', type=click.Path())
def analyze(instrument_file: str, valuation_date: datetime, 
           market_data_file: str, output: str):
    """Analyze a deposit or loan instrument"""
    
    # Load instrument
    with open(instrument_file, 'r') as f:
        instrument_data = json.load(f)
    
    # Load market data
    with open(market_data_file, 'r') as f:
        market_data = json.load(f)
    
    # Create instrument
    instrument = create_instrument_from_json(instrument_data)
    
    # Initialize analytics engines
    valuation_engine = ValuationEngine()
    credit_risk_analytics = CreditRiskAnalytics(
        rating_transition_matrix=market_data['rating_transitions'],
        default_rates=market_data['default_rates'],
        recovery_rates=market_data['recovery_rates']
    )
    
    # Calculate metrics
    results = {
        'valuation': {
            'present_value': valuation_engine.calculate_present_value(
                instrument, 
                valuation_date.date(), 
                market_data['discount_curve']
            ),
            'ytm': valuation_engine.calculate_yield_to_maturity(
                instrument,
                market_data['market_price']
            )
        },
        'risk_metrics': {
            'duration_convexity': valuation_engine.calculate_duration_convexity(
                instrument,
                market_data['yield_rate']
            ),
            'z_spread': valuation_engine.calculate_z_spread(
                instrument,
                market_data['market_price'],
                market_data['discount_curve']
            )
        },
        'credit_metrics': credit_risk_analytics.calculate_credit_metrics(
            instrument,
            market_data
        ).__dict__
    }
    
    # Output results
    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
    else:
        click.echo(json.dumps(results, indent=2, default=str))

@cli.command()
@click.argument('instrument_file', type=click.Path(exists=True))
@click.option('--start-date', type=click.DateTime())
@click.option('--end-date', type=click.DateTime())
def cashflows(instrument_file: str, start_date: datetime, end_date: datetime):
    """Project cashflows for an instrument"""
    
    # Load instrument
    with open(instrument_file, 'r') as f:
        instrument_data = json.load(f)
    
    instrument = create_instrument_from_json(instrument_data)
    valuation_engine = ValuationEngine()
    
    cashflows = valuation_engine.project_cashflows(instrument)
    
    # Filter cashflows by date if specified
    if start_date:
        cashflows = [cf for cf in cashflows if cf.payment_date >= start_date.date()]
    if end_date:
        cashflows = [cf for cf in cashflows if cf.payment_date <= end_date.date()]
    
    # Output cashflows
    for cf in cashflows:
        click.echo(f"{cf.payment_date}: {cf.payment_type} - {cf.amount:,.2f}")

def create_instrument_from_json(data: Dict) -> BaseInstrument:
    """Create instrument instance from JSON data"""
    if data['type'] == 'TimeDeposit':
        interest_rate = InterestRate(
            type=RateType[data['interest_rate']['type']],
            value=data['interest_rate']['value'],
            spread=data['interest_rate'].get('spread'),
            reference_rate=data['interest_rate'].get('reference_rate'),
            reset_frequency=PaymentFrequency[data['interest_rate'].get('reset_frequency', 'QUARTERLY')],
            floater_type=FloaterType[data['interest_rate'].get('floater_type', 'STANDARD')]
        )
        
        # Add inverse floater spec if applicable
        if interest_rate.floater_type == FloaterType.INVERSE:
            interest_rate.inverse_spec = InverseFloaterSpec(
                reference_rate=data['interest_rate']['inverse_spec']['reference_rate'],
                multiplier=data['interest_rate']['inverse_spec']['multiplier'],
                constant=data['interest_rate']['inverse_spec']['constant'],
                cap=data['interest_rate']['inverse_spec'].get('cap'),
                floor=data['interest_rate']['inverse_spec'].get('floor')
            )
        
        return TimeDeposit(
            id=data['id'],
            name=data['name'],
            status=InstrumentStatus[data['status']],
            currency=data['currency'],
            issue_date=datetime.strptime(data['issue_date'], '%Y-%m-%d').date(),
            maturity_date=datetime.strptime(data['maturity_date'], '%Y-%m-%d').date(),
            counterparty_id=data['counterparty_id'],
            counterparty_rating=data['counterparty_rating'],
            booking_entity=data['booking_entity'],
            trading_book=data['trading_book'],
            cost_center=data['cost_center'],
            principal=data['principal'],
            interest_rate=interest_rate,
            payment_frequency=PaymentFrequency[data['payment_frequency']],
            day_count_convention=DayCountConvention[data['day_count_convention']],
            compounding_frequency=PaymentFrequency[data['compounding_frequency']]
        )
    else:
        raise ValueError(f"Unsupported instrument type: {data['type']}")

if __name__ == '__main__':
    cli() 