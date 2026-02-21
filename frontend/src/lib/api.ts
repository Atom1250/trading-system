const IS_SERVER = typeof window === 'undefined';
const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const INTERNAL_API_URL = process.env.INTERNAL_API_URL || PUBLIC_API_URL;

const API_URL = IS_SERVER ? INTERNAL_API_URL : PUBLIC_API_URL;

export async function fetchDashboardStats() {
    const res = await fetch(`${API_URL}/dashboard/stats`, {
        cache: 'no-store',
    });
    if (!res.ok) {
        throw new Error('Failed to fetch dashboard stats');
    }
    return res.json();
}

export async function fetchRecentActivity() {
    const res = await fetch(`${API_URL}/dashboard/activity`, {
        cache: 'no-store',
    });
    if (!res.ok) {
        throw new Error('Failed to fetch recent activity');
    }
    return res.json();
}

export async function runBacktest(payload: any) {
    const res = await fetch(`${API_URL}/backtest/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        cache: 'no-store',
    });

    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to run backtest');
    }
    return res.json();
}

export async function fetchBacktestHistory() {
    const res = await fetch(`${API_URL}/backtest/history`, {
        cache: 'no-store',
    });
    if (!res.ok) {
        throw new Error('Failed to fetch backtest history');
    }
    return res.json();
}

export async function runOptimization(payload: any) {
    const res = await fetch(`${API_URL}/optimize/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        cache: 'no-store',
    });

    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to run optimization');
    }
    return res.json();
}

export async function fetchMLModels() {
    const res = await fetch(`${API_URL}/ml/models`, {
        cache: 'no-store',
    });
    if (!res.ok) {
        throw new Error('Failed to fetch ML models');
    }
    return res.json();
}

export async function fetchFeatureImportance(modelName: string) {
    const res = await fetch(`${API_URL}/ml/feature-importance/${modelName}`, {
        cache: 'no-store',
    });
    if (!res.ok) {
        throw new Error('Failed to fetch feature importance');
    }
    return res.json();
}

// Portfolio & Journal Fetchers
export async function fetchPortfolioState(runId: string) {
    const res = await fetch(`${API_URL}/portfolio/state?run_id=${runId}`, {
        cache: 'no-store',
    });
    if (!res.ok) throw new Error('Failed to fetch portfolio state');
    return res.json();
}

export async function fetchPortfolioTrades(runId: string) {
    const res = await fetch(`${API_URL}/portfolio/trades?run_id=${runId}`, {
        cache: 'no-store',
    });
    if (!res.ok) throw new Error('Failed to fetch portfolio trades');
    return res.json();
}

export async function fetchPortfolioMetrics(runId: string) {
    const res = await fetch(`${API_URL}/portfolio/metrics?run_id=${runId}`, {
        cache: 'no-store',
    });
    if (!res.ok) throw new Error('Failed to fetch portfolio metrics');
    return res.json();
}

export async function fetchTradeNotes(tradeId: string) {
    const res = await fetch(`${API_URL}/portfolio/journal/${tradeId}`, {
        cache: 'no-store',
    });
    if (!res.ok) throw new Error('Failed to fetch trade notes');
    return res.json();
}

export async function createTradeNote(payload: { trade_id: string; content: string; author?: string }) {
    const res = await fetch(`${API_URL}/portfolio/journal`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        cache: 'no-store',
    });
    if (!res.ok) throw new Error('Failed to create trade note');
    return res.json();
}

export async function fetchPortfolioAllocations(runId: string) {
    const res = await fetch(`${API_URL}/portfolio/allocations?run_id=${runId}`, {
        cache: 'no-store',
    });
    if (!res.ok) throw new Error('Failed to fetch portfolio allocations');
    return res.json();
}

