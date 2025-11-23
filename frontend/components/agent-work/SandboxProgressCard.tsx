'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Box, Play, CheckCircle2, XCircle, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { GitWorkflowStepper } from './GitWorkflowStepper'
import { PRLinkBadge } from './PRLinkBadge'
import {
  SandboxProgress,
  GitWorkflowStep,
  SandboxEvent,
  GitOperationEvent,
  PRCreatedEvent,
} from '@/types/sandbox'

interface SandboxProgressCardProps {
  sandboxId: string
  initialProgress?: SandboxProgress
  onEvent?: (event: SandboxEvent) => void
}

const statusConfig = {
  CREATED: { color: 'bg-gray-100 text-gray-700', icon: Clock, label: 'Created' },
  RUNNING: { color: 'bg-blue-100 text-blue-700', icon: Play, label: 'Running' },
  TERMINATED: { color: 'bg-green-100 text-green-700', icon: CheckCircle2, label: 'Completed' },
  ERROR: { color: 'bg-red-100 text-red-700', icon: XCircle, label: 'Error' },
}

export function SandboxProgressCard({
  sandboxId,
  initialProgress,
  onEvent,
}: SandboxProgressCardProps) {
  const [progress, setProgress] = useState<SandboxProgress>(
    initialProgress || {
      sandbox_id: sandboxId,
      e2b_id: '',
      status: 'CREATED',
      workflow_steps: [
        { id: 'clone', label: 'Clone Repo', status: 'pending' },
        { id: 'create_branch', label: 'Create Branch', status: 'pending' },
        { id: 'commit', label: 'Commit Changes', status: 'pending' },
        { id: 'push', label: 'Push to Remote', status: 'pending' },
      ],
      created_at: new Date().toISOString(),
      last_updated: new Date().toISOString(),
    }
  )

  const [isExpanded, setIsExpanded] = useState(true)
  const [showConfetti, setShowConfetti] = useState(false)

  const config = statusConfig[progress.status]
  const Icon = config.icon

  const handleEvent = (event: SandboxEvent) => {
    if (event.sandbox_id !== sandboxId) return

    // Call parent handler
    if (onEvent) onEvent(event)

    setProgress((prev) => {
      const newProgress = { ...prev, last_updated: event.timestamp }

      switch (event.event) {
        case 'sandbox_created':
          newProgress.e2b_id = event.e2b_id
          newProgress.status = 'RUNNING'
          newProgress.repo_url = event.repo_url
          break

        case 'git_operation': {
          const gitEvent = event as GitOperationEvent
          const stepIndex = prev.workflow_steps.findIndex((s) => s.id === gitEvent.operation)

          if (stepIndex !== -1) {
            const newSteps = [...prev.workflow_steps]
            newSteps[stepIndex] = {
              ...newSteps[stepIndex],
              status:
                gitEvent.status === 'started'
                  ? 'in_progress'
                  : gitEvent.status === 'completed'
                  ? 'completed'
                  : 'failed',
              output: gitEvent.output,
              error: gitEvent.error,
              timestamp: gitEvent.timestamp,
            }
            newProgress.workflow_steps = newSteps
            newProgress.current_operation = gitEvent.operation
          }
          break
        }

        case 'pr_created': {
          const prEvent = event as PRCreatedEvent
          newProgress.pr = {
            number: prEvent.pr_number,
            url: prEvent.pr_url,
            title: prEvent.pr_title,
            head_branch: prEvent.head_branch,
            base_branch: prEvent.base_branch,
            status: 'open',
          }
          // Trigger confetti
          setShowConfetti(true)
          setTimeout(() => setShowConfetti(false), 3000)
          break
        }

        case 'pr_approved': {
          const approvedEvent = event as any
          if (newProgress.pr) {
            newProgress.pr = {
              ...newProgress.pr,
              status: 'approved',
              reviewer: approvedEvent.reviewer,
            }
          }
          break
        }

        case 'pr_merged': {
          const mergedEvent = event as any
          if (newProgress.pr) {
            newProgress.pr = {
              ...newProgress.pr,
              status: 'merged',
              merged_by: mergedEvent.merged_by,
            }
          }
          // Trigger confetti for merge
          setShowConfetti(true)
          setTimeout(() => setShowConfetti(false), 3000)
          break
        }

        case 'pr_closed': {
          const closedEvent = event as any
          if (newProgress.pr) {
            newProgress.pr = {
              ...newProgress.pr,
              status: 'closed',
              closed_by: closedEvent.closed_by,
            }
          }
          break
        }

        case 'pr_reopened': {
          if (newProgress.pr) {
            newProgress.pr = {
              ...newProgress.pr,
              status: 'open',
            }
          }
          break
        }

        case 'sandbox_terminated':
          newProgress.status = 'TERMINATED'
          newProgress.runtime_seconds = event.runtime_seconds
          break

        case 'sandbox_error':
          newProgress.status = 'ERROR'
          break
      }

      return newProgress
    })
  }

  // Format runtime
  const formatRuntime = (seconds?: number) => {
    if (!seconds) return null
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }

  return (
    <Card className="overflow-hidden">
      <CardHeader
        className="cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              <Box className="w-5 h-5 text-gray-700" />
            </div>

            <div>
              <CardTitle className="text-base mb-2">E2B Sandbox</CardTitle>

              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className={config.color}>
                  <Icon className="w-3 h-3 mr-1" />
                  {config.label}
                </Badge>

                {progress.runtime_seconds && (
                  <Badge variant="outline" className="text-xs">
                    <Clock className="w-3 h-3 mr-1" />
                    {formatRuntime(progress.runtime_seconds)}
                  </Badge>
                )}
              </div>

              {progress.e2b_id && (
                <div className="text-xs text-gray-500 font-mono">ID: {progress.e2b_id.slice(0, 12)}...</div>
              )}
            </div>
          </div>

          <button
            className="p-1 hover:bg-gray-200 rounded transition-colors"
            onClick={(e) => {
              e.stopPropagation()
              setIsExpanded(!isExpanded)
            }}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>
        </div>
      </CardHeader>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
          >
            <CardContent className="space-y-4">
              {/* Repository URL */}
              {progress.repo_url && (
                <div className="text-sm">
                  <span className="text-gray-500">Repository:</span>
                  <div className="font-mono text-xs mt-1 p-2 bg-gray-50 rounded">
                    {progress.repo_url}
                  </div>
                </div>
              )}

              {/* Git Workflow Stepper */}
              <div className="py-4">
                <GitWorkflowStepper steps={progress.workflow_steps} />
              </div>

              {/* Pull Request */}
              {progress.pr && (
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-2">Pull Request</div>
                  <PRLinkBadge
                    pr_number={progress.pr.number}
                    pr_url={progress.pr.url}
                    pr_title={progress.pr.title}
                    head_branch={progress.pr.head_branch}
                    base_branch={progress.pr.base_branch}
                    status={progress.pr.status || 'open'}
                    showConfetti={showConfetti}
                  />
                </div>
              )}

              {/* Timestamps */}
              <div className="text-xs text-gray-500 flex gap-4">
                <div>
                  <span className="font-medium">Created:</span>{' '}
                  {new Date(progress.created_at).toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Updated:</span>{' '}
                  {new Date(progress.last_updated).toLocaleString()}
                </div>
              </div>
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  )
}
