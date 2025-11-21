'use client';

import { motion } from 'framer-motion';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import type { Agent } from '@/types/squad';

interface AgentAvatarProps {
  agent: Agent;
  size?: 'sm' | 'md' | 'lg';
  showStatus?: boolean;
  index?: number;
}

export function AgentAvatar({
  agent,
  size = 'md',
  showStatus = true,
  index = 0,
}: AgentAvatarProps) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
  };

  const statusConfig = {
    idle: {
      color: 'bg-gray-400',
      pulse: false,
      ring: false,
    },
    thinking: {
      color: 'bg-yellow-500',
      pulse: true,
      ring: true,
      ringColor: 'ring-yellow-500/50',
    },
    working: {
      color: 'bg-blue-500',
      pulse: false,
      ring: true,
      ringColor: 'ring-blue-500/50',
    },
    completed: {
      color: 'bg-green-500',
      pulse: false,
      ring: false,
    },
    error: {
      color: 'bg-red-500',
      pulse: true,
      ring: true,
      ringColor: 'ring-red-500/50',
    },
  };

  const config = statusConfig[agent.status];
  const initials = agent.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <motion.div
      className="relative"
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{
        duration: 0.3,
        delay: index * 0.05,
        type: 'spring',
        stiffness: 200,
      }}
    >
      <Avatar
        className={`${sizeClasses[size]} border-2 border-background ${
          config.ring ? `ring-2 ${config.ringColor}` : ''
        }`}
      >
        <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-medium">
          {initials}
        </AvatarFallback>
      </Avatar>

      {/* Status Indicator */}
      {showStatus && (
        <motion.div
          className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-background ${config.color}`}
          animate={
            config.pulse
              ? {
                  scale: [1, 1.2, 1],
                  opacity: [1, 0.7, 1],
                }
              : {}
          }
          transition={
            config.pulse
              ? {
                  duration: 2,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }
              : {}
          }
        />
      )}

      {/* Working Ring Animation */}
      {agent.status === 'working' && (
        <motion.div
          className="absolute inset-0 rounded-full border-2 border-blue-500"
          initial={{ scale: 1, opacity: 0.5 }}
          animate={{ scale: 1.3, opacity: 0 }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      )}
    </motion.div>
  );
}
