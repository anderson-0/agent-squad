/**
 * Sandbox Types - E2B Sandbox and Git Workflow Events
 *
 * These types match the backend SSE event schemas for real-time updates.
 */

export type SandboxStatus = 'CREATED' | 'RUNNING' | 'TERMINATED' | 'ERROR'

export type GitOperation = 'clone' | 'create_branch' | 'commit' | 'push'

export type GitOperationStatus = 'started' | 'completed' | 'failed'

/**
 * Sandbox entity from database
 */
export interface Sandbox {
  id: string
  e2b_id: string
  agent_id?: string
  task_id?: string
  repo_url?: string
  status: SandboxStatus
  last_used_at: string
  created_at: string
  updated_at: string
}

/**
 * SSE Event: Sandbox Created
 */
export interface SandboxCreatedEvent {
  event: 'sandbox_created'
  sandbox_id: string
  e2b_id: string
  task_id?: string
  agent_id?: string
  repo_url?: string
  status: string
  timestamp: string
}

/**
 * SSE Event: Git Operation
 */
export interface GitOperationEvent {
  event: 'git_operation'
  sandbox_id: string
  operation: GitOperation
  status: GitOperationStatus
  repo_url?: string
  branch_name?: string
  commit_message?: string
  output?: string
  error?: string
  timestamp: string
}

/**
 * SSE Event: Pull Request Created
 */
export interface PRCreatedEvent {
  event: 'pr_created'
  sandbox_id: string
  pr_number: number
  pr_url: string
  pr_title: string
  pr_body?: string
  head_branch: string
  base_branch: string
  repo_owner_name: string
  timestamp: string
}

/**
 * SSE Event: Sandbox Terminated
 */
export interface SandboxTerminatedEvent {
  event: 'sandbox_terminated'
  sandbox_id: string
  e2b_id: string
  runtime_seconds?: number
  status: string
  timestamp: string
}

/**
 * SSE Event: Sandbox Error
 */
export interface SandboxErrorEvent {
  event: 'sandbox_error'
  sandbox_id: string
  operation: string
  error_message: string
  error_details?: string
  timestamp: string
}

/**
 * SSE Event: PR Approved (from GitHub webhook)
 */
export interface PRApprovedEvent {
  event: 'pr_approved'
  sandbox_id: string
  pr_number: number
  pr_url: string
  reviewer: string
  review_state: string
  timestamp: string
}

/**
 * SSE Event: PR Merged (from GitHub webhook)
 */
export interface PRMergedEvent {
  event: 'pr_merged'
  sandbox_id: string
  pr_number: number
  pr_url: string
  merged_by: string
  merge_commit_sha: string
  timestamp: string
}

/**
 * SSE Event: PR Closed (from GitHub webhook)
 */
export interface PRClosedEvent {
  event: 'pr_closed'
  sandbox_id: string
  pr_number: number
  pr_url: string
  closed_by: string
  timestamp: string
}

/**
 * SSE Event: PR Reopened (from GitHub webhook)
 */
export interface PRReopenedEvent {
  event: 'pr_reopened'
  sandbox_id: string
  pr_number: number
  pr_url: string
  reopened_by: string
  timestamp: string
}

/**
 * Union type for all sandbox SSE events
 */
export type SandboxEvent =
  | SandboxCreatedEvent
  | GitOperationEvent
  | PRCreatedEvent
  | SandboxTerminatedEvent
  | SandboxErrorEvent
  | PRApprovedEvent
  | PRMergedEvent
  | PRClosedEvent
  | PRReopenedEvent

/**
 * Git workflow step for visualization
 */
export interface GitWorkflowStep {
  id: GitOperation
  label: string
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  output?: string
  error?: string
  timestamp?: string
}

/**
 * Sandbox progress state (for UI)
 */
export interface SandboxProgress {
  sandbox_id: string
  e2b_id: string
  status: SandboxStatus
  repo_url?: string
  current_operation?: GitOperation
  workflow_steps: GitWorkflowStep[]
  pr?: {
    number: number
    url: string
    title: string
    head_branch: string
    base_branch: string
    status?: 'open' | 'approved' | 'merged' | 'closed'
    reviewer?: string
    merged_by?: string
    closed_by?: string
  }
  runtime_seconds?: number
  created_at: string
  last_updated: string
}
