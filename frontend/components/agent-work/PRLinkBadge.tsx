'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { ExternalLink, GitPullRequest, Check, Clock, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import Confetti from 'react-confetti-boom'

interface PRLinkBadgeProps {
  pr_number: number
  pr_url: string
  pr_title: string
  head_branch: string
  base_branch: string
  status?: 'open' | 'merged' | 'closed' | 'approved'
  showConfetti?: boolean
}

const statusConfig = {
  open: {
    color: 'bg-blue-100 text-blue-700 border-blue-300',
    icon: Clock,
    label: 'Open',
  },
  approved: {
    color: 'bg-green-100 text-green-700 border-green-300',
    icon: Check,
    label: 'Approved',
  },
  merged: {
    color: 'bg-purple-100 text-purple-700 border-purple-300',
    icon: Check,
    label: 'Merged',
  },
  closed: {
    color: 'bg-gray-100 text-gray-700 border-gray-300',
    icon: X,
    label: 'Closed',
  },
}

export function PRLinkBadge({
  pr_number,
  pr_url,
  pr_title,
  head_branch,
  base_branch,
  status = 'open',
  showConfetti = false,
}: PRLinkBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <>
      {showConfetti && (
        <Confetti
          mode="boom"
          particleCount={50}
          spreadDeg={60}
          shapeSize={8}
          colors={['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b']}
        />
      )}

      <motion.a
        href={pr_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block group"
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        whileHover={{ scale: 1.02 }}
        transition={{ duration: 0.2 }}
      >
        <div
          className={`
            flex items-start gap-3 p-4 rounded-lg border-2
            ${config.color}
            transition-all duration-200
            hover:shadow-md
          `}
        >
          {/* PR Icon */}
          <div className="flex-shrink-0 mt-0.5">
            <GitPullRequest className="w-5 h-5" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-semibold">PR #{pr_number}</span>
              <Badge variant="outline" className={`text-xs ${config.color}`}>
                <Icon className="w-3 h-3 mr-1" />
                {config.label}
              </Badge>
            </div>

            <h4 className="text-sm font-medium mb-2 line-clamp-2 group-hover:underline">
              {pr_title}
            </h4>

            <div className="flex items-center gap-2 text-xs text-gray-600">
              <span className="font-mono bg-white/50 px-2 py-0.5 rounded">
                {head_branch}
              </span>
              <span>→</span>
              <span className="font-mono bg-white/50 px-2 py-0.5 rounded">
                {base_branch}
              </span>
            </div>
          </div>

          {/* External link icon */}
          <div className="flex-shrink-0">
            <ExternalLink className="w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </motion.a>
    </>
  )
}
