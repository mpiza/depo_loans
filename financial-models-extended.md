# Extended Financial Models Specification

## 1. Additional Analytics Fields

### Risk Analytics Extensions
```typescript
interface RiskMetrics {
    // Market Risk
    modifiedDuration: number;
    convexity: number;
    dollarDuration: number;
    bpvBucket: {[tenor: string]: number};  // Basis point value by tenor
    valueAtRisk: {
        confidence99: number;
        confidence95: number;
        historicalPeriodDays: number;
    };
    
    // Credit Risk
    probabilityOfDefault: number;
    lossGivenDefault: number;
    expectedLoss: number;
    creditValuationAdjustment: number;
    exposureAtDefault: number;
    
    // Liquidity Risk
    liquidityScore: number;      // 1-10 scale
    estimatedLiquidationPeriod: number;  // Days
    bidAskSpread: number;
    
    // Last calculation timestamps
    lastCalculationDate: Date;
    nextCalculationDue: Date;
}

interface BaseInstrument {
    // ... previous fields ...
    riskMetrics: RiskMetrics;
    
    // Portfolio Attribution
    benchmarkId: string;
    trackingError: number;
    informationRatio: number;
    
    // Regulatory
    regulatoryClass: string;
    riskWeightedAssets: number;
    regulatoryCapital: number;
    
    // ESG Metrics
    esgScore: {
        environmental: number;
        social: number;
        governance: number;
        lastUpdateDate: Date;
    };
}
```

### Instrument-Specific Analytics Extensions

```typescript
interface TimeDeposit {
    // ... previous fields ...
    optionAdjustedSpread: number;
    effectiveDuration: number;
    optionAdjustedDuration: number;
    earlyWithdrawalProbability: number;
}

interface TermLoan {
    // ... previous fields ...
    
    // Credit Analysis
    debtServiceCoverageRatio: number;
    totalLeverageRatio: number;
    seniorLeverageRatio: number;
    interestCoverageRatio: number;
    
    // Industry Analysis
    industryCode: string;
    industryConcentration: number;
    peerComparisonMetrics: {
        leveragePercentile: number;
        marginPercentile: number;
        growthPercentile: number;
    };
    
    // Cash Flow Analysis
    projectedCashFlows: CashFlowProjection[];
}

interface DirectLoan {
    // ... previous fields ...
    
    // Enterprise Valuation
    valuationMetrics: {
        evToEbitda: number;
        priceToEarnings: number;
        priceToBook: number;
        lastValuationDate: Date;
    };
    
    // Performance Monitoring
    performanceMetrics: {
        quarterlyRevenueTrend: number[];
        quarterlyEbitdaTrend: number[];
        workingCapitalRatio: number;
        cashConversionCycle: number;
    };
}
```

## 2. Database Schema Definitions

```sql
-- Base Tables
CREATE TABLE instruments (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    currency CHAR(3) NOT NULL,
    issue_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    counterparty_id VARCHAR(50) NOT NULL,
    counterparty_rating VARCHAR(10),
    booking_entity VARCHAR(50) NOT NULL,
    trading_book VARCHAR(50) NOT NULL,
    cost_center VARCHAR(50) NOT NULL,
    last_modified_date TIMESTAMP NOT NULL,
    last_modified_by VARCHAR(50) NOT NULL,
    
    -- Risk Metrics
    modified_duration DECIMAL(10,6),
    convexity DECIMAL(10,6),
    probability_of_default DECIMAL(5,4),
    loss_given_default DECIMAL(5,4),
    regulatory_capital DECIMAL(15,2),
    
    CONSTRAINT fk_counterparty 
        FOREIGN KEY (counterparty_id) 
        REFERENCES counterparties(id)
);

-- Time Deposits
CREATE TABLE time_deposits (
    instrument_id VARCHAR(50) PRIMARY KEY,
    principal DECIMAL(15,2) NOT NULL,
    interest_rate_type VARCHAR(20) NOT NULL,
    interest_rate_value DECIMAL(10,6) NOT NULL,
    payment_frequency VARCHAR(20) NOT NULL,
    day_count_convention VARCHAR(20) NOT NULL,
    early_withdrawal_allowed BOOLEAN NOT NULL,
    early_withdrawal_penalty DECIMAL(5,4),
    is_callable BOOLEAN NOT NULL,
    
    CONSTRAINT fk_instrument 
        FOREIGN KEY (instrument_id) 
        REFERENCES instruments(id)
);

-- Syndicated Loans
CREATE TABLE syndicated_loans (
    instrument_id VARCHAR(50) PRIMARY KEY,
    facility_amount DECIMAL(15,2) NOT NULL,
    outstanding_amount DECIMAL(15,2) NOT NULL,
    amortization_type VARCHAR(20) NOT NULL,
    default_spread DECIMAL(10,6) NOT NULL,
    upfront_fee DECIMAL(5,4) NOT NULL,
    agent_bank VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_instrument 
        FOREIGN KEY (instrument_id) 
        REFERENCES instruments(id)
);

-- Additional tables for complex relationships
CREATE TABLE loan_participants (
    loan_id VARCHAR(50),
    participant_id VARCHAR(50),
    participation_amount DECIMAL(15,2) NOT NULL,
    participation_percentage DECIMAL(5,4) NOT NULL,
    
    PRIMARY KEY (loan_id, participant_id),
    CONSTRAINT fk_loan 
        FOREIGN KEY (loan_id) 
        REFERENCES syndicated_loans(instrument_id)
);
```

## 3. Validation Rules and Business Logic

```typescript
interface ValidationRules {
    // Common Validations
    common: {
        maturityDateAfterIssueDate: (instrument: BaseInstrument) => boolean;
        validCurrencyCode: (currency: string) => boolean;
        validCounterpartyRating: (rating: string) => boolean;
        positiveAmount: (amount: number) => boolean;
    };
    
    // Time Deposit Validations
    timeDeposit: {
        validInterestRate: (rate: number) => boolean;
        validPenaltyRate: (penalty: number) => boolean;
        validDayCount: (convention: DayCount) => boolean;
        validateCallSchedule: (schedule: CallOption[]) => boolean;
    };
    
    // Syndicated Loan Validations
    syndicatedLoan: {
        participationsTotal100Percent: (participants: LoanParticipant[]) => boolean;
        validFacilityAmount: (amount: number) => boolean;
        outstandingLessThanFacility: (outstanding: number, facility: number) => boolean;
        validCovenantThresholds: (covenants: Covenant[]) => boolean;
    };
}

interface BusinessLogic {
    // Interest Calculations
    calculateAccruedInterest: (instrument: BaseInstrument) => number;
    calculateNextPaymentDate: (instrument: BaseInstrument) => Date;
    calculateBreakFunding: (instrument: BaseInstrument, breakDate: Date) => number;
    
    // Risk Calculations
    calculateRiskMetrics: (instrument: BaseInstrument) => RiskMetrics;
    calculateRegulatoryCaptial: (instrument: BaseInstrument) => number;
    
    // Portfolio Management
    calculateConcentration: (instrument: BaseInstrument, portfolio: Portfolio) => number;
    calculateContribution: (instrument: BaseInstrument, portfolio: Portfolio) => ContributionMetrics;
}
```

## 4. Analytics Calculations

```typescript
interface AnalyticsEngine {
    // Market Risk Analytics
    marketRisk: {
        calculateModifiedDuration: (
            cashflows: CashFlow[],
            yieldCurve: YieldCurve
        ) => number;
        
        calculateConvexity: (
            cashflows: CashFlow[],
            yieldCurve: YieldCurve
        ) => number;
        
        calculateOptionAdjustedSpread: (
            instrument: TimeDeposit,
            volatilitySurface: VolatilitySurface
        ) => number;
    };
    
    // Credit Risk Analytics
    creditRisk: {
        calculateProbabilityOfDefault: (
            financials: FinancialMetrics,
            marketData: MarketData
        ) => number;
        
        calculateLossGivenDefault: (
            collateral: Collateral[],
            seniority: number,
            industryRecoveryRates: RecoveryRates
        ) => number;
        
        calculateExpectedLoss: (
            exposure: number,
            pd: number,
            lgd: number
        ) => number;
    };
    
    // Performance Analytics
    performance: {
        calculateTotalReturn: (
            instrument: BaseInstrument,
            startDate: Date,
            endDate: Date
        ) => number;
        
        calculateYieldToMaturity: (
            cashflows: CashFlow[],
            price: number
        ) => number;
        
        calculateInformationRatio: (
            returns: number[],
            benchmarkReturns: number[]
        ) => number;
    };
    
    // Portfolio Analytics
    portfolio: {
        calculateConcentration: (
            portfolio: Portfolio,
            groupingFactor: string
        ) => ConcentrationMetrics;
        
        calculateValueAtRisk: (
            portfolio: Portfolio,
            confidenceLevel: number,
            timePeriod: number
        ) => number;
        
        calculateTrackingError: (
            portfolioReturns: number[],
            benchmarkReturns: number[]
        ) => number;
    };
}

// Implementation example for key calculations
class AnalyticsImplementation implements AnalyticsEngine {
    marketRisk = {
        calculateModifiedDuration: (cashflows: CashFlow[], yieldCurve: YieldCurve): number => {
            let duration = 0;
            let price = 0;
            
            cashflows.forEach(cf => {
                const t = this.yearFraction(cf.date);
                const r = yieldCurve.rateForTenor(t);
                const df = Math.exp(-r * t);
                
                duration += t * cf.amount * df;
                price += cf.amount * df;
            });
            
            return duration / price;
        }
        // ... other implementations
    };
    
    creditRisk = {
        calculateProbabilityOfDefault: (
            financials: FinancialMetrics,
            marketData: MarketData
        ): number => {
            // Merton model implementation
            const assetValue = financials.totalAssets;
            const debtValue = financials.totalLiabilities;
            const assetVolatility = marketData.equityVolatility;
            const timeToMaturity = 1; // 1 year
            
            const d1 = (Math.log(assetValue / debtValue) + 
                      (marketData.riskFreeRate + assetVolatility * assetVolatility / 2) * 
                      timeToMaturity) / 
                      (assetVolatility * Math.sqrt(timeToMaturity));
            
            const d2 = d1 - assetVolatility * Math.sqrt(timeToMaturity);
            
            return this.normalCDF(-d2);
        }
        // ... other implementations
    };
}
```

Would you like me to:
1. Add more specific analytics calculations for any particular instrument type?
2. Develop test cases for these implementations?
3. Create performance optimization guidelines?
4. Add more detailed documentation for specific calculations?