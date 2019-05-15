/**
 * Those classes here are just simple wrappers used for the performance evaluation.
 */

export interface SimpleStatistics {
    getCallCount(): number;
}

export class SimulatedSimpleStatistics implements SimpleStatistics {
    getCallCount(): number {
        return 0;
    }
}

export const DeviationBoundary = 0.05;

export interface ComparableStatistics {

    hasCriticalResponseTime(): boolean;

    getMaxNegativeDeviation(): number;

    isDeviationWithinBoundary(boundary: number): boolean
}

export class SimulatedComparison implements ComparableStatistics {
    // source: this.sourceEndpoint,
    // target: this.targetEndpoint,
    // stats: {
    //     critical: this.stats.hasCriticalResponseTime(),
    //     maxDeviation: this.stats.getMaxNegativeDeviation()
    // }

    critical: boolean;
    maxDeviation: number;

    constructor(critical: boolean, maxDeviation: number) {
        this.critical = critical;
        this.maxDeviation = maxDeviation;
    }

    getMaxNegativeDeviation(): number {
        return this.maxDeviation;
    }

    hasCriticalResponseTime(): boolean {
        return this.critical;
    }

    isDeviationWithinBoundary(boundary: number): boolean {
        let maxDeviation = this.getMaxNegativeDeviation();
        let buffer = boundary * DeviationBoundary;

        return boundary - buffer <= maxDeviation && maxDeviation <= boundary + buffer;
    }
}