'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  Search,
  CheckCircle,
  Zap,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { AgentThought } from '@/types/agent-activity';

interface ThoughtCardProps {
  thought: AgentThought;
  index: number;
}

const thoughtTypeConfig = {
  planning: {
    icon: Lightbulb,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/20',
    borderColor: 'border-yellow-300',
    label: 'Planning',
  },
  analyzing: {
    icon: Search,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950/20',
    borderColor: 'border-blue-300',
    label: 'Analyzing',
  },
  deciding: {
    icon: CheckCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50 dark:bg-green-950/20',
    borderColor: 'border-green-300',
    label: 'Deciding',
  },
  executing: {
    icon: Zap,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-950/20',
    borderColor: 'border-purple-300',
    label: 'Executing',
  },
};

export function ThoughtCard({ thought, index }: ThoughtCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const config = thoughtTypeConfig[thought.type];
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 0.4,
        delay: index * 0.1,
        ease: [0.22, 1, 0.36, 1],
      }}
    >
      <Card className={`overflow-hidden ${config.bgColor} border-2 ${config.borderColor}`}>
        {/* Header */}
        <div
          className="p-4 cursor-pointer hover:bg-background/50 transition-colors"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-start gap-3">
            <motion.div
              animate={
                isExpanded
                  ? {}
                  : {
                      rotate: [0, 5, -5, 0],
                    }
              }
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            >
              <Brain className={`h-5 w-5 ${config.color}`} />
            </motion.div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold text-sm">{thought.agent_name}</span>
                <Badge variant="outline" className={`text-xs ${config.color}`}>
                  <Icon className="h-3 w-3 mr-1" />
                  {config.label}
                </Badge>
                {thought.duration_ms && (
                  <span className="text-xs text-muted-foreground ml-auto">
                    {(thought.duration_ms / 1000).toFixed(1)}s
                  </span>
                )}
              </div>

              <p className="text-sm text-foreground">{thought.content}</p>
            </div>

            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 shrink-0"
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
            >
              {isExpanded ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Expanded Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-4 space-y-4 border-t bg-background/30">
                {/* Reasoning Steps */}
                {thought.reasoning_steps && thought.reasoning_steps.length > 0 && (
                  <div className="pt-4">
                    <h4 className="text-xs font-semibold text-muted-foreground mb-3">
                      Reasoning Steps:
                    </h4>
                    <div className="space-y-2">
                      {thought.reasoning_steps.map((step, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{
                            duration: 0.3,
                            delay: i * 0.1,
                          }}
                          className="flex items-start gap-2"
                        >
                          <div className={`flex items-center justify-center h-6 w-6 rounded-full ${config.bgColor} border ${config.borderColor} shrink-0 text-xs font-semibold ${config.color}`}>
                            {i + 1}
                          </div>
                          <p className="text-sm text-foreground pt-0.5">{step}</p>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Decision */}
                {thought.decision && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.3 }}
                    className="p-3 rounded-md bg-background border"
                  >
                    <div className="flex items-start gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600 shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-xs font-semibold text-muted-foreground mb-1">
                          Decision:
                        </h4>
                        <p className="text-sm text-foreground">{thought.decision}</p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>
    </motion.div>
  );
}
