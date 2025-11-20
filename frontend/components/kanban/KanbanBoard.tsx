/**
 * Kanban Board Component (Stream F)
 * 
 * Visualizes dynamic tasks organized by phase (Investigation, Building, Validation)
 */
'use client';

import React, { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { TaskDetailModal } from './TaskDetailModal';

// Types
interface KanbanTask {
  id: string;
  title: string;
  description: string;
  phase: string;
  status: string;
  rationale?: string;
  spawned_by_agent_id: string;
  created_at: string;
  updated_at: string;
  blocking_task_ids: string[];
  blocked_by_task_ids: string[];
}

interface KanbanColumn {
  phase: string;
  title: string;
  tasks: KanbanTask[];
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  pending_tasks: number;
}

interface KanbanBoardData {
  execution_id: string;
  columns: KanbanColumn[];
  dependencies: Array<{
    from_task_id: string;
    to_task_id: string;
    type: string;
  }>;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  pending_tasks: number;
}

interface KanbanBoardProps {
  executionId: string;
  onTaskClick?: (taskId: string) => void;
}

export function KanbanBoard({ executionId, onTaskClick }: KanbanBoardProps) {
  const [boardData, setBoardData] = useState<KanbanBoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<KanbanTask | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    loadBoardData();
    
    // Set up SSE for real-time updates
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const eventSource = new EventSource(
      `${apiUrl}/api/v1/sse/execution/${executionId}`,
      {
        withCredentials: true,
      }
    );

    eventSource.addEventListener('task_spawned', () => {
      loadBoardData();
    });

    eventSource.addEventListener('task_status_updated', () => {
      loadBoardData();
    });

    eventSource.addEventListener('error', (e) => {
      console.error('SSE connection error:', e);
      // Fallback to polling if SSE fails
      const interval = setInterval(loadBoardData, 5000);
      eventSource.close();
      return () => clearInterval(interval);
    });

    // Fallback polling every 30 seconds (less aggressive with SSE)
    const interval = setInterval(loadBoardData, 30000);

    return () => {
      eventSource.close();
      clearInterval(interval);
    };
  }, [executionId]);

  const loadBoardData = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getKanbanBoard(executionId);
      setBoardData(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load Kanban board');
      console.error('Error loading Kanban board:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'blocked':
        return 'bg-red-100 text-red-800';
      case 'failed':
        return 'bg-red-200 text-red-900';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'investigation':
        return 'border-purple-300 bg-purple-50';
      case 'building':
        return 'border-blue-300 bg-blue-50';
      case 'validation':
        return 'border-green-300 bg-green-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  if (loading && !boardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading Kanban board...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!boardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">No board data available</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full">
      {/* Board Header */}
      <div className="mb-6 p-4 bg-white rounded-lg shadow-sm border">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Workflow Kanban</h2>
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Total:</span>
              <Badge variant="outline">{boardData.total_tasks}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Completed:</span>
              <Badge className="bg-green-100 text-green-800">{boardData.completed_tasks}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">In Progress:</span>
              <Badge className="bg-blue-100 text-blue-800">{boardData.in_progress_tasks}</Badge>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-gray-600">Pending:</span>
              <Badge className="bg-gray-100 text-gray-800">{boardData.pending_tasks}</Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="grid grid-cols-3 gap-4">
        {boardData.columns.map((column) => (
          <div
            key={column.phase}
            className={`rounded-lg border-2 p-4 ${getPhaseColor(column.phase)}`}
          >
            {/* Column Header */}
            <div className="mb-4 pb-2 border-b border-gray-300">
              <h3 className="text-lg font-semibold">{column.title}</h3>
              <div className="flex gap-2 mt-2 text-xs text-gray-600">
                <span>{column.total_tasks} tasks</span>
                <span>•</span>
                <span>{column.completed_tasks} done</span>
                <span>•</span>
                <span>{column.in_progress_tasks} active</span>
              </div>
            </div>

            {/* Tasks */}
            <div className="space-y-3 min-h-[400px]">
              {column.tasks.length === 0 ? (
                <div className="text-center text-gray-400 py-8 text-sm">
                  No tasks in this phase
                </div>
              ) : (
                column.tasks.map((task) => (
                  <Card
                    key={task.id}
                    className={`cursor-pointer hover:shadow-md transition-shadow p-4 ${
                      task.blocked_by_task_ids.length > 0 ? 'opacity-60' : ''
                    }`}
                    onClick={() => {
                      setSelectedTask(task);
                      setIsModalOpen(true);
                      onTaskClick?.(task.id);
                    }}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-sm line-clamp-2">{task.title}</h4>
                      <Badge className={`text-xs ${getStatusColor(task.status)}`}>
                        {task.status}
                      </Badge>
                    </div>
                    
                    <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                      {task.description}
                    </p>
                    
                    {task.rationale && (
                      <p className="text-xs text-gray-500 italic mb-2">
                        💡 {task.rationale}
                      </p>
                    )}
                    
                    <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
                      <span>
                        {task.blocked_by_task_ids.length > 0 && (
                          <span className="text-orange-600">
                            🔗 Blocked by {task.blocked_by_task_ids.length}
                          </span>
                        )}
                      </span>
                      <span>
                        {task.blocking_task_ids.length > 0 && (
                          <span className="text-blue-600">
                            Blocks {task.blocking_task_ids.length}
                          </span>
                        )}
                      </span>
                    </div>
                  </Card>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Task Detail Modal */}
      <TaskDetailModal
        task={selectedTask}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedTask(null);
        }}
        onTaskClick={(taskId) => {
          // Find and open clicked task
          const clickedTask = boardData?.columns
            .flatMap(col => col.tasks)
            .find(t => t.id === taskId);
          if (clickedTask) {
            setSelectedTask(clickedTask);
          }
        }}
      />
    </div>
  );
}

