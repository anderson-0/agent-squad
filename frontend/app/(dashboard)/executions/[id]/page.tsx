'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { executionsAPI } from '@/lib/api/executions';
import { TaskExecution, AgentMessage } from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  ArrowLeft,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  StopCircle,
  Radio,
  MessageSquare,
  User,
  Bot,
} from 'lucide-react';
import { format } from 'date-fns';
import { useToast } from '@/lib/hooks/use-toast';

export default function ExecutionDetailsPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { toast } = useToast();
  const { id: executionId } = params;

  const [execution, setExecution] = useState<TaskExecution | null>(null);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [cancelling, setCancelling] = useState(false);

  const eventSourceRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchExecution();
    return () => {
      // Cleanup: close EventSource on unmount
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [executionId]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchExecution = async () => {
    setLoading(true);
    try {
      const data = await executionsAPI.getExecution(executionId);
      setExecution(data);

      // If execution is in progress, start streaming
      if (data.status === 'in_progress' || data.status === 'pending') {
        startStreaming();
      } else {
        // If completed/failed, fetch historical messages
        fetchMessages();
      }
    } catch (error) {
      console.error('Failed to fetch execution:', error);
      toast({
        title: 'Error',
        description: 'Failed to load execution details.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async () => {
    try {
      const data = await executionsAPI.getExecutionMessages(executionId);
      setMessages(data);
    } catch (error) {
      console.error('Failed to fetch messages:', error);
    }
  };

  const startStreaming = () => {
    if (eventSourceRef.current) {
      return; // Already streaming
    }

    setIsStreaming(true);

    const eventSource = executionsAPI.streamExecutionMessages(
      executionId,
      (message) => {
        // Add new message to the list
        setMessages((prev) => [...prev, message]);

        // Update execution progress if metadata contains it
        if (message.metadata?.progress_percentage !== undefined) {
          setExecution((prev) =>
            prev
              ? {
                  ...prev,
                  progress_percentage: message.metadata?.progress_percentage || 0,
                }
              : null
          );
        }

        // Update execution status if message indicates completion
        if (message.metadata?.execution_status) {
          setExecution((prev) =>
            prev
              ? {
                  ...prev,
                  status: message.metadata?.execution_status || prev.status,
                }
              : null
          );
        }
      },
      (error) => {
        console.error('SSE error:', error);
        setIsStreaming(false);
        toast({
          title: 'Connection Error',
          description: 'Lost connection to execution stream. Retrying...',
          variant: 'destructive',
        });

        // Retry after 5 seconds
        setTimeout(() => {
          startStreaming();
        }, 5000);
      },
      () => {
        // Stream completed
        setIsStreaming(false);
        toast({
          title: 'Execution Complete',
          description: 'The execution has finished.',
        });

        // Refresh execution data
        fetchExecution();
      }
    );

    eventSourceRef.current = eventSource;
  };

  const handleCancelExecution = async () => {
    setCancelling(true);
    try {
      await executionsAPI.cancelExecution(executionId);

      toast({
        title: 'Success',
        description: 'Execution cancelled successfully.',
      });

      // Close EventSource if streaming
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      setIsStreaming(false);

      // Refresh execution
      await fetchExecution();
    } catch (error) {
      console.error('Failed to cancel execution:', error);
      toast({
        title: 'Error',
        description: 'Failed to cancel execution. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setCancelling(false);
      setShowCancelDialog(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<
      string,
      { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }
    > = {
      pending: { variant: 'secondary', icon: <Clock className="w-3 h-3 mr-1" /> },
      in_progress: { variant: 'default', icon: <Activity className="w-3 h-3 mr-1" /> },
      completed: {
        variant: 'outline',
        icon: <CheckCircle2 className="w-3 h-3 mr-1 text-green-600" />,
      },
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

  const getMessageIcon = (messageType: string) => {
    if (messageType.includes('user') || messageType.includes('human')) {
      return <User className="w-4 h-4" />;
    }
    return <Bot className="w-4 h-4" />;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <XCircle className="w-16 h-16 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-semibold">Execution Not Found</h2>
        <p className="text-muted-foreground mt-2">
          The execution you're looking for doesn't exist.
        </p>
        <Button className="mt-4" onClick={() => router.push('/executions')}>
          Back to Executions
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Execution Details</h1>
            <p className="text-muted-foreground mt-1 font-mono text-sm">{execution.id}</p>
          </div>
        </div>
        <div className="flex gap-2">
          {isStreaming && (
            <Badge variant="outline" className="flex items-center gap-2">
              <Radio className="w-3 h-3 animate-pulse text-red-600" />
              Live
            </Badge>
          )}
          {(execution.status === 'in_progress' || execution.status === 'pending') && (
            <Button
              variant="destructive"
              onClick={() => setShowCancelDialog(true)}
              disabled={cancelling}
            >
              <StopCircle className="w-4 h-4 mr-2" />
              Cancel Execution
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status</CardTitle>
          </CardHeader>
          <CardContent>{getStatusBadge(execution.status)}</CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Workflow State</CardTitle>
          </CardHeader>
          <CardContent>
            <code className="text-xs bg-muted px-2 py-1 rounded">
              {execution.workflow_state || 'initializing'}
            </code>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Progress</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-muted rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${execution.progress_percentage || 0}%` }}
                  />
                </div>
                <span className="text-sm font-medium">{execution.progress_percentage || 0}%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Started</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{format(new Date(execution.started_at), 'MMM d, HH:mm:ss')}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              {execution.completed_at
                ? `${Math.round(
                    (new Date(execution.completed_at).getTime() -
                      new Date(execution.started_at).getTime()) /
                      1000
                  )}s`
                : 'In progress...'}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Execution Details */}
        <Card>
          <CardHeader>
            <CardTitle>Execution Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">Execution ID</p>
              <p className="font-mono text-sm">{execution.id}</p>
            </div>

            <Separator />

            <div>
              <p className="text-sm text-muted-foreground">Task ID</p>
              <Link
                href={`/tasks/${execution.task_id}`}
                className="font-mono text-sm text-blue-600 hover:underline"
              >
                {execution.task_id}
              </Link>
            </div>

            <Separator />

            <div>
              <p className="text-sm text-muted-foreground">Squad ID</p>
              <Link
                href={`/squads/${execution.squad_id}`}
                className="font-mono text-sm text-blue-600 hover:underline"
              >
                {execution.squad_id}
              </Link>
            </div>

            <Separator />

            {execution.error && (
              <>
                <div>
                  <p className="text-sm text-muted-foreground">Error</p>
                  <p className="text-sm text-red-600">{execution.error}</p>
                </div>
                <Separator />
              </>
            )}

            {execution.result && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">Result</p>
                <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                  {JSON.stringify(execution.result, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Message Stream */}
        <Card className="md:col-span-1">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                Agent Messages
                {isStreaming && <Radio className="w-4 h-4 animate-pulse text-red-600" />}
              </CardTitle>
              <Badge variant="outline">{messages.length} messages</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px] pr-4">
              {messages.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No messages yet</p>
                  {isStreaming && <p className="text-xs mt-1">Waiting for agent activity...</p>}
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message, idx) => (
                    <div key={message.id || idx} className="flex gap-3">
                      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        {getMessageIcon(message.message_type)}
                      </div>
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-medium">
                            {message.message_type.replace('_', ' ')}
                          </p>
                          <span className="text-xs text-muted-foreground">
                            {format(new Date(message.timestamp), 'HH:mm:ss')}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground">{message.content}</p>
                        {message.metadata && Object.keys(message.metadata).length > 0 && (
                          <details className="text-xs">
                            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                              Metadata
                            </summary>
                            <pre className="mt-1 bg-muted p-2 rounded overflow-x-auto">
                              {JSON.stringify(message.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Cancel Confirmation Dialog */}
      <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Execution?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel this execution? This action cannot be undone and will
              stop all agent activity.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={cancelling}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleCancelExecution} disabled={cancelling}>
              {cancelling ? 'Cancelling...' : 'Yes, Cancel Execution'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
