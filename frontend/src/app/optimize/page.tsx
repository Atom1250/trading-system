"use client"

import { useState } from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon, Loader2, Play, Plus, Trash2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"
import { runOptimization } from "@/lib/api"

interface ParameterRange {
    name: string
    min_value: number
    max_value: number
    type: "int" | "float"
    step?: number
}

export default function OptimizationPage() {
    const [isLoading, setIsLoading] = useState(false)
    const [result, setResult] = useState<any>(null)
    const [error, setError] = useState<string | null>(null)

    // Form State
    const [strategy, setStrategy] = useState("MovingAverageCrossover")
    const [symbol, setSymbol] = useState("AAPL")
    const [startDate, setStartDate] = useState<Date>(new Date(2023, 0, 1))
    const [endDate, setEndDate] = useState<Date>(new Date(2023, 11, 31))
    const [initialCapital, setInitialCapital] = useState("100000")
    const [nTrials, setNTrials] = useState("20")

    // Parameter Ranges State
    const [ranges, setRanges] = useState<ParameterRange[]>([
        { name: "short_window", min_value: 10, max_value: 50, type: "int" },
        { name: "long_window", min_value: 100, max_value: 200, type: "int" }
    ])

    const addRange = () => {
        setRanges([...ranges, { name: "", min_value: 0, max_value: 0, type: "int" }])
    }

    const updateRange = (index: number, field: keyof ParameterRange, value: any) => {
        const newRanges = [...ranges]
        newRanges[index] = { ...newRanges[index], [field]: value }
        setRanges(newRanges)
    }

    const removeRange = (index: number) => {
        setRanges(ranges.filter((_, i) => i !== index))
    }

    const handleRunOptimization = async () => {
        setIsLoading(true)
        setError(null)
        setResult(null)

        try {
            // Validate ranges
            const validRanges = ranges.filter(r => r.name && r.min_value < r.max_value)
            if (validRanges.length === 0) {
                throw new Error("Please define at least one valid parameter range (min < max)")
            }

            const payload = {
                strategy_name: strategy,
                symbol: symbol,
                start_date: format(startDate, "yyyy-MM-dd"),
                end_date: format(endDate, "yyyy-MM-dd"),
                initial_capital: parseFloat(initialCapital),
                n_trials: parseInt(nTrials),
                parameter_ranges: validRanges,
                fixed_parameters: {} // Can add UI for this later
            }

            const data = await runOptimization(payload)
            setResult(data)
        } catch (e: any) {
            setError(e.message || "An unexpected error occurred")
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="container mx-auto p-6 space-y-8">
            <header>
                <h1 className="text-3xl font-bold tracking-tight">Optimization Lab</h1>
                <p className="text-muted-foreground">
                    Find optimal parameters for your strategies using Optuna.
                </p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Configuration Panel */}
                <Card className="lg:col-span-1 h-fit">
                    <CardHeader>
                        <CardTitle>Configuration</CardTitle>
                        <CardDescription>Set up optimization search space.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">

                        <div className="space-y-2">
                            <Label>Strategy</Label>
                            <Select value={strategy} onValueChange={setStrategy}>
                                <SelectTrigger>
                                    <SelectValue placeholder="Select strategy" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="MovingAverageCrossover">Moving Average Crossover</SelectItem>
                                    <SelectItem value="RSIMeanReversion">RSI Mean Reversion</SelectItem>
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

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label>Initial Capital ($)</Label>
                                <Input
                                    type="number"
                                    value={initialCapital}
                                    onChange={(e) => setInitialCapital(e.target.value)}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label>Num Trials</Label>
                                <Input
                                    type="number"
                                    value={nTrials}
                                    onChange={(e) => setNTrials(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label>Parameter Ranges</Label>
                                <Button variant="ghost" size="sm" onClick={addRange}>
                                    <Plus className="h-4 w-4 mr-1" /> Add
                                </Button>
                            </div>

                            <div className="space-y-3">
                                {ranges.map((range, idx) => (
                                    <div key={idx} className="flex flex-col gap-2 p-3 border rounded-md relative bg-muted/20">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="absolute right-1 top-1 h-6 w-6 text-destructive hover:bg-destructive/10"
                                            onClick={() => removeRange(idx)}
                                        >
                                            <Trash2 className="h-3 w-3" />
                                        </Button>
                                        <Input
                                            placeholder="Param Name"
                                            value={range.name}
                                            onChange={(e) => updateRange(idx, "name", e.target.value)}
                                            className="h-8 text-sm"
                                        />
                                        <div className="grid grid-cols-3 gap-2">
                                            <Input
                                                type="number"
                                                placeholder="Min"
                                                value={range.min_value}
                                                onChange={(e) => updateRange(idx, "min_value", parseFloat(e.target.value))}
                                                className="h-8 text-xs"
                                            />
                                            <Input
                                                type="number"
                                                placeholder="Max"
                                                value={range.max_value}
                                                onChange={(e) => updateRange(idx, "max_value", parseFloat(e.target.value))}
                                                className="h-8 text-xs"
                                            />
                                            <Select
                                                value={range.type}
                                                onValueChange={(val) => updateRange(idx, "type", val)}
                                            >
                                                <SelectTrigger className="h-8 text-xs">
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    <SelectItem value="int">Int</SelectItem>
                                                    <SelectItem value="float">Float</SelectItem>
                                                </SelectContent>
                                            </Select>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <Button className="w-full" onClick={handleRunOptimization} disabled={isLoading}>
                            {isLoading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Running Optimization...
                                </>
                            ) : (
                                <>
                                    <Play className="mr-2 h-4 w-4" />
                                    Run Optimization
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
                    {!result ? (
                        <div className="flex h-full items-center justify-center border-2 border-dashed rounded-lg p-12 text-muted-foreground">
                            Run optimization to find best parameters.
                        </div>
                    ) : (
                        <Card className="bg-gradient-to-br from-background to-muted/50">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    Optimization Results
                                    <span className="text-xs font-normal px-2 py-1 rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
                                        Completed
                                    </span>
                                </CardTitle>
                                <CardDescription>
                                    Best parameters found for {result.strategy_name} on {result.symbol}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm">
                                        <h3 className="text-sm font-medium text-muted-foreground mb-2">Best Objective Value</h3>
                                        <div className="text-3xl font-bold">
                                            {result.best_value !== 0 ? result.best_value.toFixed(4) : "N/A"}
                                        </div>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            (Sharpe Ratio or configured objective)
                                        </p>
                                    </div>
                                    <div className="p-4 rounded-lg border bg-card text-card-foreground shadow-sm">
                                        <h3 className="text-sm font-medium text-muted-foreground mb-2">Optimization ID</h3>
                                        <div className="text-sm font-mono break-all text-muted-foreground">
                                            {result.optimization_id}
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-lg font-semibold mb-4">Best Parameters</h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                        {Object.entries(result.best_params).map(([key, value]) => (
                                            <div key={key} className="flex flex-col p-3 bg-muted/30 rounded-md border">
                                                <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{key}</span>
                                                <span className="text-xl font-mono mt-1">{String(value)}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    )
}
