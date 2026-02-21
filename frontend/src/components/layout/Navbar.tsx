import Link from "next/link"
import { Activity, BarChart2, FlaskConical, GitCompare } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export function Navbar() {
    return (
        <div className="border-b">
            <div className="container flex h-16 items-center px-4">
                <div className="mr-8 hidden md:flex">
                    <Link href="/" className="mr-6 flex items-center space-x-2">
                        <Activity className="h-6 w-6" />
                        <span className="hidden font-bold sm:inline-block">
                            Strategy Lab
                        </span>
                    </Link>
                    <nav className="flex items-center space-x-6 text-sm font-medium">
                        <Link
                            href="/"
                            className={cn(
                                "transition-colors hover:text-foreground/80 text-foreground/60"
                            )}
                        >
                            Dashboard
                        </Link>
                        <Link
                            href="/backtest"
                            className={cn(
                                "transition-colors hover:text-foreground/80 text-foreground/60"
                            )}
                        >
                            Backtest
                        </Link>
                        <Link
                            href="/optimize"
                            className={cn(
                                "transition-colors hover:text-foreground/80 text-foreground/60"
                            )}
                        >
                            Optimization
                        </Link>
                        <Link
                            href="/compare"
                            className={cn(
                                "transition-colors hover:text-foreground/80 text-foreground/60"
                            )}
                        >
                            Compare
                        </Link>
                    </nav>
                </div>
                <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
                    <div className="w-full flex-1 md:w-auto md:flex-none">
                        {/* Search or other items could go here */}
                    </div>
                    <div className="flex items-center space-x-2">
                        <Button variant="ghost" size="icon" asChild>
                            <Link href="https://github.com/Atom1250/trading-system" target="_blank">
                                <span className="sr-only">GitHub</span>
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    width="24"
                                    height="24"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    className="h-5 w-5"
                                >
                                    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4" />
                                    <path d="M9 18c-4.51 2-5-2-7-2" />
                                </svg>
                            </Link>
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    )
}
