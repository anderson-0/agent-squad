'use client';

import { motion } from 'framer-motion';
import { MessageCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { AgentAvatar } from '@/components/squads/AgentAvatar';
import type { AgentMessage } from '@/types/agent-activity';
import type { Agent } from '@/types/squad';

interface ConversationViewProps {
  messages: AgentMessage[];
}

export function ConversationView({ messages }: ConversationViewProps) {
  if (messages.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <MessageCircle className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-semibold mb-2">No conversations yet</h3>
        <p className="text-sm text-muted-foreground">
          Agent conversations will appear here
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.map((message, index) => {
        // Create mock agent for avatar
        const mockAgent: Agent = {
          id: message.agent_id,
          name: message.agent_name,
          role: message.agent_role,
          status: 'idle',
          stats: {
            tasks_completed: 0,
            success_rate: 0,
            total_time_hours: 0,
          },
        };

        // Format timestamp
        const timestamp = new Date(message.timestamp);
        const timeStr = timestamp.toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        });

        const isReply = !!message.parent_message_id;

        return (
          <motion.div
            key={message.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.4,
              delay: index * 0.1,
              ease: [0.22, 1, 0.36, 1],
            }}
            className={isReply ? 'ml-12' : ''}
          >
            <Card className="p-4">
              <div className="flex items-start gap-3">
                <AgentAvatar agent={mockAgent} size="sm" showStatus={false} index={0} />

                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-sm">{message.agent_name}</span>
                    <span className="text-xs text-muted-foreground">
                      {message.agent_role}
                    </span>
                    <span className="text-xs text-muted-foreground ml-auto">
                      {timeStr}
                    </span>
                  </div>

                  {/* Message Content */}
                  <p className="text-sm text-foreground whitespace-pre-wrap">
                    {message.content.split('@').map((part, i) => {
                      if (i === 0) return part;
                      const [mention, ...rest] = part.split(' ');
                      return (
                        <span key={i}>
                          <span className="font-semibold text-blue-600 bg-blue-50 dark:bg-blue-950/20 px-1 rounded">
                            @{mention}
                          </span>
                          {rest.length > 0 && ' ' + rest.join(' ')}
                        </span>
                      );
                    })}
                  </p>

                  {/* Reply Indicator */}
                  {isReply && (
                    <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                      <svg
                        className="h-3 w-3"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"
                        />
                      </svg>
                      <span>Reply</span>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
