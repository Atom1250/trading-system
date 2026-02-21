"use client"

import { useState, useEffect } from "react"
import { Server, TrendingUp, DollarSign, PieChart, Info, Loader2, Filter } from "lucide-react"
import { fetchPortfolioMetrics, fetchPortfolioState, fetchPortfolioAllocations } from "@/lib/api"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

interface MetricCardProps {
    title: string
    value: string | number
    description?: string
    status?: "positive" | "negative" | "neutral"
}

function MetricCard({ title, value, description, status }: MetricCardProps) {
    const statusColor = status === "positive" ? "text-green-500" : status === "negative" ? "text-red-500" : ""
    return (
        <Card>
            <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
            </CardHeader>
            <CardContent>
                <div className={`text-2xl font-bold ${statusColor}`}>{value}</div>
                {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
            </CardContent>
        </Card>
    )
}

export default function PortfolioPage() {
    const [isLoading, setIsLoading] = useState(true)
    const [metrics, setMetrics] = useState<any>(null)
    const [state, setState] = useState<any>(null)
    const [allocations, setAllocations] = useState<any[]>([])

    useEffect(() => {
        loadData()
    }, [])

    const loadData = async () => {
        try {
            const [m, s, a] = await Promise.all([
                fetchPortfolioMetrics(""),
                fetchPortfolioState(""),
                fetchPortfolioAllocations("")
            ])
            setMetrics(m)
            setState(s)
            setAllocations(a)
        } catch (e) {
            console.error("Failed to load portfolio data:", e)
        } finally {
            setIsLoading(false)
        }
    }

    if (isLoading) {
        return (
            <div className="h-screen flex items-center justify-center">
                <Loader2 className="h-10 w-10 animate-spin text-primary" />
            </div>
        )
    }

    return (
        <div className="container mx-auto p-6 space-y-8">
            <header>
                <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                    <Server className="h-8 w-8 text-primary" />
                    Portfolio Navigator
                </h1>
                <p className="text-muted-foreground mt-1">
                    Consolidated view of all active capital and strategy performance.
                </p>
            </header>

            {/* Top Level Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                    title="Total Equity"
                    value={`$${state?.equity?.toLocaleString() || '0'}`}
                    description="Current combined account value"
                    status="neutral"
                />
                <MetricCard
                    title="Total Return"
                    value={`${metrics?.total_return?.toFixed(2) || '0'}%`}
                    description="Performance since inception"
                    status={metrics?.total_return > 0 ? "positive" : "negative"}
                />
                <MetricCard
                    title="Sharpe Ratio"
                    value={metrics?.sharpe_ratio?.toFixed(2) || '0.00'}
                    description="Risk-adjusted return score"
                    status={metrics?.sharpe_ratio > 1.5 ? "positive" : "neutral"}
                />
                <MetricCard
                    title="Max Drawdown"
                    value={`${metrics?.max_drawdown?.toFixed(2) || '0'}%`}
                    description="Largest peak-to-trough decline"
                    status="negative"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Active Positions */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <TrendingUp className="h-5 w-5 text-primary" />
                            Live Positions
                        </CardTitle>
                        <CardDescription>Aggregation of all symbols currently held across strategies.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {Object.keys(state?.positions || {}).length === 0 ? (
                            <div className="h-48 flex items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg">
                                No active positions found.
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {Object.entries(state.positions).map(([symbol, qty]: [string, any]) => (
                                    <div key={symbol} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
                                        <div className="flex items-center gap-4">
                                            <div className="h-10 w-10 flex items-center justify-center bg-primary/10 rounded-full font-bold">
                                                {symbol[0]}
                                            </div>
                                            <div>
                                                <div className="font-bold">{symbol}</div>
                                                <div className="text-xs text-muted-foreground">{qty > 0 ? 'LONG' : 'SHORT'} ENTRY</div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="font-mono font-bold">{qty.toLocaleString()} units</div>
                                            <Badge variant="outline" className="mt-1">Active</Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Strategy Allocation */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <PieChart className="h-5 w-5 text-primary" />
                            Allocations
                        </CardTitle>
                        <CardDescription>Capital distribution by strategy.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        {allocations.length === 0 ? (
                            <p className="text-center text-sm text-muted-foreground italic">No allocation data available.</p>
                        ) : (
                            allocations.map((alloc) => (
                                <div key={alloc.strategy_id} className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span className="font-medium">{alloc.strategy_id}</span>
                                        <span className="text-muted-foreground">{alloc.trade_count} trades</span>
                                    </div>
                                    <Progress value={Math.min(100, (alloc.total_exposure / state.equity) * 100)} className="h-2" />
                                    <div className="flex justify-between text-[10px] text-muted-foreground uppercase">
                                        <span>Exposure: ${alloc.total_exposure.toLocaleString()}</span>
                                        <span>PnL: ${alloc.total_pnl.toFixed(2)}</span>
                                    </div>
                                </div>
                            ))
                        )}
                        <div className="mt-6 p-4 bg-primary/5 rounded-lg border border-primary/10">
                            <h4 className="text-xs font-bold text-primary uppercase flex items-center gap-1 mb-2">
                                <Info className="h-3 w-3" />
                                Insights
                            </h4>
                            <p className="text-xs text-muted-foreground leading-relaxed">
                                Your portfolio is currently concentrated in <strong>{Object.keys(state?.positions || {}).length}</strong> assets. Consider diversifying to lower your correlation risk.
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
