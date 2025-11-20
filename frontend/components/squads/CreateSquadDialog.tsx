'use client';

import { useState } from 'react';
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
import { squadsAPI } from '@/lib/api/squads';
import { useAuthStore } from '@/lib/store/auth';
import { handleApiError } from '@/lib/api/client';

const squadSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  description: z.string().optional(),
  squad_type: z.string().min(1, 'Squad type is required'),
});

type SquadFormData = z.infer<typeof squadSchema>;

const SQUAD_TYPES = [
  { value: 'development', label: 'Development Team' },
  { value: 'qa', label: 'QA Team' },
  { value: 'devops', label: 'DevOps Team' },
  { value: 'design', label: 'Design Team' },
  { value: 'custom', label: 'Custom Squad' },
];

interface CreateSquadDialogProps {
  onSuccess?: () => void;
  trigger?: React.ReactNode;
}

export function CreateSquadDialog({ onSuccess, trigger }: CreateSquadDialogProps) {
  const router = useRouter();
  const { toast } = useToast();
  const user = useAuthStore((state) => state.user);
  const [open, setOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
    reset,
  } = useForm<SquadFormData>({
    resolver: zodResolver(squadSchema),
  });

  const onSubmit = async (data: SquadFormData) => {
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
      const squad = await squadsAPI.createSquad({
        ...data,
        organization_id: user.organization_id,
      });

      toast({
        title: 'Squad created',
        description: `${squad.name} has been created successfully.`,
      });

      setOpen(false);
      reset();
      
      if (onSuccess) {
        onSuccess();
      } else {
        router.push(`/squads/${squad.id}`);
      }
    } catch (error) {
      toast({
        title: 'Failed to create squad',
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
        {trigger || <Button>Create Squad</Button>}
      </DialogTrigger>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Create New Squad</DialogTitle>
          <DialogDescription>
            Create a new AI agent squad. Add agents after creation.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Squad Name</Label>
            <Input
              id="name"
              placeholder="Backend Development Squad"
              {...register('name')}
              disabled={isLoading}
            />
            {errors.name && (
              <p className="text-sm text-red-500">{errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="squad_type">Squad Type</Label>
            <Select
              onValueChange={(value) => setValue('squad_type', value)}
              disabled={isLoading}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select squad type" />
              </SelectTrigger>
              <SelectContent>
                {SQUAD_TYPES.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.squad_type && (
              <p className="text-sm text-red-500">{errors.squad_type.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              placeholder="Describe the squad's purpose..."
              rows={3}
              {...register('description')}
              disabled={isLoading}
            />
            {errors.description && (
              <p className="text-sm text-red-500">{errors.description.message}</p>
            )}
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
              {isLoading ? 'Creating...' : 'Create Squad'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
