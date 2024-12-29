# Financial Instruments Data Models

## Common Base Fields
All instruments share these base attributes:
```typescript
interface BaseInstrument {
    id: string;                     // Unique identifier
    name: string;                   // Instrument name
    status: InstrumentStatus;       // Active, Matured, Defaulted, etc.
    currency: string;               // ISO currency code
    issueDate: Date;               // Origination date
    maturityDate: Date;            // Final maturity date
    counterpartyId: string;        // Legal entity identifier
    counterpartyRating: string;    // Credit rating
    bookingEntity: string;         // Legal entity holding the instrument
    tradingBook: string;           // Trading/banking book classification
    costCenter: string;            // Business unit identifier
    lastModifiedDate: Date;        // Audit timestamp
    lastModifiedBy: string;        // User identifier
}

enum InstrumentStatus {
    Active,
    Matured,
    Defaulted,
    Restructured,
    Cancelled
}
```

## 1. Deposits

### Time Deposit
```typescript
interface TimeDeposit extends BaseInstrument {
    // Core attributes
    principal: number;             // Initial deposit amount
    interestRate: InterestRate;    // Rate details
    paymentFrequency: Frequency;   // Interest payment schedule
    rolloverType: RolloverType;    // Automatic/Manual rollover
    
    // Interest calculation
    dayCountConvention: DayCount;  // ACT/360, 30/360, etc.
    compoundingFrequency: Frequency;
    paymentCalendar: string[];     // Holiday calendars
    
    // Early withdrawal
    allowEarlyWithdrawal: boolean;
    earlyWithdrawalPenalty: number; // Percentage or fixed amount
    
    // Call features (if callable)
    isCallable: boolean;
    callSchedule?: CallOption[];
}

interface InterestRate {
    type: RateType;               // Fixed, Floating, Step-up
    value: number;                // Current rate value
    spread?: number;              // Spread for floating rate
    referenceRate?: string;       // LIBOR, SOFR, etc.
    resetFrequency?: Frequency;   // For floating rates
    rateSchedule?: StepSchedule[]; // For step-up/down rates
}
```

### Demand Deposit
```typescript
interface DemandDeposit extends BaseInstrument {
    // Account details
    accountNumber: string;
    accountType: DemandAccountType;
    currentBalance: number;
    availableBalance: number;
    
    // Interest terms
    interestRate: InterestRate;
    minimumBalance: number;
    tierSchedule: BalanceTier[];
    
    // Operational limits
    dailyWithdrawalLimit: number;
    monthlyWithdrawalLimit: number;
    
    // Service charges
    monthlyServiceCharge: number;
    excessActivityCharge: number;
}
```

## 2. Syndicated Loans

### Term Loan
```typescript
interface TermLoan extends BaseInstrument {
    // Facility details
    facilityAmount: number;
    outstandingAmount: number;
    amortizationType: AmortizationType;
    
    // Interest terms
    interestRate: InterestRate;
    defaultSpread: number;
    interestPeriods: InterestPeriod[];
    paymentFrequency: Frequency;
    
    // Fees
    upfrontFee: number;
    commitmentFee: number;
    agentFee: number;
    
    // Syndicate structure
    participants: LoanParticipant[];
    agentBank: string;
    
    // Covenants
    financialCovenants: Covenant[];
    
    // Security
    collateral: Collateral[];
    guarantors: string[];
    
    // Payment schedule
    repaymentSchedule: RepaymentEvent[];
}

interface LoanParticipant {
    participantId: string;
    participationAmount: number;
    participationPercentage: number;
    transferable: boolean;
    minimumHoldAmount: number;
}
```

### Revolving Credit Facility
```typescript
interface RevolvingFacility extends BaseInstrument {
    // Facility details
    totalCommitment: number;
    availableAmount: number;
    utilizationAmount: number;
    
    // Drawing options
    allowedCurrencies: string[];
    minimumDrawAmount: number;
    drawingPeriod: Period;
    
    // Interest and fees
    interestRate: InterestRate;
    utilizationFee: UtilizationFee[];
    commitmentFee: number;
    
    // Operational details
    noticePeriod: number;         // Notice required for drawings
    cleanDownProvision?: {
        frequency: Frequency;
        durationDays: number;
        targetUtilization: number;
    }
}
```

## 3. Private Credit

### Direct Lending
```typescript
interface DirectLoan extends BaseInstrument {
    // Loan details
    principalAmount: number;
    outstandingAmount: number;
    loanType: DirectLoanType;     // Senior, Unitranche, etc.
    
    // Interest terms
    interestRate: InterestRate;
    PIKInterest?: {              // Payment-in-kind
        rate: number;
        compoundingFrequency: Frequency;
    }
    
    // Security and ranking
    securityRank: number;        // 1 = most senior
    collateral: Collateral[];
    guarantors: string[];
    
    // Enterprise details
    borrowerFinancials: {
        lastReportDate: Date;
        revenue: number;
        ebitda: number;
        totalDebt: number;
        enterpriseValue: number;
    }
    
    // Covenants
    financialCovenants: Covenant[];
    
    // Exit provisions
    prepaymentFee: PrepaymentFee[];
    changeOfControlProvision: boolean;
}

interface Collateral {
    type: CollateralType;
    description: string;
    value: number;
    valuationDate: Date;
    valuationMethod: string;
    ltvRatio: number;            // Loan-to-Value
    independentValuation: boolean;
}
```

### Specialty Finance
```typescript
interface SpecialtyFinance extends BaseInstrument {
    // Asset details
    assetType: SpecialtyAssetType;
    assetValue: number;
    assetDescription: string;
    
    // Financing terms
    advanceRate: number;         // Percentage of asset value
    maximumAmount: number;
    outstandingAmount: number;
    
    // Interest and fees
    interestRate: InterestRate;
    servicing: {
        servicerId: string;
        servicingFee: number;
        collectionAccount: string;
    }
    
    // Performance metrics
    delinquencyStatus: DelinquencyStatus;
    daysDelinquent: number;
    collectionHistory: CollectionEvent[];
}
```

## Supporting Types
```typescript
enum Frequency {
    Daily,
    Weekly,
    Monthly,
    Quarterly,
    SemiAnnual,
    Annual
}

enum DayCount {
    ACT_360,
    ACT_365,
    THIRTY_360,
    ACT_ACT
}

interface StepSchedule {
    effectiveDate: Date;
    rate: number;
}

interface BalanceTier {
    minimumBalance: number;
    rate: number;
}

interface Covenant {
    type: CovenantType;
    description: string;
    threshold: number;
    testingFrequency: Frequency;
    lastTestDate: Date;
    lastTestResult: boolean;
}

interface RepaymentEvent {
    dueDate: Date;
    principalAmount: number;
    expectedInterestAmount: number;
}

interface PrepaymentFee {
    periodStart: Date;
    periodEnd: Date;
    feePercentage: number;
}
```
