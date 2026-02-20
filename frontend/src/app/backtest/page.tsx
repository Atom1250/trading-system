"use client"

import { useState } from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, Loader2, Play } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { runBacktest } from "@/lib/api"
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';

export default function BacktestPage() {
    const [isLoading, setIsLoading] = useState(false)
    const [results, setResults] = useState<any>(null)
    const [error, setError] = useState<string | null>(null)

    // Form State
    const [strategy, setStrategy] = useState("MovingAverageCrossover")
    const [symbol, setSymbol] = useState("AAPL")
    const [startDate, setStartDate] = useState<Date>(new Date(2023, 0, 1))
    const [endDate, setEndDate] = useState<Date>(new Date(2023, 11, 31))
    const [initialCapital, setInitialCapital] = useState("100000")
    const [parameters, setParameters] = useState('{\n  "short_window": 50,\n  "long_window": 200\n}')

    const handleStrategyChange = (val: string) => {
        setStrategy(val)
        if (val === "MovingAverageCrossover") {
            setParameters('{\n  "short_window": 50,\n  "long_window": 200\n}')
        } else if (val === "RSIMeanReversion") {
            setParameters('{\n  "period": 14,\n  "lower_threshold": 30,\n  "upper_threshold": 70\n}')
        } else if (val === "TrendPullback") {
            setParameters('{\n  "ema_period": 50,\n  "rsi_period": 14,\n  "rsi_threshold": 40\n}')
        }
    }

    const handleRunBacktest = async () => {
        setIsLoading(true)
        setError(null)
        setResults(null)

        try {
            let parsedParams = {}
            try {
                parsedParams = JSON.parse(parameters)
            } catch (e) {
                throw new Error("Invalid JSON parameters")
            }

            const payload = {
                strategy_name: strategy,
                symbol: symbol,
                start_date: format(startDate, "yyyy-MM-dd"),
                end_date: format(endDate, "yyyy-MM-dd"),
                initial_capital: parseFloat(initialCapital),
                parameters: parsedParams
            }

            const data = await runBacktest(payload)
            setResults(data)
        } catch (e: any) {
            setError(e.message || "An unexpected error occurred")
        } finally {
            setIsLoading(false)
        }
    }

    // Helper to format currency
    const formatCurrency = (value: number) =>
        new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);

    // Helper for metrics display
    const MetricCard = ({ title, value, subtext }: { title: string, value: string, subtext?: string }) => (
        <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <div className="text-2xl font-bold">{value}</div>
            {subtext && <p className="text-xs text-muted-foreground">{subtext}</p>}
        </div>
    )

    return (
        <div className="container mx-auto p-6 space-y-8">
            <header>
                <h1 className="text-3xl font-bold tracking-tight">Backtest Runner</h1>
                <p className="text-muted-foreground">
                    Configure and execute strategies against historical market data.
                </p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Configuration Panel */}
                <Card className="lg:col-span-1 h-fit">
                    <CardHeader>
                        <CardTitle>Configuration</CardTitle>
                        <CardDescription>Set up your backtest parameters.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">

                        <div className="space-y-2">
                            <Label>Strategy</Label>
                            <Select value={strategy} onValueChange={handleStrategyChange}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select strategy" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="MovingAverageCrossover">Moving Average Crossover</SelectItem>
                                    <SelectItem value="RSIMeanReversion">RSI Mean Reversion</SelectItem>
                                    <SelectItem value="TrendPullback">Trend Pullback</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="space-y-2">
                            <Label>Symbol</Label>
                            <Input
                                value={symbol}
                                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                                placeholder="e.g. AAPL"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Start Date</Label>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button
                                            variant={"outline"}
                                            className={cn(
                                                "w-full justify-start text-left font-normal",
                                                !startDate && "text-muted-foreground"
                                            )}
                                        >
                                            <CalendarIcon className="mr-2 h-4 w-4" />
                                            {startDate ? format(startDate, "PPP") : <span>Pick a date</span>}
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-auto p-0">
                                        <Calendar
                                            mode="single"
                                            selected={startDate}
                                            onSelect={(date) => date && setStartDate(date)}
                                            initialFocus
                                        />
                                    </PopoverContent>
                                </Popover>
                            </div>

                            <div className="space-y-2">
                                <Label>End Date</Label>
                                <Popover>
                                    <PopoverTrigger asChild>
                                        <Button
                                            variant={"outline"}
                                            className={cn(
                                                "w-full justify-start text-left font-normal",
                                                !endDate && "text-muted-foreground"
                                            )}
                                        >
                                            <CalendarIcon className="mr-2 h-4 w-4" />
                                            {endDate ? format(endDate, "PPP") : <span>Pick a date</span>}
                                        </Button>
                                    </PopoverTrigger>
                                    <PopoverContent className="w-auto p-0">
                                        <Calendar
                                            mode="single"
                                            selected={endDate}
                                            onSelect={(date) => date && setEndDate(date)}
                                            initialFocus
                                        />
                                    </PopoverContent>
                                </Popover>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label>Initial Capital ($)</Label>
                            <Input
                                type="number"
                                value={initialCapital}
                                onChange={(e) => setInitialCapital(e.target.value)}
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>Parameters (JSON)</Label>
                            <textarea
                                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                value={parameters}
                                onChange={(e) => setParameters(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">Refine specific strategy settings.</p>
                        </div>

                        <Button className="w-full" onClick={handleRunBacktest} disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Running Simulation...
                                </>
                            ) : (
                                <>
                                    <Play className="mr-2 h-4 w-4" />
                                    Run Backtest
                                </>
                            )}
                        </Button>

                        {error && (
                            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
                                Error: {error}
                            </div>
                        )}

                    </CardContent>
                </Card>

                {/* Results Panel */}
                <div className="lg:col-span-2 space-y-6">
                    {!results ? (
                        <div className="flex h-full items-center justify-center border-2 border-dashed rounded-lg p-12 text-muted-foreground">
                            Run a backtest to see results here.
                        </div>
                    ) : (
                        <>
                            {/* Metrics Grid */}
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <Card>
                                    <CardContent className="pt-6">
                                        <MetricCard
                                            title="Total Return"
                                            value={`${results.metrics.total_return.toFixed(2)}%`}
                                            subtext={`CAGR: ${results.metrics.cagr.toFixed(2)}%`}
                                        />
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent className="pt-6">
                                        <MetricCard
                                            title="Sharpe Ratio"
                                            value={results.metrics.sharpe_ratio.toFixed(2)}
                                        />
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent className="pt-6">
                                        <MetricCard
                                            title="Max Drawdown"
                                            value={`${results.metrics.max_drawdown.toFixed(2)}%`}
                                        />
                                    </CardContent>
                                </Card>
                                <Card>
                                    <CardContent className="pt-6">
                                        <MetricCard
                                            title="Win Rate"
                                            value={`${results.metrics.win_rate.toFixed(1)}%`}
                                            subtext={`${results.metrics.total_trades} Trades`}
                                        />
                                    </CardContent>
                                </Card>
                            </div>

                            {/* Equity Curve Chart */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>Equity Curve</CardTitle>
                                </CardHeader>
                                <CardContent className="h-[400px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={results.equity_curve}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                                            <XAxis
                                                dataKey="timestamp"
                                                tickFormatter={(str) => format(new Date(str), 'MMM dd')}
                                                minTickGap={30}
                                                stroke="#9CA3AF"
                                                fontSize={12}
                                            />
                                            <YAxis
                                                domain={['auto', 'auto']}
                                                tickFormatter={(val) => `$${val.toLocaleString()}`}
                                                stroke="#9CA3AF"
                                                fontSize={12}
                                            />
                                            <Tooltip
                                                labelFormatter={(str) => format(new Date(str), 'PPP')}
                                                formatter={(val: any) => [formatCurrency(val), "Equity"]}
                                                contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="equity"
                                                stroke="hsl(var(--primary))"
                                                strokeWidth={2}
                                                dot={false}
                                                activeDot={{ r: 6 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </CardContent>
                            </Card>

                            {/* Trade Log (Preview) */}
                            <Card>
                                <CardHeader>
                                    <CardTitle>Recent Trades</CardTitle>
                                    <CardDescription>Displaying last 5 trades</CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <div className="relative w-full overflow-auto">
                                        <table className="w-full caption-bottom text-sm text-left">
                                            <thead className="[&_tr]:border-b">
                                                <tr className="border-b transition-colors">
                                                    <th className="h-10 px-2 align-middle font-medium text-muted-foreground">Date</th>
                                                    <th className="h-10 px-2 align-middle font-medium text-muted-foreground">Type</th>
                                                    <th className="h-10 px-2 align-middle font-medium text-muted-foreground">Price</th>
                                                    <th className="h-10 px-2 align-middle font-medium text-muted-foreground">Qty</th>
                                                    <th className="h-10 px-2 align-middle font-medium text-muted-foreground">PnL</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {results.trades.slice(-5).reverse().map((trade: any, i: number) => (
                                                    <tr key={i} className="border-b transition-colors hover:bg-muted/50">
                                                        <td className="p-2 align-middle">{format(new Date(trade.timestamp), 'yyyy-MM-dd')}</td>
                                                        <td className="p-2 align-middle font-medium">{trade.type}</td>
                                                        <td className="p-2 align-middle">{formatCurrency(trade.price)}</td>
                                                        <td className="p-2 align-middle">{trade.quantity.toFixed(4)}</td>
                                                        <td className={cn("p-2 align-middle", trade.pnl > 0 ? "text-green-600" : trade.pnl < 0 ? "text-red-600" : "")}>
                                                            {formatCurrency(trade.pnl)}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </CardContent>
                            </Card>

                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
