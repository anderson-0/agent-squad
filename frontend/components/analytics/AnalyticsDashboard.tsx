import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    BarChart, Bar, PieChart, Pie, Cell
} from 'recharts';
import { Loader2, TrendingUp, Users, Clock, AlertTriangle } from 'lucide-react';
import { axiosInstance } from '@/lib/axios';

interface AnalyticsData {
    summary: {
        total_questions: number;
        total_resolved: number;
        total_escalated: number;
        total_timeouts: number;
        avg_resolution_time_seconds: number;
        resolution_rate: number;
        escalation_rate: number;
    };
    time_series: Array<{
        timestamp: string;
        questions: number;
        resolved: number;
        escalated: number;
        avg_time: number;
    }>;
    question_types: Record<string, number>;
}

interface AnalyticsDashboardProps {
    squadId: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export function AnalyticsDashboard({ squadId }: AnalyticsDashboardProps) {
    const [data, setData] = useState<AnalyticsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [period, setPeriod] = useState('7'); // days

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const res = await axiosInstance.get(`/api/v1/analytics/squad/${squadId}?days=${period}`);
                setData(res.data);
            } catch (error) {
                console.error("Failed to fetch analytics:", error);
            } finally {
                setLoading(false);
            }
        };

        if (squadId) {
            fetchData();
        }
    }, [squadId, period]);

    if (loading) {
        return (
            <div className="flex h-96 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (!data) {
        return <div className="p-4 text-center">No data available</div>;
    }

    const pieData = Object.entries(data.question_types).map(([name, value]) => ({ name, value }));

    return (
        <div className="space-y-6 p-6">
            <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold tracking-tight">Squad Analytics</h2>
                <div className="flex gap-2">
                    {['7', '30', '90'].map((d) => (
                        <button
                            key={d}
                            onClick={() => setPeriod(d)}
                            className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${period === d
                                    ? 'bg-primary text-primary-foreground'
                                    : 'bg-muted text-muted-foreground hover:bg-accent'
                                }`}
                        >
                            {d} Days
                        </button>
                    ))}
                </div>
            </div>

            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Questions</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.summary.total_questions}</div>
                        <p className="text-xs text-muted-foreground">
                            {data.summary.resolution_rate.toFixed(1)}% resolution rate
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Resolution Time</CardTitle>
                        <Clock className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">
                            {(data.summary.avg_resolution_time_seconds / 60).toFixed(1)}m
                        </div>
                        <p className="text-xs text-muted-foreground">
                            Average time to resolve
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Escalations</CardTitle>
                        <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.summary.total_escalated}</div>
                        <p className="text-xs text-muted-foreground">
                            {data.summary.escalation_rate.toFixed(1)}% escalation rate
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Timeouts</CardTitle>
                        <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{data.summary.total_timeouts}</div>
                        <p className="text-xs text-muted-foreground">
                            Unanswered questions
                        </p>
                    </CardContent>
                </Card>
            </div>

            <Tabs defaultValue="overview" className="space-y-4">
                <TabsList>
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="performance">Performance</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                        <Card className="col-span-4">
                            <CardHeader>
                                <CardTitle>Activity Overview</CardTitle>
                            </CardHeader>
                            <CardContent className="pl-2">
                                <ResponsiveContainer width="100%" height={350}>
                                    <LineChart data={data.time_series}>
                                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                        <XAxis
                                            dataKey="timestamp"
                                            tickFormatter={(str) => new Date(str).toLocaleDateString()}
                                            className="text-xs"
                                        />
                                        <YAxis className="text-xs" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                                            labelFormatter={(label) => new Date(label).toLocaleString()}
                                        />
                                        <Legend />
                                        <Line type="monotone" dataKey="questions" stroke="#8884d8" name="Questions" />
                                        <Line type="monotone" dataKey="resolved" stroke="#82ca9d" name="Resolved" />
                                        <Line type="monotone" dataKey="escalated" stroke="#ff7300" name="Escalated" />
                                    </LineChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>

                        <Card className="col-span-3">
                            <CardHeader>
                                <CardTitle>Question Types</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <ResponsiveContainer width="100%" height={350}>
                                    <PieChart>
                                        <Pie
                                            data={pieData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={80}
                                            fill="#8884d8"
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {pieData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip />
                                        <Legend />
                                    </PieChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>

                <TabsContent value="performance" className="space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Response Time Trend</CardTitle>
                        </CardHeader>
                        <CardContent className="pl-2">
                            <ResponsiveContainer width="100%" height={350}>
                                <BarChart data={data.time_series}>
                                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                    <XAxis
                                        dataKey="timestamp"
                                        tickFormatter={(str) => new Date(str).toLocaleDateString()}
                                        className="text-xs"
                                    />
                                    <YAxis className="text-xs" />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'hsl(var(--background))', borderColor: 'hsl(var(--border))' }}
                                        labelFormatter={(label) => new Date(label).toLocaleString()}
                                    />
                                    <Legend />
                                    <Bar dataKey="avg_time" fill="#8884d8" name="Avg Time (s)" />
                                </BarChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>
        </div>
    );
}
