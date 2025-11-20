'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, Home, RotateCcw } from 'lucide-react';
import Link from 'next/link';

export default function TasksError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Tasks page error:', error);
  }, [error]);

  return (
    <div className="container mx-auto py-10">
      <Alert variant="destructive" className="max-w-2xl mx-auto">
        <AlertCircle className="h-5 w-5" />
        <AlertTitle className="text-lg font-semibold">
          Error Loading Tasks
        </AlertTitle>
        <AlertDescription className="mt-4 space-y-4">
          <p>
            We encountered an error while loading your tasks. This could be due to:
          </p>
          <ul className="list-disc list-inside space-y-1 text-sm ml-4">
            <li>Network connectivity issues</li>
            <li>Server temporarily unavailable</li>
            <li>Invalid task data</li>
          </ul>
          {error.message && (
            <div className="mt-2 rounded-md bg-destructive/10 p-3">
              <p className="text-xs font-mono text-destructive">
                {error.message}
              </p>
            </div>
          )}
          <div className="flex gap-2 mt-4">
            <Button onClick={reset} size="sm">
              <RotateCcw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/">
                <Home className="mr-2 h-4 w-4" />
                Go to Dashboard
              </Link>
            </Button>
          </div>
        </AlertDescription>
      </Alert>
    </div>
  );
}
