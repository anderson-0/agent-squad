'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store/auth';
import { squadsAPI } from '@/lib/api/squads';
import { tasksAPI } from '@/lib/api/tasks';
import { executionsAPI } from '@/lib/api/executions';
import { StatCard } from '@/components/dashboard/StatCard';
import { Users, CheckSquare, PlayCircle, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Task, TaskExecution } from '@/lib/api/types';

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const [stats, setStats] = useState({
    totalSquads: 0,
    totalTasks: 0,
    activeExecutions: 0,
    completionRate: 0,
  });
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [recentExecutions, setRecentExecutions] = useState<TaskExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      if (!user?.organization_id) return;

      try {
        setIsLoading(true);

        // Fetch squads
        const squadsData = await squadsAPI.listSquads(user.organization_id, 1, 100);
        
        // Fetch tasks
        const tasksData = await tasksAPI.listTasks(user.organization_id, { page: 1, size: 100 });
        
        // Calculate stats
        const completedTasks = tasksData.items.filter((t) => t.status === 'completed').length;
        const completionRate = tasksData.total > 0 
          ? Math.round((completedTasks / tasksData.total) * 100) 
          : 0;

        setStats({
          totalSquads: squadsData.total,
          totalTasks: tasksData.total,
          activeExecutions: tasksData.items.filter((t) => t.status === 'in_progress').length,
          completionRate,
        });

        // Get recent tasks (last 5)
        setRecentTasks(tasksData.items.slice(0, 5));

        // Try to get recent executions for first squad if available
        if (squadsData.items.length > 0) {
          const executionsData = await executionsAPI.listSquadExecutions(
            squadsData.items[0].id,
            1,
            5
          );
          setRecentExecutions(executionsData.items);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [user]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome back, {user?.full_name}! Here's what's happening with your squads.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {isLoading ? (
          <>
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </>
        ) : (
          <>
            <StatCard
              title="Total Squads"
              value={stats.totalSquads}
              description="Active AI agent squads"
              icon={Users}
            />
            <StatCard
              title="Total Tasks"
              value={stats.totalTasks}
              description="All tasks created"
              icon={CheckSquare}
            />
            <StatCard
              title="Active Executions"
              value={stats.activeExecutions}
              description="Currently running"
              icon={PlayCircle}
            />
            <StatCard
              title="Completion Rate"
              value={`${stats.completionRate}%`}
              description="Tasks completed"
              icon={TrendingUp}
            />
          </>
        )}
      </div>

      {/* Recent Activity */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Tasks */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Tasks</CardTitle>
            <CardDescription>Latest tasks in your organization</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
              </div>
            ) : recentTasks.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No tasks yet</p>
                <Link href="/tasks/new">
                  <Button className="mt-4" size="sm">Create your first task</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {recentTasks.map((task) => (
                  <Link
                    key={task.id}
                    href={`/tasks/${task.id}`}
                    className="block rounded-lg border p-3 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{task.title}</p>
                        <p className="text-sm text-muted-foreground truncate mt-0.5">
                          {task.description}
                        </p>
                      </div>
                      <div className="flex flex-col gap-1 items-end">
                        <Badge className={getStatusColor(task.status)} variant="secondary">
                          {task.status}
                        </Badge>
                        <Badge className={getPriorityColor(task.priority)} variant="secondary">
                          {task.priority}
                        </Badge>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Executions */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Executions</CardTitle>
            <CardDescription>Latest task executions</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
                <Skeleton className="h-16" />
              </div>
            ) : recentExecutions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <p>No executions yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {recentExecutions.map((execution) => (
                  <Link
                    key={execution.id}
                    href={`/executions/${execution.id}`}
                    className="block rounded-lg border p-3 hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium">Execution #{execution.id.slice(0, 8)}</p>
                        <p className="text-sm text-muted-foreground">
                          {execution.workflow_state}
                        </p>
                      </div>
                      <div className="flex flex-col gap-1 items-end">
                        <Badge className={getStatusColor(execution.status)} variant="secondary">
                          {execution.status}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {execution.progress_percentage}%
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks to get you started</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Link href="/squads/new">
              <Button>Create Squad</Button>
            </Link>
            <Link href="/tasks/new">
              <Button variant="outline">Create Task</Button>
            </Link>
            <Link href="/squads">
              <Button variant="outline">View All Squads</Button>
            </Link>
            <Link href="/tasks">
              <Button variant="outline">View All Tasks</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
