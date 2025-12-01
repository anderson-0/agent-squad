'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { GitBranch, GitCommit, GitPullRequest, Download, Check, Loader2, X } from 'lucide-react'
import { GitWorkflowStep } from '@/types/sandbox'

interface GitWorkflowStepperProps {
  steps: GitWorkflowStep[]
  className?: string
}

const stepIcons = {
  clone: Download,
  create_branch: GitBranch,
  commit: GitCommit,
  push: GitPullRequest,
}

const statusColors = {
  pending: 'text-gray-400 border-gray-300',
  in_progress: 'text-blue-500 border-blue-500 animate-pulse',
  completed: 'text-green-500 border-green-500',
  failed: 'text-red-500 border-red-500',
}

const statusBgColors = {
  pending: 'bg-gray-100',
  in_progress: 'bg-blue-50',
  completed: 'bg-green-50',
  failed: 'bg-red-50',
}

const StatusIcon = ({ status }: { status: GitWorkflowStep['status'] }) => {
  if (status === 'completed') return <Check className="w-4 h-4" />
  if (status === 'failed') return <X className="w-4 h-4" />
  if (status === 'in_progress') return <Loader2 className="w-4 h-4 animate-spin" />
  return null
}

export function GitWorkflowStepper({ steps, className = '' }: GitWorkflowStepperProps) {
  return (
    <div className={`relative ${className}`}>
      {/* Horizontal progress line */}
      <div className="absolute top-6 left-0 right-0 h-0.5 bg-gray-200" />

      {/* Progress indicator */}
      <motion.div
        className="absolute top-6 left-0 h-0.5 bg-blue-500"
        initial={{ width: '0%' }}
        animate={{
          width: `${(steps.filter(s => s.status === 'completed').length / steps.length) * 100}%`,
        }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      />

      {/* Steps */}
      <div className="relative flex justify-between">
        {steps.map((step, index) => {
          const Icon = stepIcons[step.id]
          const colorClass = statusColors[step.status]
          const bgClass = statusBgColors[step.status]

          return (
            <motion.div
              key={step.id}
              className="flex flex-col items-center"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              {/* Step circle */}
              <div
                className={`
                  relative z-10 w-12 h-12 rounded-full border-2
                  ${colorClass} ${bgClass}
                  flex items-center justify-center
                  transition-all duration-300
                `}
              >
                {step.status === 'pending' && Icon && <Icon className="w-5 h-5" />}
                {(step.status === 'in_progress' || step.status === 'completed' || step.status === 'failed') && (
                  <div className="relative">
                    {Icon && <Icon className="w-5 h-5" />}
                    <div className="absolute -bottom-1 -right-1 bg-white rounded-full">
                      <StatusIcon status={step.status} />
                    </div>
                  </div>
                )}
              </div>

              {/* Step label */}
              <div className="mt-2 text-center">
                <div className={`text-xs font-medium ${colorClass.split(' ')[0]}`}>
                  {step.label}
                </div>

                {/* Error message */}
                {step.status === 'failed' && step.error && (
                  <div className="mt-1 text-xs text-red-600 max-w-24 truncate" title={step.error}>
                    {step.error}
                  </div>
                )}

                {/* Timestamp */}
                {step.timestamp && step.status !== 'pending' && (
                  <div className="text-xs text-gray-400 mt-0.5">
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
