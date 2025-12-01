'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import {
  Users,
  CheckCircle2,
  Clock,
  TrendingUp,
  Zap,
  Pause,
  Play
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { Squad } from '@/types/squad';
import { AgentAvatar } from './AgentAvatar';

interface SquadCardProps {
  squad: Squad;
  index: number;
}

export function SquadCard({ squad, index }: SquadCardProps) {
  const router = useRouter();

  const completedTasks = squad.tasks.filter((t) => t.status === 'done').length;
  const totalTasks = squad.tasks.length;
  const activeAgents = squad.agents.filter((a) => a.status === 'working' || a.status === 'thinking').length;

  // Calculate time since last update
  const lastUpdate = new Date(squad.updated_at);
  const now = new Date();
  const hoursAgo = Math.floor((now.getTime() - lastUpdate.getTime()) / (1000 * 60 * 60));

  const getStatusConfig = (status: Squad['status']) => {
    switch (status) {
      case 'active':
        return {
          label: 'Active',
          icon: Play,
          color: 'text-green-500',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/20',
        };
      case 'paused':
        return {
          label: 'Paused',
          icon: Pause,
          color: 'text-yellow-500',
          bgColor: 'bg-yellow-500/10',
          borderColor: 'border-yellow-500/20',
        };
      case 'completed':
        return {
          label: 'Completed',
          icon: CheckCircle2,
          color: 'text-blue-500',
          bgColor: 'bg-blue-500/10',
          borderColor: 'border-blue-500/20',
        };
    }
  };

  const statusConfig = getStatusConfig(squad.status);
  const StatusIcon = statusConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        duration: 0.4,
        delay: index * 0.1,
        ease: [0.22, 1, 0.36, 1],
      }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
    >
      <Card
        className="relative overflow-hidden cursor-pointer group"
        onClick={() => router.push(`/squads/${squad.id}`)}
      >
        {/* Hover gradient overlay */}
        <motion.div
          className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
          initial={false}
        />

        {/* Status indicator bar */}
        <div className={`h-1 ${statusConfig.bgColor}`}>
          <motion.div
            className={`h-full bg-gradient-to-r ${statusConfig.color.replace('text', 'from')} to-purple-500`}
            initial={{ width: 0 }}
            animate={{ width: `${squad.progress}%` }}
            transition={{ duration: 1, delay: index * 0.1 + 0.3, ease: 'easeOut' }}
          />
        </div>

        <div className="p-6 space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold truncate group-hover:text-blue-600 transition-colors">
                {squad.name}
              </h3>
              <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                {squad.description}
              </p>
            </div>

            <Badge
              variant="outline"
              className={`${statusConfig.bgColor} ${statusConfig.borderColor} ${statusConfig.color} shrink-0`}
            >
              <StatusIcon className="w-3 h-3 mr-1" />
              {statusConfig.label}
            </Badge>
          </div>

          {/* Progress Ring and Level */}
          <div className="flex items-center justify-between">
            {/* Circular Progress */}
            <div className="relative">
              <svg className="w-20 h-20 -rotate-90">
                {/* Background circle */}
                <circle
                  cx="40"
                  cy="40"
                  r="32"
                  stroke="currentColor"
                  strokeWidth="6"
                  fill="none"
                  className="text-muted/20"
                />
                {/* Progress circle */}
                <motion.circle
                  cx="40"
                  cy="40"
                  r="32"
                  stroke="url(#gradient)"
                  strokeWidth="6"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 32}`}
                  initial={{ strokeDashoffset: 2 * Math.PI * 32 }}
                  animate={{
                    strokeDashoffset: 2 * Math.PI * 32 * (1 - squad.progress / 100),
                  }}
                  transition={{ duration: 1.5, delay: index * 0.1 + 0.2, ease: 'easeOut' }}
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#3b82f6" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>

              {/* Progress text */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <motion.span
                  className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: index * 0.1 + 0.5 }}
                >
                  {squad.progress}%
                </motion.span>
              </div>
            </div>

            {/* Level Badge with Animation */}
            <motion.div
              className="flex flex-col items-end gap-2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: index * 0.1 + 0.4 }}
            >
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-500" />
                <span className="text-sm font-medium text-muted-foreground">
                  Level {squad.level}
                </span>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground">XP</div>
                <div className="text-sm font-semibold">{squad.xp.toLocaleString()}</div>
              </div>
            </motion.div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-3 pt-3 border-t">
            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span className="text-xs">Tasks</span>
              </div>
              <div className="text-sm font-semibold">
                {completedTasks}/{totalTasks}
              </div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <Users className="w-3.5 h-3.5" />
                <span className="text-xs">Agents</span>
              </div>
              <div className="text-sm font-semibold">
                {activeAgents}/{squad.agents.length}
              </div>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
                <Clock className="w-3.5 h-3.5" />
                <span className="text-xs">Updated</span>
              </div>
              <div className="text-xs font-semibold">
                {hoursAgo < 1 ? 'Just now' : `${hoursAgo}h ago`}
              </div>
            </div>
          </div>

          {/* Agent Avatars */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex -space-x-2">
              {squad.agents.slice(0, 4).map((agent, i) => (
                <AgentAvatar
                  key={agent.id}
                  agent={agent}
                  size="sm"
                  index={i}
                />
              ))}
              {squad.agents.length > 4 && (
                <div className="w-8 h-8 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs font-medium">
                  +{squad.agents.length - 4}
                </div>
              )}
            </div>

            {squad.achievements.length > 0 && (
              <motion.div
                className="flex items-center gap-1"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{
                  duration: 0.5,
                  delay: index * 0.1 + 0.7,
                  type: 'spring',
                  stiffness: 200,
                }}
              >
                <TrendingUp className="w-3.5 h-3.5 text-yellow-500" />
                <span className="text-xs font-medium text-muted-foreground">
                  {squad.achievements.length} achievement{squad.achievements.length !== 1 ? 's' : ''}
                </span>
              </motion.div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
}
