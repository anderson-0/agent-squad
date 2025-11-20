'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { tasksAPI } from '@/lib/api/tasks';
import { executionsAPI } from '@/lib/api/executions';
import { Task, TaskExecution } from '@/lib/api/types';
import { DeleteTaskDialog } from '@/components/tasks/DeleteTaskDialog';
import { EditTaskDialog } from '@/components/tasks/EditTaskDialog';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ArrowLeft, Calendar, CheckSquare, PlayCircle, Users } from 'lucide-react';
import { format } from 'date-fns';
import { useToast } from '@/lib/hooks/use-toast';
import { handleApiError } from '@/lib/api/client';

export default function TaskDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const taskId = params.id as string;

  const [task, setTask] = useState<Task | null>(null);
  const [executions, setExecutions] = useState<TaskExecution[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isExecuting, setIsExecuting] = useState(false);

  const fetchTaskDetails = async () => {
    try {
      setIsLoading(true);

      // Fetch task details
      const taskData = await tasksAPI.getTask(taskId);
      setTask(taskData);

      // Fetch task executions
      const executionsData = await executionsAPI.listTaskExecutions(taskId, 1, 20);
      setExecutions(executionsData.items);
    } catch (error) {
      console.error('Failed to fetch task details:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (taskId) {
      fetchTaskDetails();
    }
  }, [taskId]);

  const handleExecuteTask = async () => {
    if (!task?.squad_id) {
      toast({
        title: 'Cannot execute task',
        description: 'Task must be assigned to a squad before execution',
        variant: 'destructive',
      });
      return;
    }

    setIsExecuting(true);
    try {
      const execution = await executionsAPI.createExecution({
        task_id: task.id,
        squad_id: task.squad_id,
      });

      toast({
        title: 'Task execution started',
        description: 'The task is now being executed by the squad.',
      });

      // Refresh task details to show new execution
      await fetchTaskDetails();

      // Navigate to execution details page
      router.push(`/executions/${execution.id}`);
    } catch (error) {
      toast({
        title: 'Failed to execute task',
        description: handleApiError(error),
        variant: 'destructive',
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
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

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold">Task not found</h2>
        <p className="text-muted-foreground mt-2">
          The task you're looking for doesn't exist.
        </p>
        <Link href="/tasks">
          <Button className="mt-4">Back to Tasks</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/tasks">
          <Button variant="ghost" size="sm">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">{task.title}</h1>
          <p className="text-muted-foreground mt-1">{task.description}</p>
        </div>
        <div className="flex gap-2">
          {task.squad_id && (
            <Button onClick={handleExecuteTask} disabled={isExecuting}>
              <PlayCircle className="h-4 w-4 mr-2" />
              {isExecuting ? 'Starting...' : 'Execute Task'}
            </Button>
          )}
          <EditTaskDialog task={task} onSuccess={fetchTaskDetails} />
          <DeleteTaskDialog taskId={task.id} taskTitle={task.title} />
        </div>
      </div>

      {/* Task Info Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge className={getStatusColor(task.status)} variant="secondary">
              {task.status}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Priority</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge className={getPriorityColor(task.priority)} variant="secondary">
              {task.priority}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Type</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="secondary">{task.task_type}</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Executions</CardTitle>
            <PlayCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{executions.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Created</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              {format(new Date(task.created_at), 'MMM d, yyyy')}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Task Details */}
      <Card>
        <CardHeader>
          <CardTitle>Task Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Task ID</span>
              <span className="text-sm text-muted-foreground font-mono">{task.id}</span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Organization ID</span>
              <span className="text-sm text-muted-foreground font-mono">
                {task.organization_id}
              </span>
            </div>
            <Separator />
            {task.squad_id && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Assigned Squad</span>
                  <Link href={`/squads/${task.squad_id}`}>
                    <Badge variant="outline" className="hover:bg-gray-100">
                      View Squad
                    </Badge>
                  </Link>
                </div>
                <Separator />
              </>
            )}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Created By</span>
              <span className="text-sm text-muted-foreground font-mono">
                {task.created_by}
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Last Updated</span>
              <span className="text-sm text-muted-foreground">
                {format(new Date(task.updated_at), 'MMM d, yyyy HH:mm')}
              </span>
            </div>
            {task.completed_at && (
              <>
                <Separator />
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Completed At</span>
                  <span className="text-sm text-muted-foreground">
                    {format(new Date(task.completed_at), 'MMM d, yyyy HH:mm')}
                  </span>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Execution History */}
      <Card>
        <CardHeader>
          <CardTitle>Execution History</CardTitle>
          <CardDescription>
            Past executions of this task ({executions.length} total)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {executions.length === 0 ? (
            <div className="text-center py-12">
              <PlayCircle className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-semibold">No executions yet</h3>
              <p className="mt-2 text-sm text-muted-foreground">
                This task hasn't been executed yet
              </p>
              {task.squad_id && (
                <Button className="mt-6" onClick={handleExecuteTask} disabled={isExecuting}>
                  <PlayCircle className="h-4 w-4 mr-2" />
                  {isExecuting ? 'Starting...' : 'Execute Now'}
                </Button>
              )}
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
                  <TableHead>Completed</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {executions.map((execution) => (
                  <TableRow key={execution.id}>
                    <TableCell>
                      <Link
                        href={`/executions/${execution.id}`}
                        className="font-mono text-sm hover:underline"
                      >
                        {execution.id.slice(0, 8)}...
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Link href={`/squads/${execution.squad_id}`}>
                        <Badge variant="outline" className="hover:bg-gray-100">
                          View Squad
                        </Badge>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusColor(execution.status)} variant="secondary">
                        {execution.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">{execution.workflow_state}</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${execution.progress_percentage}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {execution.progress_percentage}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {format(new Date(execution.started_at), 'MMM d, HH:mm')}
                    </TableCell>
                    <TableCell>
                      {execution.completed_at
                        ? format(new Date(execution.completed_at), 'MMM d, HH:mm')
                        : '-'}
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
