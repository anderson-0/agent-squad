'use client';

import { motion } from 'framer-motion';
import {
  Play,
  Brain,
  MessageCircle,
  Code,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  FileText,
  Edit,
  TestTube,
  XCircle,
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AgentAvatar } from '@/components/squads/AgentAvatar';
import type { AgentActivity } from '@/types/agent-activity';
import type { Agent } from '@/types/squad';

interface ActivityCardProps {
  activity: AgentActivity;
  index: number;
}

const activityConfig = {
  task_started: {
    icon: Play,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50 dark:bg-blue-950/20',
    borderColor: 'border-blue-200',
    label: 'Started Task',
  },
  thinking: {
    icon: Brain,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50 dark:bg-purple-950/20',
    borderColor: 'border-purple-200',
    label: 'Thinking',
  },
  message: {
    icon: MessageCircle,
    color: 'text-green-600',
    bgColor: 'bg-green-50 dark:bg-green-950/20',
    borderColor: 'border-green-200',
    label: 'Message',
  },
  code_change: {
    icon: Code,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50 dark:bg-indigo-950/20',
    borderColor: 'border-indigo-200',
    label: 'Code Change',
  },
  task_completed: {
    icon: CheckCircle2,
    color: 'text-emerald-600',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/20',
    borderColor: 'border-emerald-200',
    label: 'Completed',
  },
  error: {
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50 dark:bg-red-950/20',
    borderColor: 'border-red-200',
    label: 'Error',
  },
  question: {
    icon: HelpCircle,
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50 dark:bg-yellow-950/20',
    borderColor: 'border-yellow-200',
    label: 'Question',
  },
  file_created: {
    icon: FileText,
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-50 dark:bg-cyan-950/20',
    borderColor: 'border-cyan-200',
    label: 'File Created',
  },
  file_modified: {
    icon: Edit,
    color: 'text-orange-600',
    bgColor: 'bg-orange-50 dark:bg-orange-950/20',
    borderColor: 'border-orange-200',
    label: 'File Modified',
  },
  test_passed: {
    icon: TestTube,
    color: 'text-green-600',
    bgColor: 'bg-green-50 dark:bg-green-950/20',
    borderColor: 'border-green-200',
    label: 'Tests Passed',
  },
  test_failed: {
    icon: XCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-50 dark:bg-red-950/20',
    borderColor: 'border-red-200',
    label: 'Tests Failed',
  },
};

export function ActivityCard({ activity, index }: ActivityCardProps) {
  const config = activityConfig[activity.type];
  const Icon = config.icon;

  // Format timestamp
  const timestamp = new Date(activity.timestamp);
  const now = new Date();
  const diffMs = now.getTime() - timestamp.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const timeAgo =
    diffMins < 1
      ? 'Just now'
      : diffMins < 60
      ? `${diffMins}m ago`
      : `${Math.floor(diffMins / 60)}h ago`;

  // Create mock agent for avatar
  const mockAgent: Agent = {
    id: activity.agent_id,
    name: activity.agent_name,
    role: activity.agent_role,
    status: activity.type === 'thinking' ? 'thinking' : activity.type === 'task_completed' ? 'completed' : 'working',
    stats: {
      tasks_completed: 0,
      success_rate: 0,
      total_time_hours: 0,
    },
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        duration: 0.4,
        delay: index * 0.05,
        ease: [0.22, 1, 0.36, 1],
      }}
    >
      <Card className={`p-4 ${config.bgColor} border ${config.borderColor}`}>
        <div className="flex items-start gap-3">
          {/* Agent Avatar */}
          <AgentAvatar agent={mockAgent} size="sm" showStatus index={0} />

          <div className="flex-1 min-w-0">
            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
              <Icon className={`h-4 w-4 ${config.color}`} />
              <span className="text-sm font-semibold">{activity.agent_name}</span>
              <Badge variant="outline" className="text-xs">
                {config.label}
              </Badge>
              <span className="text-xs text-muted-foreground ml-auto">
                {timeAgo}
              </span>
            </div>

            {/* Message/Content */}
            {activity.message && (
              <p className="text-sm text-foreground mb-2">
                {activity.message.split('@').map((part, i) => {
                  if (i === 0) return part;
                  const [mention, ...rest] = part.split(' ');
                  return (
                    <span key={i}>
                      <span className="font-semibold text-blue-600">@{mention}</span>
                      {rest.length > 0 && ' ' + rest.join(' ')}
                    </span>
                  );
                })}
              </p>
            )}

            {/* Task Info */}
            {activity.task && (
              <div className="text-sm text-muted-foreground mb-2">
                Task: <span className="font-medium">{activity.task.title}</span>
              </div>
            )}

            {/* Code Change Preview */}
            {activity.code_change && (
              <div className="mt-2 p-3 rounded-md bg-background/50 border">
                <div className="flex items-center justify-between mb-2">
                  <code className="text-xs font-mono text-muted-foreground">
                    {activity.code_change.file_path}
                  </code>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-green-600">
                      +{activity.code_change.additions}
                    </span>
                    <span className="text-red-600">
                      -{activity.code_change.deletions}
                    </span>
                  </div>
                </div>
                {activity.code_change.preview && (
                  <pre className="text-xs overflow-x-auto">
                    <code>{activity.code_change.preview}</code>
                  </pre>
                )}
              </div>
            )}

            {/* Test Results */}
            {activity.metadata?.tests_passed !== undefined && (
              <div className="mt-2 flex items-center gap-4 text-sm">
                <span className="text-green-600">
                  ✓ {activity.metadata.tests_passed} passed
                </span>
                {activity.metadata.tests_failed > 0 && (
                  <span className="text-red-600">
                    ✗ {activity.metadata.tests_failed} failed
                  </span>
                )}
                <span className="text-muted-foreground text-xs">
                  {activity.metadata.duration_ms}ms
                </span>
              </div>
            )}

            {/* Task Completion Stats */}
            {activity.type === 'task_completed' && activity.metadata && (
              <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                {activity.metadata.files_changed && (
                  <span>{activity.metadata.files_changed} files changed</span>
                )}
                {activity.metadata.lines_added && (
                  <span className="text-green-600">
                    +{activity.metadata.lines_added}
                  </span>
                )}
                {activity.metadata.lines_deleted && (
                  <span className="text-red-600">
                    -{activity.metadata.lines_deleted}
                  </span>
                )}
                {activity.metadata.duration_hours && (
                  <span>{activity.metadata.duration_hours}h duration</span>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
