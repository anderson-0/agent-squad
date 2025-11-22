'use client';

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, CheckCircle2, GitBranch, Github } from 'lucide-react';
import type { Task } from '@/types/squad';

interface TaskDetailsDialogProps {
    task: Task | null;
    isOpen: boolean;
    onClose: () => void;
}

export function TaskDetailsDialog({ task, isOpen, onClose }: TaskDetailsDialogProps) {
    if (!task) return null;

    const priorityColors = {
        low: 'bg-gray-100 text-gray-800 border-gray-200',
        medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        high: 'bg-red-100 text-red-800 border-red-200',
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <div className="flex items-center justify-between gap-4 pr-8">
                        <DialogTitle className="text-xl">{task.title}</DialogTitle>
                        <Badge variant="outline" className={priorityColors[task.priority]}>
                            {task.priority}
                        </Badge>
                    </div>
                    <DialogDescription>
                        Task ID: {task.id}
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-6 py-4">
                    {/* Description */}
                    <div className="space-y-2">
                        <h4 className="font-medium leading-none">Description</h4>
                        <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                            {task.description}
                        </p>
                    </div>

                    {/* Status & Time */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <h4 className="font-medium leading-none">Status</h4>
                            <Badge variant="secondary" className="capitalize">
                                {task.status.replace('_', ' ')}
                            </Badge>
                        </div>
                        <div className="space-y-2">
                            <h4 className="font-medium leading-none">Time Estimate</h4>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <Clock className="h-4 w-4" />
                                {task.time_estimate_hours ? `${task.time_estimate_hours} hours` : 'Not set'}
                            </div>
                        </div>
                    </div>

                    {/* Git Integration */}
                    {(task.git_branch || task.pull_request_url) && (
                        <div className="space-y-3 pt-4 border-t">
                            <h4 className="font-medium leading-none">Git Integration</h4>
                            <div className="flex flex-col gap-2">
                                {task.git_branch && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <GitBranch className="h-4 w-4 text-muted-foreground" />
                                        <span className="font-mono bg-muted px-2 py-1 rounded text-xs">
                                            {task.git_branch}
                                        </span>
                                    </div>
                                )}
                                {task.pull_request_url && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <Github className="h-4 w-4 text-muted-foreground" />
                                        <a
                                            href={task.pull_request_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-blue-600 hover:underline"
                                        >
                                            View Pull Request
                                        </a>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Subtasks */}
                    {task.subtasks && task.subtasks.length > 0 && (
                        <div className="space-y-3 pt-4 border-t">
                            <h4 className="font-medium leading-none">Subtasks</h4>
                            <div className="space-y-2">
                                {task.subtasks.map((subtask) => (
                                    <div key={subtask.id} className="flex items-center gap-2 text-sm">
                                        <CheckCircle2
                                            className={`h-4 w-4 ${subtask.completed ? 'text-green-500' : 'text-muted-foreground'}`}
                                        />
                                        <span className={subtask.completed ? 'line-through text-muted-foreground' : ''}>
                                            {subtask.title}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button onClick={onClose}>Close</Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
