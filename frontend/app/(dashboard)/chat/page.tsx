/**
 * Chat Page
 *
 * Chat interface with agents
 */

'use client';

import { motion } from 'framer-motion';
import { MessageSquare } from 'lucide-react';

export default function ChatPage() {
  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="flex items-center gap-3">
          <MessageSquare className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Chat
          </h1>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Communicate with your agents
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="flex min-h-[400px] items-center justify-center rounded-xl border-2 border-dashed border-border bg-muted/30"
      >
        <div className="text-center">
          <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground" />
          <h3 className="mt-4 text-lg font-semibold text-foreground">
            Chat content coming soon
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            This page will show the chat interface
          </p>
        </div>
      </motion.div>
    </div>
  );
}
