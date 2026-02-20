"use client"

import { useEffect, useState } from "react"
import { format } from "date-fns"
import { BarChart2, Loader2, ArrowLeft } from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { fetchBacktestHistory } from "@/lib/api"
import { cn } from "@/lib/utils"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';

interface BacktestResult {
    id: string
    timestamp: string
    strategy: string
    symbol: string
    metrics: {
        total_return: number
        cagr: number
        sharpe_ratio: number
        max_drawdown: number
        win_rate: number
        total_trades: number
    }
}

export default function ComparePage() {
    const [history, setHistory] = useState<BacktestResult[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

    useEffect(() => {
        async function load() {
            try {
                const data = await fetchBacktestHistory()
                // Sort by newest first
                setHistory(data.sort((a: any, b: any) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()))
            } catch (e) {
                console.error("Failed to load history", e)
            } finally {
                setIsLoading(false)
            }
        }
        load()
    }, [])

    const toggleSelection = (id: string) => {
        const next = new Set(selectedIds)
        if (next.has(id)) {
            next.delete(id)
        } else {
            next.add(id)
        }
        setSelectedIds(next)
    }

    const selectedResults = history.filter(h => selectedIds.has(h.id))

    // Prepare chart data
    const chartData = selectedResults.map(r => ({
        name: `${r.strategy} (${r.symbol})`,
        "Total Return %": r.metrics.total_return,
        "Max Drawdown %": r.metrics.max_drawdown,
        "Sharpe Ratio": r.metrics.sharpe_ratio
    }))

    return (
        <div className="container mx-auto p-6 space-y-8">
            <header className="flex items-center space-x-4">
                <Link href="/">
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Results Comparison</h1>
                    <p className="text-muted-foreground">
                        Select backtests to compare performance metrics side-by-side.
                    </p>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Selection List */}
                <Card className="lg:col-span-1 h-[calc(100vh-200px)] flex flex-col">
                    <CardHeader>
                        <CardTitle>History</CardTitle>
                        <CardDescription>Select items to compare</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1 overflow-auto p-0">
                        {isLoading ? (
                            <div className="flex justify-center p-8">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : history.length === 0 ? (
                            <div className="text-center p-8 text-muted-foreground">
                                No backtest history found. Run a backtest first.
                            </div>
                        ) : (
                            <div className="divide-y">
                                {history.map((item) => (
                                    <div
                                        key={item.id}
                                        className={cn(
                                            "flex items-start space-x-3 p-4 cursor-pointer hover:bg-muted/50 transition-colors",
                                            selectedIds.has(item.id) && "bg-muted"
                                        )}
                                        onClick={() => toggleSelection(item.id)}
                                    >
                                        <Checkbox
                                            checked={selectedIds.has(item.id)}
                                            // onClick handled by parent div
                                            onCheckedChange={() => { }}
                                        />
                                        <div className="space-y-1">
                                            <p className="font-medium leading-none">{item.strategy}</p>
                                            <p className="text-sm text-muted-foreground">{item.symbol} • {format(new Date(item.timestamp), "MMM d, HH:mm")}</p>
                                            <div className="flex gap-2 text-xs mt-1">
                                                <span className={cn(item.metrics.total_return >= 0 ? "text-green-600" : "text-red-600")}>
                                                    {item.metrics.total_return.toFixed(2)}% Ret
                                                </span>
                                                <span className="text-muted-foreground">
                                                    SR: {item.metrics.sharpe_ratio.toFixed(2)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Comparison View */}
                <div className="lg:col-span-2 space-y-6">
                    {selectedResults.length === 0 ? (
                        <div className="flex h-full items-center justify-center border-2 border-dashed rounded-lg p-12 text-muted-foreground opacity-50">
                            <div className="text-center">
                                <BarChart2 className="h-12 w-12 mx-auto mb-4" />
                                <p>Select at least one backtest from the list to view details.</p>
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* Metrics Comparison Table */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>Metrics Overview</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm text-left">
                                            <thead className="text-muted-foreground font-medium border-b">
                                                <tr>
                                                    <th className="py-2 px-4">Metric</th>
                                                    {selectedResults.map(r => (
                                                        <th key={r.id} className="py-2 px-4 whitespace-nowrap">
                                                            {r.strategy} <span className="text-xs font-normal">({r.symbol})</span>
                                                            <div className="text-xs font-normal opacity-70">{format(new Date(r.timestamp), "HH:mm")}</div>
                                                        </th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y">
                                                <tr>
                                                    <td className="py-3 px-4 font-medium">Total Return</td>
                                                    {selectedResults.map(r => (
                                                        <td key={r.id} className={cn("py-3 px-4", r.metrics.total_return >= 0 ? "text-green-600" : "text-red-600")}>
                                                            {r.metrics.total_return.toFixed(2)}%
                                                        </td>
                                                    ))}
                                                </tr>
                                                <tr>
                                                    <td className="py-3 px-4 font-medium">Sharpe Ratio</td>
                                                    {selectedResults.map(r => (
                                                        <td key={r.id} className="py-3 px-4">
                                                            {r.metrics.sharpe_ratio.toFixed(2)}
                                                        </td>
                                                    ))}
                                                </tr>
                                                <tr>
                                                    <td className="py-3 px-4 font-medium">Max Drawdown</td>
                                                    {selectedResults.map(r => (
                                                        <td key={r.id} className="py-3 px-4 text-red-600">
                                                            {r.metrics.max_drawdown.toFixed(2)}%
                                                        </td>
                                                    ))}
                                                </tr>
                                                <tr>
                                                    <td className="py-3 px-4 font-medium">Win Rate</td>
                                                    {selectedResults.map(r => (
                                                        <td key={r.id} className="py-3 px-4">
                                                            {r.metrics.win_rate.toFixed(1)}%
                                                        </td>
                                                    ))}
                                                </tr>
                                                <tr>
                                                    <td className="py-3 px-4 font-medium">Trades</td>
                                                    {selectedResults.map(r => (
                                                        <td key={r.id} className="py-3 px-4">
                                                            {r.metrics.total_trades}
                                                        </td>
                                                    ))}
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Chart Comparison */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>Performance Comparison</CardTitle>
                                </CardHeader>
                                <CardContent className="h-[400px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                            <XAxis dataKey="name" />
                                            <YAxis />
                                            <Tooltip
                                                cursor={{ fill: 'transparent' }}
                                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                            />
                                            <Legend />
                                            <Bar dataKey="Total Return %" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} />
                                            <Bar dataKey="Max Drawdown %" fill="hsl(var(--destructive))" radius={[4, 4, 0, 0]} />
                                        </BarChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>
                        </>
                    )}
                </div>

            </div>
        </div>
    )
}
