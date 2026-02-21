"use client"

import { useState, useEffect } from "react"
import { BookOpen, MessageSquare, Plus, Search, Calendar, Tag, ChevronDown, ChevronUp, Loader2 } from "lucide-react"
import { format } from "date-fns"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { fetchPortfolioTrades, fetchTradeNotes, createTradeNote } from "@/lib/api"

interface Trade {
    id: string
    symbol: string
    side: string
    qty: number
    price: number
    timestamp: string
    strategy_id: string
    run_id: string
}

interface Note {
    id: string
    content: string
    author: string
    created_at: string
}

export default function TradeJournalPage() {
    const [trades, setTrades] = useState<Trade[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [expandedTrade, setExpandedTrade] = useState<string | null>(null)
    const [notes, setNotes] = useState<Record<string, Note[]>>({})
    const [newNote, setNewNote] = useState("")
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [searchQuery, setSearchQuery] = useState("")

    useEffect(() => {
        loadTrades()
    }, [])

    const loadTrades = async () => {
        try {
            const data = await fetchPortfolioTrades("") // Empty runId for all trades
            setTrades(data)
        } catch (e) {
            console.error("Failed to load trades:", e)
        } finally {
            setIsLoading(false)
        }
    }

    const toggleExpand = async (tradeId: string) => {
        if (expandedTrade === tradeId) {
            setExpandedTrade(null)
        } else {
            setExpandedTrade(tradeId)
            if (!notes[tradeId]) {
                try {
                    const data = await fetchTradeNotes(tradeId)
                    setNotes(prev => ({ ...prev, [tradeId]: data }))
                } catch (e: any) {
                    console.error("Failed to load notes:", e)
                }
            }
        }
    }

    const handleAddNote = async (tradeId: string) => {
        if (!newNote.trim()) return
        setIsSubmitting(true)
        try {
            const note = await createTradeNote({
                trade_id: tradeId,
                content: newNote,
                author: "Admin"
            })
            setNotes(prev => ({
                ...prev,
                [tradeId]: [...(prev[tradeId] || []), note]
            }))
            setNewNote("")
        } catch (e) {
            console.error("Failed to add note:", e)
        } finally {
            setIsSubmitting(false)
        }
    }

    const filteredTrades = trades.filter(t =>
        t.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.strategy_id.toLowerCase().includes(searchQuery.toLowerCase())
    )

    return (
        <div className="container mx-auto p-6 space-y-8">
            <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                        <BookOpen className="h-8 w-8 text-primary" />
                        Trade Journal
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Chronological record of trades with technical notes and commentary.
                    </p>
                </div>

                <div className="relative w-full md:w-72">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search Symbol or Strategy..."
                        className="pl-9"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </header>

            <Card>
                <CardHeader>
                    <CardTitle>Trading History</CardTitle>
                    <CardDescription>
                        Displaying recent activity across all strategy runs.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="h-64 flex items-center justify-center">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        </div>
                    ) : filteredTrades.length === 0 ? (
                        <div className="h-64 flex flex-col items-center justify-center text-muted-foreground border-2 border-dashed rounded-lg">
                            <p>No trades found in the ledger.</p>
                        </div>
                    ) : (
                        <div className="border rounded-md">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[180px]">Date</TableHead>
                                        <TableHead>Symbol</TableHead>
                                        <TableHead>Side</TableHead>
                                        <TableHead>Quantity</TableHead>
                                        <TableHead>Price</TableHead>
                                        <TableHead>Strategy</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredTrades.map((trade) => (
                                        <>
                                            <TableRow key={trade.id} className="cursor-pointer hover:bg-muted/50" onClick={() => toggleExpand(trade.id)}>
                                                <TableCell className="font-medium">
                                                    <div className="flex flex-col">
                                                        <span>{format(new Date(trade.timestamp), "MMM dd, HH:mm")}</span>
                                                        <span className="text-xs text-muted-foreground">{format(new Date(trade.timestamp), "yyyy")}</span>
                                                    </div>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge variant="outline" className="font-mono">{trade.symbol}</Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge className={trade.side === "BUY" ? "bg-green-500/10 text-green-600 hover:bg-green-500/20" : "bg-red-500/10 text-red-600 hover:bg-red-500/20"}>
                                                        {trade.side}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>{trade.qty.toLocaleString()}</TableCell>
                                                <TableCell>${trade.price.toFixed(2)}</TableCell>
                                                <TableCell>
                                                    <div className="flex items-center gap-1 text-sm">
                                                        <Tag className="h-3 w-3 text-muted-foreground" />
                                                        {trade.strategy_id}
                                                    </div>
                                                </TableCell>
                                                <TableCell className="text-right">
                                                    <Button variant="ghost" size="sm" className="gap-2">
                                                        <MessageSquare className="h-4 w-4" />
                                                        {notes[trade.id]?.length || 0}
                                                        {expandedTrade === trade.id ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                                    </Button>
                                                </TableCell>
                                            </TableRow>
                                            {expandedTrade === trade.id && (
                                                <TableRow className="bg-muted/30">
                                                    <TableCell colSpan={7} className="p-0">
                                                        <div className="p-6 space-y-6">
                                                            <div className="space-y-4">
                                                                <h4 className="text-sm font-semibold flex items-center gap-2">
                                                                    <MessageSquare className="h-4 w-4" />
                                                                    Trade Notes
                                                                </h4>
                                                                <div className="space-y-3">
                                                                    {(notes[trade.id] || []).map((note) => (
                                                                        <div key={note.id} className="bg-background p-3 rounded-lg border shadow-sm">
                                                                            <div className="flex items-center justify-between mb-2">
                                                                                <span className="text-xs font-bold text-primary">{note.author}</span>
                                                                                <span className="text-[10px] text-muted-foreground">{format(new Date(note.created_at), "PPp")}</span>
                                                                            </div>
                                                                            <p className="text-sm leading-relaxed">{note.content}</p>
                                                                        </div>
                                                                    ))}
                                                                    {(!notes[trade.id] || notes[trade.id].length === 0) && (
                                                                        <p className="text-sm text-muted-foreground italic">No notes yet. Add your commentary below.</p>
                                                                    )}
                                                                </div>
                                                            </div>

                                                            <div className="space-y-3 pt-4 border-t">
                                                                <Textarea
                                                                    placeholder="What was the rationale for this trade? Any technical observations?"
                                                                    value={newNote}
                                                                    onChange={(e) => setNewNote(e.target.value)}
                                                                    className="min-h-[100px] resize-none"
                                                                />
                                                                <div className="flex justify-end">
                                                                    <Button
                                                                        size="sm"
                                                                        className="gap-2"
                                                                        onClick={() => handleAddNote(trade.id)}
                                                                        disabled={isSubmitting || !newNote.trim()}
                                                                    >
                                                                        {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                                                                        Add Entry
                                                                    </Button>
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                                </TableRow>
                                            )}
                                        </>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
