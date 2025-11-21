/**
 * Tasks Page
 *
 * View and manage tasks
 */

'use client';

import { motion } from 'framer-motion';
import { ClipboardList } from 'lucide-react';

export default function TasksPage() {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="flex items-center gap-3">
          <ClipboardList className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Tasks
          </h1>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Track and manage all your tasks
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="flex min-h-[400px] items-center justify-center rounded-xl border-2 border-dashed border-border bg-muted/30"
      >
        <div className="text-center">
          <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold text-foreground">
            Tasks content coming soon
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            This page will show your task list
          </p>
        </div>
      </motion.div>
    </div>
  );
}
