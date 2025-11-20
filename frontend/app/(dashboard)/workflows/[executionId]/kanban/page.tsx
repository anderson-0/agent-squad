/**
 * Kanban Board Page (Stream F)
 * 
 * Page for viewing workflow Kanban board
 */
'use client';

import { useParams } from 'next/navigation';
import { KanbanBoard } from '@/components/kanban/KanbanBoard';

export default function KanbanPage() {
  const params = useParams();
  const executionId = params.executionId as string;

  const handleTaskClick = (taskId: string) => {
    // Navigate to task details page (future enhancement)
    console.log('Task clicked:', taskId);
    // router.push(`/workflows/${executionId}/tasks/${taskId}`);
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <KanbanBoard 
        executionId={executionId}
        onTaskClick={handleTaskClick}
      />
    </div>
  );
}

