'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/lib/hooks/use-toast';
import { tasksAPI } from '@/lib/api/tasks';
import { handleApiError } from '@/lib/api/client';
import { Trash2 } from 'lucide-react';

interface DeleteTaskDialogProps {
  taskId: string;
  taskTitle: string;
  onSuccess?: () => void;
  trigger?: React.ReactNode;
}

export function DeleteTaskDialog({
  taskId,
  taskTitle,
  onSuccess,
  trigger,
}: DeleteTaskDialogProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await tasksAPI.deleteTask(taskId);

      toast({
        title: 'Task deleted',
        description: `${taskTitle} has been deleted successfully.`,
      });

      setOpen(false);

      if (onSuccess) {
        onSuccess();
      } else {
        router.push('/tasks');
      }
    } catch (error) {
      toast({
        title: 'Failed to delete task',
        description: handleApiError(error),
        variant: 'destructive',
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild>
        {trigger || (
          <Button variant="destructive" size="sm">
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        )}
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete the task{' '}
            <strong>{taskTitle}</strong> and all associated execution history.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-red-600 hover:bg-red-700"
          >
            {isDeleting ? 'Deleting...' : 'Delete Task'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
