/**
 * Chat Page
 *
 * Chat interface with agents
 */

'use client';

import { motion } from 'framer-motion';
import { MessageSquare } from 'lucide-react';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { useSearchParams } from 'next/navigation';

export default function ChatPage() {
  const searchParams = useSearchParams();
  const squadId = searchParams.get('squadId') || 'default-squad-id'; // Fallback or get from context

  return (
    <div className="space-y-6 h-full flex flex-col">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="flex items-center gap-3">
          <MessageSquare className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold tracking-tight text-foreground">
            Squad Chat
          </h1>
        </div>
        <p className="mt-2 text-sm text-muted-foreground">
          Real-time collaboration between your agents
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2, duration: 0.5 }}
        className="flex-1"
      >
        <ChatInterface squadId={squadId} />
      </motion.div>
    </div>
  );
}
