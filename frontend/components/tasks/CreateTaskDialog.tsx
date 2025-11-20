'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/lib/hooks/use-toast';
import { tasksAPI } from '@/lib/api/tasks';
import { squadsAPI } from '@/lib/api/squads';
import { useAuthStore } from '@/lib/store/auth';
import { handleApiError } from '@/lib/api/client';
import { Squad } from '@/lib/api/types';

const taskSchema = z.object({
  title: z.string().min(3, 'Title must be at least 3 characters'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  task_type: z.string().min(1, 'Task type is required'),
  priority: z.enum(['low', 'medium', 'high', 'urgent']),
  squad_id: z.string().optional(),
});

type TaskFormData = z.infer<typeof taskSchema>;

const TASK_TYPES = [
  { value: 'feature', label: 'Feature Development' },
  { value: 'bug', label: 'Bug Fix' },
  { value: 'refactor', label: 'Refactoring' },
  { value: 'documentation', label: 'Documentation' },
  { value: 'testing', label: 'Testing' },
  { value: 'devops', label: 'DevOps' },
];

const PRIORITIES = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
];

interface CreateTaskDialogProps {
  onSuccess?: () => void;
  trigger?: React.ReactNode;
}

export function CreateTaskDialog({ onSuccess, trigger }: CreateTaskDialogProps) {
  const router = useRouter();
  const { toast } = useToast();
  const user = useAuthStore((state) => state.user);
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [squads, setSquads] = useState<Squad[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    reset,
  } = useForm<TaskFormData>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      priority: 'medium',
    },
  });

  // Fetch squads for assignment
  useEffect(() => {
    const fetchSquads = async () => {
      if (!user?.organization_id) return;
      
      try {
        const data = await squadsAPI.listSquads(user.organization_id, 1, 100);
        setSquads(data.items);
      } catch (error) {
        console.error('Failed to fetch squads:', error);
      }
    };

    if (open) {
      fetchSquads();
    }
  }, [open, user]);

  const onSubmit = async (data: TaskFormData) => {
    if (!user?.organization_id) {
      toast({
        title: 'Error',
        description: 'No organization found',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    try {
      const task = await tasksAPI.createTask({
        ...data,
        organization_id: user.organization_id,
      });

      toast({
        title: 'Task created',
        description: `${task.title} has been created successfully.`,
      });

      setOpen(false);
      reset();
      
      if (onSuccess) {
        onSuccess();
      } else {
        router.push(`/tasks/${task.id}`);
      }
    } catch (error) {
      toast({
        title: 'Failed to create task',
        description: handleApiError(error),
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || <Button>Create Task</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Create New Task</DialogTitle>
          <DialogDescription>
            Create a new task and optionally assign it to a squad.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="title">Task Title</Label>
            <Input
              id="title"
              placeholder="Implement user authentication"
              {...register('title')}
              disabled={isLoading}
            />
            {errors.title && (
              <p className="text-sm text-red-500">{errors.title.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe the task in detail..."
              rows={4}
              {...register('description')}
              disabled={isLoading}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description.message}</p>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="task_type">Task Type</Label>
              <Select
                onValueChange={(value) => setValue('task_type', value)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {TASK_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.task_type && (
                <p className="text-sm text-red-500">{errors.task_type.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Select
                onValueChange={(value) => setValue('priority', value as any)}
                defaultValue="medium"
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select priority" />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITIES.map((priority) => (
                    <SelectItem key={priority.value} value={priority.value}>
                      {priority.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.priority && (
                <p className="text-sm text-red-500">{errors.priority.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="squad_id">Assign to Squad (Optional)</Label>
            <Select
              onValueChange={(value) => setValue('squad_id', value)}
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue placeholder="No squad assigned" />
              </SelectTrigger>
              <SelectContent>
                {squads.map((squad) => (
                  <SelectItem key={squad.id} value={squad.id}>
                    {squad.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create Task'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
