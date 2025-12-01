'use client';

import { useState } from 'react';
import { Check, X, AlertTriangle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { axiosInstance } from '@/lib/axios';

interface ApprovalRequestCardProps {
    request: {
        id: string;
        squad_id: string;
        agent_id: string;
        action_type: string;
        payload: any;
        status: 'pending' | 'approved' | 'rejected';
        created_at: string;
    };
    onUpdate: () => void;
}

export function ApprovalRequestCard({ request, onUpdate }: ApprovalRequestCardProps) {
    const [isLoading, setIsLoading] = useState(false);

    const handleAction = async (action: 'approve' | 'reject') => {
        setIsLoading(true);
        try {
            await axiosInstance.post(`/approvals/${request.id}/${action}`);
            onUpdate();
        } catch (error) {
            console.error(`Failed to ${action} request:`, error);
        } finally {
            setIsLoading(false);
        }
    };

    if (request.status !== 'pending') {
        return (
            <Card className={`p-4 border-l-4 ${request.status === 'approved' ? 'border-l-green-500' : 'border-l-red-500'}`}>
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        {request.status === 'approved' ? (
                            <Check className="h-5 w-5 text-green-500" />
                        ) : (
                            <X className="h-5 w-5 text-red-500" />
                        )}
                        <span className="font-medium capitalize">
                            Action {request.status}
                        </span>
                    </div>
                    <span className="text-xs text-muted-foreground">
                        {new Date(request.created_at).toLocaleTimeString()}
                    </span>
                </div>
            </Card>
        );
    }

    return (
        <Card className="p-4 border-l-4 border-l-yellow-500 bg-yellow-50/50 dark:bg-yellow-900/10">
            <div className="flex items-start gap-3">
                <div className="p-2 bg-yellow-100 dark:bg-yellow-900/30 rounded-full">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
                </div>
                <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold text-sm">Approval Required</h4>
                        <Badge variant="outline" className="text-xs border-yellow-200 bg-yellow-100 text-yellow-800">
                            {request.action_type}
                        </Badge>
                    </div>

                    <p className="text-sm text-muted-foreground mb-3">
                        Agent requests permission to perform this action.
                    </p>

                    <div className="bg-background/50 p-3 rounded-md text-xs font-mono mb-4 overflow-x-auto border">
                        <pre>{JSON.stringify(request.payload, null, 2)}</pre>
                    </div>

                    <div className="flex gap-2 justify-end">
                        <Button
                            variant="outline"
                            size="sm"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => handleAction('reject')}
                            disabled={isLoading}
                        >
                            <X className="h-4 w-4 mr-1" />
                            Reject
                        </Button>
                        <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700 text-white"
                            onClick={() => handleAction('approve')}
                            disabled={isLoading}
                        >
                            <Check className="h-4 w-4 mr-1" />
                            Approve
                        </Button>
                    </div>
                </div>
            </div>
        </Card>
    );
}
