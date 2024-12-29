# Multi-Curve Framework for Floating Rate Analytics

## 1. Curve Data Structures

```typescript
interface RateCurve {
    curveId: string;
    asOfDate: Date;
    currency: string;
    indexName?: string;        // e.g., 'LIBOR', 'SOFR', 'EURIBOR'
    indexTenor?: string;       // e.g., '3M', '6M'
    curveType: CurveType;     // Discount, Forward, Spread
    
    // Curve points
    tenors: string[];         // e.g., '1D', '1W', '1M', '3M', etc.
    rates: number[];          // Zero rates or forward rates
    dayCountConvention: DayCount;
    interpolationMethod: InterpolationMethod;
    
    // Curve construction metadata
    instruments: CurveInstrument[];
    buildTime: Date;
    qualityMetrics: CurveQualityMetrics;
}

enum CurveType {
    DiscountCurve,
    ForwardCurve,
    SpreadCurve
}

interface CurveInstrument {
    instrumentType: string;    // Deposit, FRA, Future, Swap
    maturity: string;
    rate: number;
    weight: number;           // Used in curve calibration
}

interface CurveQualityMetrics {
    maxFittingError: number;
    averageFittingError: number;
    smoothnessMetric: number;
}

interface CurveSet {
    baseDate: Date;
    currency: string;
    discountCurve: RateCurve;
    forwardCurves: Map<string, RateCurve>;  // Indexed by tenor
    spreadCurves: Map<string, RateCurve>;   // Credit spread curves
}
```

## 2. Floating Rate Analytics Engine

```typescript
interface FloatingRateAnalytics {
    // Forward Rate Calculation
    calculateForwardRate: (
        indexCurve: RateCurve,
        startDate: Date,
        endDate: Date,
        dayCount: DayCount
    ) => number;
    
    // Projected Cashflows
    projectFloatingCashflows: (
        loan: SyndicatedLoan | TimeDeposit,
        curveSet: CurveSet,
        asOfDate: Date
    ) => ProjectedCashflow[];
    
    // Present Value Calculations
    calculatePresentValue: (
        cashflows: ProjectedCashflow[],
        curveSet: CurveSet,
        asOfDate: Date
    ) => PresentValueResult;
    
    // Risk Metrics
    calculateDV01: (
        loan: SyndicatedLoan | TimeDeposit,
        curveSet: CurveSet,
        bumpSize?: number
    ) => DV01Result;
    
    calculateCrossCurveDelta: (
        loan: SyndicatedLoan | TimeDeposit,
        curveSet: CurveSet,
        bumpSize?: number
    ) => CrossCurveDeltaResult;
}

interface ProjectedCashflow {
    paymentDate: Date;
    accrualStartDate: Date;
    accrualEndDate: Date;
    
    principal?: number;
    projectedRate?: number;    // For floating payments
    fixedRate?: number;        // For fixed payments
    projectedAmount: number;
    
    // Calculation components
    indexRate?: number;
    spread?: number;
    dayCountFraction: number;
}

interface PresentValueResult {
    totalPV: number;
    pvByComponent: {
        fixedPV: number;
        floatingPV: number;
        principalPV: number;
    };
    effectiveRate: number;    // Internal rate of return
    cleanPrice: number;       // PV excluding accrued interest
    dirtyPrice: number;       // PV including accrued interest
}

interface DV01Result {
    total: number;
    byTenor: Map<string, number>;
    byComponent: {
        discounting: number;
        forwarding: number;
    };
}

interface CrossCurveDeltaResult {
    deltaMatrix: Map<string, Map<string, number>>;  // Impact of each curve on each cash flow
    correlatedValue: number;                        // Value considering curve correlations
}
```

## 3. Implementation Details

```typescript
class FloatingRateAnalyticsImpl implements FloatingRateAnalytics {
    calculateForwardRate(
        indexCurve: RateCurve,
        startDate: Date,
        endDate: Date,
        dayCount: DayCount
    ): number {
        const t1 = this.yearFraction(indexCurve.baseDate, startDate, dayCount);
        const t2 = this.yearFraction(indexCurve.baseDate, endDate, dayCount);
        
        const r1 = this.interpolateRate(indexCurve, t1);
        const r2 = this.interpolateRate(indexCurve, t2);
        
        // Convert zero rates to forward rate
        const dcf = this.yearFraction(startDate, endDate, dayCount);
        return ((1 + r2 * t2) / (1 + r1 * t1) - 1) / dcf;
    }

    projectFloatingCashflows(
        loan: SyndicatedLoan | TimeDeposit,
        curveSet: CurveSet,
        asOfDate: Date
    ): ProjectedCashflow[] {
        const cashflows: ProjectedCashflow[] = [];
        const schedule = this.generateSchedule(loan);
        
        for (const period of schedule) {
            const indexCurve = curveSet.forwardCurves.get(loan.interestRate.referenceRate);
            const projectedRate = this.calculateForwardRate(
                indexCurve,
                period.startDate,
                period.endDate,
                loan.dayCountConvention
            );
            
            const dcf = this.yearFraction(
                period.startDate,
                period.endDate,
                loan.dayCountConvention
            );
            
            const projectedAmount = loan.principalAmount * 
                                  (projectedRate + loan.interestRate.spread) * 
                                  dcf;
            
            cashflows.push({
                paymentDate: period.paymentDate,
                accrualStartDate: period.startDate,
                accrualEndDate: period.endDate,
                projectedRate,
                projectedAmount,
                indexRate: projectedRate,
                spread: loan.interestRate.spread,
                dayCountFraction: dcf
            });
        }
        
        return cashflows;
    }

    calculatePresentValue(
        cashflows: ProjectedCashflow[],
        curveSet: CurveSet,
        asOfDate: Date
    ): PresentValueResult {
        let totalPV = 0;
        let fixedPV = 0;
        let floatingPV = 0;
        let principalPV = 0;
        
        for (const cf of cashflows) {
            const df = this.getDiscountFactor(
                curveSet.discountCurve,
                asOfDate,
                cf.paymentDate
            );
            
            const pv = cf.projectedAmount * df;
            totalPV += pv;
            
            if (cf.fixedRate) fixedPV += pv;
            else if (cf.projectedRate) floatingPV += pv;
            if (cf.principal) principalPV += cf.principal * df;
        }
        
        return {
            totalPV,
            pvByComponent: {
                fixedPV,
                floatingPV,
                principalPV
            },
            effectiveRate: this.calculateEffectiveRate(cashflows, totalPV),
            cleanPrice: totalPV - this.calculateAccruedInterest(cashflows, asOfDate),
            dirtyPrice: totalPV
        };
    }
}
```

## 4. Curve Bootstrapping and Maintenance

```typescript
interface CurveBuilder {
    // Curve Construction
    buildDiscountCurve: (
        instruments: CurveInstrument[],
        settings: CurveSettings
    ) => RateCurve;
    
    buildForwardCurve: (
        instruments: CurveInstrument[],
        discountCurve: RateCurve,
        settings: CurveSettings
    ) => RateCurve;
    
    // Curve Maintenance
    updateCurve: (
        existingCurve: RateCurve,
        newInstruments: CurveInstrument[]
    ) => RateCurve;
    
    // Quality Checks
    validateCurve: (curve: RateCurve) => CurveQualityMetrics;
}
```

Would you like me to:
1. Add more details about curve bootstrapping methods?
2. Expand the risk calculations to include cross-gamma and vega for floating rates?
3. Add specific handling for fallback rates and transition periods?
4. Develop more detailed credit spread curve analytics?