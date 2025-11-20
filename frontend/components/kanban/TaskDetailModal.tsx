/**
 * Task Detail Modal Component (Stream F Enhancement)
 * 
 * Shows detailed information about a task
 */
'use client';

import React from 'react';
import { Badge } from '@/components/ui/badge';

interface TaskDetail {
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

interface TaskDetailModalProps {
  task: TaskDetail | null;
  isOpen: boolean;
  onClose: () => void;
  onTaskClick?: (taskId: string) => void;
}

export function TaskDetailModal({ 
  task, 
  isOpen, 
  onClose, 
  onTaskClick 
}: TaskDetailModalProps) {
  if (!isOpen || !task) return null;

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'investigation':
        return 'bg-purple-100 text-purple-800';
      case 'building':
        return 'bg-blue-100 text-blue-800';
      case 'validation':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">{task.title}</h2>
              <div className="flex gap-2 flex-wrap">
                <Badge className={getPhaseColor(task.phase)}>
                  {task.phase}
                </Badge>
                <Badge className={getStatusColor(task.status)}>
                  {task.status}
                </Badge>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Description</h3>
            <p className="text-gray-900 whitespace-pre-wrap">{task.description}</p>
          </div>

          {/* Rationale */}
          {task.rationale && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Rationale</h3>
              <p className="text-gray-600 italic">{task.rationale}</p>
            </div>
          )}

          {/* Dependencies */}
          {(task.blocking_task_ids.length > 0 || task.blocked_by_task_ids.length > 0) && (
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Dependencies</h3>
              <div className="space-y-2">
                {task.blocked_by_task_ids.length > 0 && (
                  <div>
                    <span className="text-sm text-orange-600 font-medium">
                      Blocked by {task.blocked_by_task_ids.length} task(s):
                    </span>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {task.blocked_by_task_ids.map((taskId) => (
                        <button
                          key={taskId}
                          onClick={() => onTaskClick?.(taskId)}
                          className="text-xs px-2 py-1 bg-orange-50 text-orange-700 rounded hover:bg-orange-100 transition-colors"
                        >
                          {taskId.slice(0, 8)}...
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {task.blocking_task_ids.length > 0 && (
                  <div>
                    <span className="text-sm text-blue-600 font-medium">
                      Blocks {task.blocking_task_ids.length} task(s):
                    </span>
                    <div className="mt-1 flex flex-wrap gap-2">
                      {task.blocking_task_ids.map((taskId) => (
                        <button
                          key={taskId}
                          onClick={() => onTaskClick?.(taskId)}
                          className="text-xs px-2 py-1 bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                        >
                          {taskId.slice(0, 8)}...
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Created</h3>
              <p className="text-sm text-gray-600">{formatDate(task.created_at)}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Last Updated</h3>
              <p className="text-sm text-gray-600">{formatDate(task.updated_at)}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Spawned By</h3>
              <p className="text-sm text-gray-600 font-mono">{task.spawned_by_agent_id.slice(0, 8)}...</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Task ID</h3>
              <p className="text-sm text-gray-600 font-mono">{task.id.slice(0, 8)}...</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

