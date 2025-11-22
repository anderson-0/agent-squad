'use client';

import { useDraggable } from '@dnd-kit/core';
import { motion } from 'framer-motion';
import {
  Clock,
  CheckCircle2,
  AlertCircle,
  GripVertical,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AgentAvatar } from './AgentAvatar';
import type { Task } from '@/types/squad';

interface TaskCardProps {
  task: Task;
  index: number;
  onClick?: () => void;
}

export function TaskCard({ task, index, onClick }: TaskCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({ id: task.id });

  const style = transform
    ? {
      transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    }
    : undefined;

  const priorityConfig = {
    low: {
      color: 'text-gray-600',
      bgColor: 'bg-gray-100',
      borderColor: 'border-gray-300',
    },
    medium: {
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-100',
      borderColor: 'border-yellow-300',
    },
    high: {
      color: 'text-red-600',
      bgColor: 'bg-red-100',
      borderColor: 'border-red-300',
    },
  };

  const config = priorityConfig[task.priority];

  // Calculate subtask progress
  const completedSubtasks = task.subtasks?.filter((s) => s.completed).length || 0;
  const totalSubtasks = task.subtasks?.length || 0;
  const subtaskProgress = totalSubtasks > 0
    ? Math.round((completedSubtasks / totalSubtasks) * 100)
    : 100;

  return (
    <motion.div
      ref={setNodeRef}
      style={style}
      initial={{ opacity: 0, y: 20 }}
      animate={{
        opacity: isDragging ? 0.5 : 1,
        y: 0,
        scale: isDragging ? 1.02 : 1,
      }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{
        duration: 0.2,
        delay: index * 0.05,
        ease: [0.22, 1, 0.36, 1],
      }}
    >
      <Card
        onClick={onClick}
        className={`p-4 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow ${isDragging ? 'shadow-lg ring-2 ring-blue-500' : ''
          }`}
      >
        {/* Drag Handle & Priority */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing">
            <GripVertical className="h-5 w-5 text-muted-foreground" />
          </div>

          <Badge
            variant="outline"
            className={`${config.bgColor} ${config.borderColor} ${config.color} text-xs shrink-0`}
          >
            {task.priority}
          </Badge>
        </div>

        {/* Title */}
        <h4 className="font-semibold text-sm mb-2 line-clamp-2">
          {task.title}
        </h4>

        {/* Description */}
        {task.description && (
          <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
            {task.description}
          </p>
        )}

        {/* Subtasks Progress */}
        {totalSubtasks > 0 && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground mb-1.5">
              <span>Subtasks</span>
              <span>{completedSubtasks}/{totalSubtasks}</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                initial={{ width: 0 }}
                animate={{ width: `${subtaskProgress}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
              />
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between pt-3 border-t">
          {/* Time/Status */}
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            {task.time_estimate_hours && (
              <>
                <Clock className="h-3.5 w-3.5" />
                <span>{task.time_estimate_hours}h</span>
              </>
            )}
            {task.status === 'done' && task.completed_at && (
              <>
                <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
                <span className="text-green-600">Done</span>
              </>
            )}
          </div>

          {/* Assigned Agent */}
          {task.assigned_agent_id && (
            <div className="flex items-center gap-2">
              {/* We'd need to pass agent data here in a real implementation */}
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs text-white font-medium">
                A
              </div>
            </div>
          )}
        </div>
      </Card>
    </motion.div>
  );
}
