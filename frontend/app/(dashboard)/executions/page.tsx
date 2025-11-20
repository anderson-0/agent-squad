'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { executionsAPI } from '@/lib/api/executions';
import { squadsAPI } from '@/lib/api/squads';
import { TaskExecution, Squad } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { PlayCircle, Eye, Activity, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { useToast } from '@/lib/hooks/use-toast';
import { useAuthStore } from '@/lib/store/auth';

export default function ExecutionsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const { user } = useAuthStore();

  const [executions, setExecutions] = useState<TaskExecution[]>([]);
  const [squads, setSquads] = useState<Squad[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [squadFilter, setSquadFilter] = useState<string>('all');

  // Stats
  const [stats, setStats] = useState({
    total: 0,
    inProgress: 0,
    completed: 0,
    failed: 0,
  });

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    calculateStats();
  }, [executions]);

  const fetchData = async () => {
    if (!user?.organization_id) return;

    setLoading(true);
    try {
      // For now, we'll fetch executions without pagination
      // In production, you'd want to implement proper pagination
      const executionsData: TaskExecution[] = [];

      // Fetch squads for filter
      const squadsResponse = await squadsAPI.listSquads(user.organization_id, 1, 100);
      const squadsData = squadsResponse.items || [];
      setSquads(squadsData);

      // Fetch executions for each squad (this is a simplified approach)
      // In a real app, you'd have a dedicated endpoint to list all executions
      for (const squad of squadsData) {
        try {
          const squadExecutions = await executionsAPI.listSquadExecutions(squad.id);
          executionsData.push(...(squadExecutions.items || []));
        } catch (error) {
          // Squad might not have executions, continue
          console.error(`Failed to fetch executions for squad ${squad.id}:`, error);
        }
      }

      setExecutions(executionsData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load executions. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = () => {
    setStats({
      total: executions.length,
      inProgress: executions.filter((e) => e.status === 'in_progress' || e.status === 'pending').length,
      completed: executions.filter((e) => e.status === 'completed').length,
      failed: executions.filter((e) => e.status === 'failed').length,
    });
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline', icon: React.ReactNode }> = {
      pending: { variant: 'secondary', icon: <Clock className="w-3 h-3 mr-1" /> },
      in_progress: { variant: 'default', icon: <Activity className="w-3 h-3 mr-1" /> },
      completed: { variant: 'outline', icon: <CheckCircle2 className="w-3 h-3 mr-1 text-green-600" /> },
      failed: { variant: 'destructive', icon: <XCircle className="w-3 h-3 mr-1" /> },
      cancelled: { variant: 'secondary', icon: <XCircle className="w-3 h-3 mr-1" /> },
    };

    const config = variants[status] || variants.pending;

    return (
      <Badge variant={config.variant} className="flex items-center w-fit">
        {config.icon}
        {status.replace('_', ' ')}
      </Badge>
    );
  };

  const filteredExecutions = executions.filter((execution) => {
    if (statusFilter !== 'all' && execution.status !== statusFilter) return false;
    if (squadFilter !== 'all' && execution.squad_id !== squadFilter) return false;
    return true;
  });

  const getSquadName = (squadId: string) => {
    const squad = squads.find((s) => s.id === squadId);
    return squad?.name || 'Unknown Squad';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Task Executions</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage your task execution workflows
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Executions</CardTitle>
            <PlayCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Activity className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inProgress}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.completed}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.failed}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1">
              <label className="text-sm font-medium mb-2 block">Squad</label>
              <Select value={squadFilter} onValueChange={setSquadFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All Squads" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Squads</SelectItem>
                  {squads.map((squad) => (
                    <SelectItem key={squad.id} value={squad.id}>
                      {squad.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button
                variant="outline"
                onClick={() => {
                  setStatusFilter('all');
                  setSquadFilter('all');
                }}
              >
                Clear Filters
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Executions</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : filteredExecutions.length === 0 ? (
            <div className="text-center py-12">
              <PlayCircle className="mx-auto h-12 w-12 text-muted-foreground" />
              <h3 className="mt-4 text-lg font-semibold">No executions found</h3>
              <p className="text-muted-foreground mt-2">
                {statusFilter !== 'all' || squadFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Execute a task to get started'}
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Execution ID</TableHead>
                  <TableHead>Squad</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Workflow State</TableHead>
                  <TableHead>Progress</TableHead>
                  <TableHead>Started</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredExecutions.map((execution) => (
                  <TableRow
                    key={execution.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => router.push(`/executions/${execution.id}`)}
                  >
                    <TableCell className="font-mono text-sm">
                      {execution.id.slice(0, 8)}...
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/squads/${execution.squad_id}`}
                        className="text-blue-600 hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {getSquadName(execution.squad_id)}
                      </Link>
                    </TableCell>
                    <TableCell>{getStatusBadge(execution.status)}</TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {execution.workflow_state || 'initializing'}
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-muted rounded-full h-2 max-w-[100px]">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${execution.progress_percentage || 0}%` }}
                          />
                        </div>
                        <span className="text-sm text-muted-foreground min-w-[40px]">
                          {execution.progress_percentage || 0}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {format(new Date(execution.started_at), 'MMM d, HH:mm')}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/executions/${execution.id}`);
                        }}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
