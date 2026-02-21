"use client"

import { useState, useEffect } from "react"
import { Cpu, Loader2, Info, Brain, Target, BarChart3, Activity } from "lucide-react"
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell
} from 'recharts'

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { fetchMLModels, fetchFeatureImportance } from "@/lib/api"

export default function MLAnalyticsPage() {
    const [isLoading, setIsLoading] = useState(false)
    const [models, setModels] = useState<string[]>([])
    const [selectedModel, setSelectedModel] = useState<string>("")
    const [importanceData, setImportanceData] = useState<any[]>([])
    const [error, setError] = useState<string | null>(null)

    // Load available models on mount
    useEffect(() => {
        const loadModels = async () => {
            try {
                const data = await fetchMLModels()
                setModels(data.models || [])
                if (data.models && data.models.length > 0) {
                    setSelectedModel(data.models[0])
                }
            } catch (e) {
                console.error("Failed to load models:", e)
            }
        }
        loadModels()
    }, [])

    const handleLoadImportance = async () => {
        if (!selectedModel) return

        setIsLoading(true)
        setError(null)
        try {
            const data = await fetchFeatureImportance(selectedModel)
            if (data.error) {
                setError(data.error)
                setImportanceData([])
            } else {
                setImportanceData(data.feature_importances || [])
            }
        } catch (e: any) {
            setError(e.message || "Failed to load importance data")
            setImportanceData([])
        } finally {
            setIsLoading(false)
        }
    }

    // Auto-load when model changes
    useEffect(() => {
        if (selectedModel) {
            handleLoadImportance()
        }
    }, [selectedModel])

    return (
        <div className="container mx-auto p-6 space-y-8">
            <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        <Cpu className="h-8 w-8 text-primary" />
                        AI / ML Analytics
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Examine technical feature weights and model interpretability.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <Select value={selectedModel} onValueChange={setSelectedModel}>
                        <SelectTrigger className="w-[240px]">
                            <SelectValue placeholder="Select a model" />
                        </SelectTrigger>
                        <SelectContent>
                            {models.length > 0 ? (
                                models.map(m => (
                                    <SelectItem key={m} value={m}>{m}.joblib</SelectItem>
                                ))
                            ) : (
                                <SelectItem value="default" disabled>No models found</SelectItem>
                            )}
                        </SelectContent>
                    </Select>
                    <Button
                        variant="outline"
                        size="icon"
                        onClick={handleLoadImportance}
                        disabled={isLoading || !selectedModel}
                    >
                        <Loader2 className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Feature Importance Chart */}
                <Card className="lg:col-span-2">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>Feature Importances</CardTitle>
                                <CardDescription>
                                    Relative weights assigned to technical indicators during training.
                                </CardDescription>
                            </div>
                            <BarChart3 className="h-5 w-5 text-muted-foreground" />
                        </div>
                    </CardHeader>
                    <CardContent className="h-[450px]">
                        {error ? (
                            <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-destructive/5 rounded-lg border border-destructive/20">
                                <Info className="h-10 w-10 text-destructive mb-4" />
                                <h3 className="text-lg font-semibold text-destructive">Model Analytics Unavailable</h3>
                                <p className="text-sm text-muted-foreground max-w-md mt-2">
                                    {error}
                                </p>
                            </div>
                        ) : importanceData.length > 0 ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                    data={importanceData}
                                    layout="vertical"
                                    margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                                >
                                    <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#E5E7EB" />
                                    <XAxis type="number" hide />
                                    <YAxis
                                        dataKey="feature"
                                        type="category"
                                        width={100}
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <Tooltip
                                        cursor={{ fill: 'transparent' }}
                                        contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                    />
                                    <Bar
                                        dataKey="importance"
                                        fill="hsl(var(--primary))"
                                        radius={[0, 4, 4, 0]}
                                        barSize={24}
                                    >
                                        {importanceData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fillOpacity={1 - (index / (importanceData.length * 1.5))} />
                                        ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg">
                                <p>Select a trained model to visualize importance.</p>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Educational Content */}
                <div className="space-y-6">
                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Brain className="h-5 w-5 text-primary" />
                                Model Training
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-sm text-muted-foreground leading-relaxed">
                            Before running a backtest with an ML Strategy, ensure a model is trained.
                            The system uses historical OHLCV data to create features (like RSI and MACD)
                            and trains a gradient boosted tree to predict forward returns.
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Target className="h-5 w-5 text-primary" />
                                Feature Importance
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-sm text-muted-foreground leading-relaxed">
                            This chart shows which technical indicators the AI relies on most.
                            A higher score means the model heavily weights this feature when
                            deciding to Buy, Sell, or Hold.
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-3">
                            <CardTitle className="text-lg flex items-center gap-2">
                                <Activity className="h-5 w-5 text-primary" />
                                Pattern Recognition
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-sm text-muted-foreground leading-relaxed">
                            The ML engine matches current market conditions to historical regimes.
                            If the current volatility and trend match a historical 'bull flag',
                            the model's confidence score increases.
                        </CardContent>
                    </Card>

                    <div className="p-4 bg-primary/5 rounded-lg border border-primary/10">
                        <h4 className="text-xs font-bold text-primary uppercase tracking-wider mb-2">Pro Tip</h4>
                        <p className="text-xs text-muted-foreground">
                            Standardise your features before training for best linear model results. Tree-based models (XGBoost/Random Forest) handle unscaled data natively.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}
