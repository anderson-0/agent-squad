'use client';

import { useState } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
} from '@dnd-kit/core';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TaskCard } from './TaskCard';
import { WIPLimitModal } from './WIPLimitModal';
import { ReviewFeedbackModal } from './ReviewFeedbackModal';
import type { Task, TaskStatus, Agent } from '@/types/squad';

interface KanbanBoardProps {
  tasks: Task[];
  agents: Agent[];
  onTaskUpdate?: (taskId: string, status: TaskStatus, feedback?: string) => void;
}

const columns: { id: TaskStatus; title: string; color: string }[] = [
  { id: 'pending', title: 'Pending', color: 'border-gray-300 bg-gray-50/50 dark:bg-gray-900/20' },
  { id: 'in_progress', title: 'In Progress', color: 'border-blue-300 bg-blue-50/50 dark:bg-blue-900/20' },
  { id: 'in_review', title: 'In Review', color: 'border-purple-300 bg-purple-50/50 dark:bg-purple-900/20' },
  { id: 'done', title: 'Done', color: 'border-green-300 bg-green-50/50 dark:bg-green-900/20' },
];

// Droppable Column Component
function DroppableColumn({
  id,
  children,
  className,
}: {
  id: string;
  children: React.ReactNode;
  className?: string;
}) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={`${className} ${isOver ? 'ring-2 ring-blue-500 ring-offset-2' : ''}`}
    >
      {children}
    </div>
  );
}

export function KanbanBoard({ tasks, agents, onTaskUpdate }: KanbanBoardProps) {
  const [taskList, setTaskList] = useState(tasks);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [showWIPModal, setShowWIPModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [pendingTask, setPendingTask] = useState<Task | null>(null);
  const [pendingStatus, setPendingStatus] = useState<TaskStatus | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor)
  );

  // Calculate available agents (not assigned to any task)
  const availableAgents = agents.filter((agent) => !agent.current_task_id);
  const availableAgentsCount = availableAgents.length;

  // Count tasks in progress
  const tasksInProgress = taskList.filter((t) => t.status === 'in_progress').length;

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = active.id as string;
    const overId = over.id as string;

    // Check if dragging over a column
    const overColumn = columns.find((col) => col.id === overId);
    if (overColumn) {
      const activeTask = taskList.find((t) => t.id === activeId);
      if (activeTask && activeTask.status !== overColumn.id) {
        // Don't update state here for in_progress moves - we'll check in handleDragEnd
        // Just provide visual feedback for other moves
        if (overColumn.id !== 'in_progress') {
          setTaskList((tasks) =>
            tasks.map((task) =>
              task.id === activeId ? { ...task, status: overColumn.id } : task
            )
          );
        }
      }
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeTask = taskList.find((t) => t.id === active.id);
    if (!activeTask) return;

    // Check if dropped on a column
    const overColumn = columns.find((col) => col.id === over.id);
    if (!overColumn || activeTask.status === overColumn.id) {
      // Reset to original position if dropped in same column
      setTaskList(tasks);
      return;
    }

    // Special handling for moving TO in_progress
    if (overColumn.id === 'in_progress') {
      // Check if we have available agents
      if (availableAgentsCount === 0) {
        setShowWIPModal(true);
        setTaskList(tasks); // Reset
        return;
      }

      // Check if moving from in_review (requires feedback)
      if (activeTask.status === 'in_review') {
        setPendingTask(activeTask);
        setPendingStatus(overColumn.id);
        setShowFeedbackModal(true);
        setTaskList(tasks); // Reset
        return;
      }
    }

    // Update the task status
    setTaskList((tasks) =>
      tasks.map((task) =>
        task.id === activeTask.id ? { ...task, status: overColumn.id } : task
      )
    );
    onTaskUpdate?.(activeTask.id, overColumn.id);
  };

  const handleDragCancel = () => {
    setActiveId(null);
    setTaskList(tasks); // Reset to original
  };

  const handleFeedbackSubmit = (feedback: string) => {
    if (pendingTask && pendingStatus) {
      setTaskList((tasks) =>
        tasks.map((task) =>
          task.id === pendingTask.id ? { ...task, status: pendingStatus } : task
        )
      );
      onTaskUpdate?.(pendingTask.id, pendingStatus, feedback);
    }
    setShowFeedbackModal(false);
    setPendingTask(null);
    setPendingStatus(null);
  };

  const getTasksByStatus = (status: TaskStatus) => {
    return taskList.filter((task) => task.status === status);
  };

  const activeTask = activeId ? taskList.find((t) => t.id === activeId) : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {columns.map((column, columnIndex) => {
          const columnTasks = getTasksByStatus(column.id);

          return (
            <motion.div
              key={column.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: 0.4,
                delay: columnIndex * 0.1,
                ease: [0.22, 1, 0.36, 1],
              }}
            >
              <DroppableColumn
                id={column.id}
                className={`flex flex-col rounded-xl border-2 ${column.color} overflow-hidden transition-all duration-200`}
              >
                {/* Column Header */}
                <div className="p-4 border-b bg-background/50 backdrop-blur-sm">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold">{column.title}</h3>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {columnTasks.length} task{columnTasks.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Tasks */}
                <div className="flex-1 p-4 space-y-3 min-h-[400px]">
                  <AnimatePresence mode="popLayout">
                    {columnTasks.map((task, index) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        index={index}
                      />
                    ))}
                  </AnimatePresence>

                  {columnTasks.length === 0 && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex items-center justify-center h-32 text-sm text-muted-foreground rounded-lg border-2 border-dashed"
                    >
                      Drop tasks here
                    </motion.div>
                  )}
                </div>
              </DroppableColumn>
            </motion.div>
          );
        })}
      </div>

      <DragOverlay>
        {activeTask ? (
          <div className="opacity-90 rotate-3 scale-105">
            <TaskCard task={activeTask} index={0} />
          </div>
        ) : null}
      </DragOverlay>

      {/* Modals */}
      <WIPLimitModal
        isOpen={showWIPModal}
        onClose={() => setShowWIPModal(false)}
        availableAgents={availableAgentsCount}
        tasksInProgress={tasksInProgress}
      />

      <ReviewFeedbackModal
        isOpen={showFeedbackModal}
        onClose={() => {
          setShowFeedbackModal(false);
          setPendingTask(null);
          setPendingStatus(null);
        }}
        onSubmit={handleFeedbackSubmit}
        taskTitle={pendingTask?.title || ''}
        hasAvailableAgents={availableAgentsCount > 0}
      />
    </DndContext>
  );
}
