import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, BarChart2, FlaskConical, LineChart, Activity, Cpu, Server } from "lucide-react";
import Link from "next/link";
import { fetchDashboardStats, fetchRecentActivity } from "@/lib/api";

// Force dynamic rendering as we depend on the backend API
export const dynamic = 'force-dynamic';

export default async function Home() {
  let stats = null;
  let activity = [];
  let error = null;

  try {
    stats = await fetchDashboardStats();
    activity = await fetchRecentActivity();
  } catch (e) {
    console.error("Failed to load dashboard data:", e);
    error = "System is offline or unreachable.";
  }

  return (
    <div className="container mx-auto p-8">
      <header className="mb-12">
        <h1 className="text-4xl font-bold tracking-tight mb-2">Trading Strategy Lab</h1>
        <p className="text-xl text-muted-foreground">
          Design, backtest, and optimize algorithmic trading strategies.
        </p>
      </header>

      {/* System Status Banner */}
      {error ? (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-8 flex items-center">
          <Server className="w-5 h-5 mr-2" />
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Status</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold capitalize text-green-600">
                {stats?.system_status || "Unknown"}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Last updated: {stats ? new Date(stats.last_updated).toLocaleTimeString() : "--"}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Strategies</CardTitle>
              <LineChart className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.active_strategies || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Backtests</CardTitle>
              <BarChart2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.total_backtests || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
              <Cpu className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats?.system_info?.cpu_usage || "0%"}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Mem: {stats?.system_info?.memory_usage || "0%"}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {/* Quick Actions */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <LineChart className="w-6 h-6 text-primary" />
            </div>
            <CardTitle>Backtest Runner</CardTitle>
            <CardDescription>
              Test strategies against historical data.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/backtest">
              <Button className="w-full group">
                Start Backtest
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <FlaskConical className="w-6 h-6 text-primary" />
            </div>
            <CardTitle>Optimization Lab</CardTitle>
            <CardDescription>
              Find optimal parameter sets automatically.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/optimize">
              <Button variant="secondary" className="w-full group">
                Run Optimization
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <BarChart2 className="w-6 h-6 text-primary" />
            </div>
            <CardTitle>Results Comparison</CardTitle>
            <CardDescription>
              Compare performance metrics side-by-side.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/compare">
              <Button variant="outline" className="w-full group">
                Compare Results
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader>
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
              <Cpu className="w-6 h-6 text-primary" />
            </div>
            <CardTitle>AI / ML Analytics</CardTitle>
            <CardDescription>
              Visualize model internals and technical feature weights.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/ml">
              <Button variant="outline" className="w-full group">
                Examine Models
                <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity Table */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold tracking-tight">Recent Activity</h2>
        <Card>
          <CardContent className="p-0">
            <div className="relative w-full overflow-auto">
              <table className="w-full caption-bottom text-sm text-center">
                <thead className="[&_tr]:border-b">
                  <tr className="border-b transition-colors hover:bg-muted/50">
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Type</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Strategy</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Symbol</th>
                    <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">Metrics</th>
                    <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">Time</th>
                  </tr>
                </thead>
                <tbody className="[&_tr:last-child]:border-0">
                  {activity.length > 0 ? (
                    activity.map((item: any) => (
                      <tr key={item.id} className="border-b transition-colors hover:bg-muted/50">
                        <td className="p-4 align-middle text-left capitalize">{item.type}</td>
                        <td className="p-4 align-middle text-left">{item.strategy}</td>
                        <td className="p-4 align-middle text-left font-semibold">{item.symbol}</td>
                        <td className="p-4 align-middle text-left">
                          {item.metrics.return && <span className="text-green-600 mr-2">Ret: {item.metrics.return}</span>}
                          {item.metrics.sharpe && <span className="text-blue-600">Sharpe: {item.metrics.sharpe}</span>}
                        </td>
                        <td className="p-4 align-middle text-right text-muted-foreground">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} className="p-4 text-center text-muted-foreground">
                        No recent activity found.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="mt-16 border-t pt-8 text-center text-sm text-muted-foreground">
        <p>Built with Next.js, FastAPI, and Python • Version 2.0.0</p>
      </div>
    </div>
  );
}
