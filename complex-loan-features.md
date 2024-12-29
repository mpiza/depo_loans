# Complex Loan Features Specification

## 1. Multiple Payment Frequencies

```typescript
interface PaymentSchedule {
    // Separating different schedule types
    interestSchedule: {
        paymentFrequency: Frequency;
        rolloverConvention: RolloverConvention;
        businessDayAdjustment: BusinessDayAdjustment;
        paymentCalendars: string[];          // Holiday calendars
        paymentLag: number;                  // Days
        shortPeriodConvention: ShortPeriodConvention;
    };
    
    rateResetSchedule: {
        resetFrequency: Frequency;
        observationMethod: ObservationMethod;
        fixingCalendars: string[];
        fixingLag: number;                   // Days
        lockoutPeriod?: number;              // Days
        lookbackPeriod?: number;             // Days
    };
    
    principalSchedule: {
        paymentFrequency: Frequency;
        amortizationType: AmortizationType;
        businessDayAdjustment: BusinessDayAdjustment;
        paymentCalendars: string[];
    };

    // Schedule synchronization
    periodAlignment: {
        alignmentRule: AlignmentRule;
        masterSchedule: ScheduleType;
        stubHandling: StubHandling;
    };
}

interface ScheduleGenerator {
    generateSchedule: (
        startDate: Date,
        endDate: Date,
        schedule: PaymentSchedule
    ) => SchedulePeriod[];
    
    // Handle schedule adjustments
    adjustForHolidays: (
        dates: Date[],
        calendars: string[],
        convention: BusinessDayAdjustment
    ) => Date[];
    
    // Handle schedule conflicts
    resolveConflicts: (
        interestDates: Date[],
        resetDates: Date[],
        principalDates: Date[],
        alignment: periodAlignment
    ) => AlignedSchedule;
}
```

## 2. Day Count Convention Management

```typescript
interface DayCountManager {
    conventions: {
        interestAccrual: DayCount;
        rateCalculation: DayCount;
        principalAccrual?: DayCount;
        feeCalculation?: DayCount;
    };
    
    calculateFraction: (
        startDate: Date,
        endDate: Date,
        convention: DayCount,
        schedule?: Schedule
    ) => number;
    
    // Handle convention mismatches
    reconcileConventions: (
        amount: number,
        fromConvention: DayCount,
        toConvention: DayCount,
        period: Period
    ) => number;
}

interface InterestCalculator {
    calculatePeriodInterest: (
        principal: number,
        rate: number,
        period: Period,
        conventions: DayCountManager
    ) => InterestResult;
    
    calculateAccruedInterest: (
        principal: number,
        rate: number,
        startDate: Date,
        asOfDate: Date,
        conventions: DayCountManager
    ) => AccruedInterestResult;
}
```

## 3. Complex Amortization

```typescript
interface AmortizationSchedule {
    type: AmortizationType;
    
    // Standard amortization
    standardAmortization?: {
        frequency: Frequency;
        calculationType: AmortizationCalculationType;
        percentageOrAmount: number;
    };
    
    // Custom schedule
    customSchedule?: {
        dates: Date[];
        amounts: number[];
        isPercentage: boolean;
    };
    
    // Balloon payment
    balloonPayment?: {
        date: Date;
        amount: number;
        isPercentage: boolean;
        triggerConditions?: TriggerCondition[];
    };
    
    // Step-up/Step-down
    steps?: {
        dates: Date[];
        amounts: number[];
        isPercentage: boolean;
    };
}

interface AmortizationCalculator {
    calculateAmortizationSchedule: (
        principal: number,
        schedule: AmortizationSchedule,
        interestRate: InterestRate
    ) => AmortizationPeriod[];
    
    recalculateSchedule: (
        currentSchedule: AmortizationPeriod[],
        prepayment: Prepayment
    ) => AmortizationPeriod[];
}

interface AmortizationPeriod {
    date: Date;
    beginningBalance: number;
    payment: number;
    principal: number;
    interest: number;
    endingBalance: number;
    
    // Track modifications
    prepayments: Prepayment[];
    modifications: ScheduleModification[];
}
```

## 4. Revolving Facility Management

```typescript
interface RevolvingFacilityManager {
    // Availability tracking
    availability: {
        totalCommitment: number;
        currentUtilization: number;
        availableAmount: number;
        reservedAmount: number;
        
        // Sublimits
        sublimits: {
            currency?: {[currency: string]: number};
            facility?: {[facilityType: string]: number};
            borrowerEntity?: {[entityId: string]: number};
        };
    };
    
    // Draw management
    drawManagement: {
        minimumDrawAmount: number;
        maximumDraws: number;
        noticePeriod: number;
        allowedCurrencies: string[];
        
        validateDraw: (draw: DrawRequest) => ValidationResult;
        processDraw: (draw: DrawRequest) => DrawResult;
    };
    
    // Repayment management
    repaymentManagement: {
        minimumRepaymentAmount: number;
        noticePeriod: number;
        applicationOrder: ApplicationOrder[];
        
        processRepayment: (repayment: RepaymentRequest) => RepaymentResult;
        reallocateAvailability: (repayment: RepaymentRequest) => AvailabilityUpdate;
    };
}

interface DrawRequest {
    requestDate: Date;
    valueDate: Date;
    amount: number;
    currency: string;
    borrowerEntity: string;
    facilityType: string;
    interestPeriod: Period;
    rateType: RateType;
    purpose?: string;
}

interface RepaymentRequest {
    requestDate: Date;
    valueDate: Date;
    amount: number;
    currency: string;
    borrowerEntity: string;
    drawReferences: string[];     // References to original draws
    applicationInstructions?: ApplicationInstruction[];
}
```

## 5. Covenant Tracking

```typescript
interface CovenantManager {
    covenants: Covenant[];
    
    // Covenant testing
    testCovenant: (
        covenant: Covenant,
        financials: FinancialStatements,
        testDate: Date
    ) => CovenantTestResult;
    
    // Compliance tracking
    trackCompliance: (
        covenantResults: CovenantTestResult[],
        reportingPeriod: Period
    ) => ComplianceReport;
    
    // Waiver management
    waivers: {
        applyWaiver: (waiver: CovenantWaiver) => WaiverResult;
        trackWaivers: (covenant: Covenant) => WaiverHistory;
    };
}

interface Covenant {
    type: CovenantType;
    definition: {
        metric: string;
        calculation: string;
        threshold: number;
        operator: ComparisonOperator;
    };
    
    testing: {
        frequency: Frequency;
        testDates: Date[];
        reportingDeadline: number;        // Days after period end
        curePeriod: number;               // Days to cure breach
    };
    
    remedies: {
        breachConsequences: BreachConsequence[];
        cureConditions: CureCondition[];
    };
}

interface FinancialCovenant extends Covenant {
    calculation: {
        numerator: CalculationComponent[];
        denominator?: CalculationComponent[];
        adjustments: Adjustment[];
    };
}

interface InformationalCovenant extends Covenant {
    reportingRequirements: {
        content: string[];
        format: string;
        certificationRequired: boolean;
    };
}
```

## 6. Guarantee and Collateral Management

```typescript
interface CollateralManager {
    // Collateral tracking
    collateral: {
        registerCollateral: (collateral: Collateral) => CollateralRecord;
        updateValuation: (collateralId: string, valuation: Valuation) => ValuationUpdate;
        trackEncumbrance: (collateralId: string) => EncumbranceStatus;
    };
    
    // LTV monitoring
    ltvMonitoring: {
        calculateLTV: (loan: Loan, collateral: Collateral[]) => LTVResult;
        monitorThresholds: (ltvResult: LTVResult) => ThresholdStatus;
    };
    
    // Margin calls
    marginCalls: {
        calculateRequired: (shortfall: number) => MarginCallAmount;
        trackMarginCalls: (marginCall: MarginCall) => MarginCallStatus;
    };
}

interface GuaranteeManager {
    // Guarantee tracking
    guarantees: {
        registerGuarantee: (guarantee: Guarantee) => GuaranteeRecord;
        updateStatus: (guaranteeId: string, status: GuaranteeStatus) => StatusUpdate;
        trackExposure: (guaranteeId: string) => ExposureStatus;
    };
    
    // Guarantee valuation
    valuation: {
        calculateValue: (guarantee: Guarantee) => GuaranteeValue;
        assessStrength: (guarantor: Entity) => GuarantorAssessment;
    };
}

interface Collateral {
    type: CollateralType;
    description: string;
    owner: Entity;
    
    // Valuation
    valuation: {
        amount: number;
        currency: string;
        date: Date;
        method: ValuationMethod;
        provider: string;
    };
    
    // Legal
    legal: {
        jurisdiction: string;
        documentationType: string;
        perfection: PerfectionStatus;
        registrations: Registration[];
    };
    
    // Monitoring
    monitoring: {
        revaluationFrequency: Frequency;
        lastReviewDate: Date;
        nextReviewDate: Date;
    };
}
```

## 7. Payment Waterfall and Subordination

```typescript
interface WaterfallManager {
    // Waterfall definition
    waterfall: {
        levels: WaterfallLevel[];
        conditions: WaterfallCondition[];
        triggers: WaterfallTrigger[];
    };
    
    // Payment processing
    processPayment: (
        payment: Payment,
        waterfall: Waterfall
    ) => PaymentAllocation[];
    
    // Subordination
    subordination: {
        levels: SubordinationLevel[];
        restrictions: SubordinationRestriction[];
    };
}

interface WaterfallLevel {
    priority: number;
    type: PaymentType;
    
    allocation: {
        method: AllocationMethod;
        ratios?: number[];
        conditions?: AllocationCondition[];
    };
    
    restrictions: {
        minimumAmount?: number;
        maximumAmount?: number;
        currency?: string[];
    };
}

interface SubordinationLevel {
    rank: number;
    claims: ClaimType[];
    
    constraints: {
        paymentRestrictions: PaymentRestriction[];
        modificationRestrictions: ModificationRestriction[];
    };
    
    protections: {
        turnoverProvisions: TurnoverProvision[];
        buyoutRights: BuyoutRight[];
    };
}

interface PaymentProcessor {
    // Payment application
    applyPayment: (
        payment: Payment,
        waterfall: Waterfall,
        subordination: SubordinationLevel[]
    ) => PaymentResult;
    
    // Payment redistribution
    redistributePayment: (
        payment: Payment,
        trigger: WaterfallTrigger
    ) => PaymentAllocation[];
}
```

Would you like me to:
1. Add more specific calculation methods for any of these components?
2. Expand the event handling and state management aspects?
3. Detail the integration points with risk and accounting systems?
4. Add more comprehensive validation and error handling?
5. Develop monitoring and reporting specifications?
6. Add specifications for regulatory compliance tracking?
7. Elaborate on the cross-feature interactions and dependencies?

The framework above covers the main structural elements, but there are many intricate details and edge cases within each component that we could specify further. Let me know which aspects need more detailed elaboration.