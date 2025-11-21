/**
 * Agent Activity Types
 *
 * Types for real-time agent work visualization
 */

export type ActivityType =
  | 'task_started'
  | 'thinking'
  | 'message'
  | 'code_change'
  | 'task_completed'
  | 'error'
  | 'question'
  | 'file_created'
  | 'file_modified'
  | 'test_passed'
  | 'test_failed';

export type ThoughtType = 'planning' | 'analyzing' | 'deciding' | 'executing';

export interface AgentMessage {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_role: string;
  content: string;
  timestamp: string;
  mentions?: string[]; // Agent IDs mentioned in message
  parent_message_id?: string; // For threading
}

export interface AgentThought {
  id: string;
  agent_id: string;
  agent_name: string;
  type: ThoughtType;
  content: string;
  reasoning_steps?: string[];
  decision?: string;
  timestamp: string;
  duration_ms?: number;
}

export interface CodeChange {
  id: string;
  file_path: string;
  language: string;
  additions: number;
  deletions: number;
  diff?: string;
  preview?: string;
}

export interface AgentActivity {
  id: string;
  agent_id: string;
  agent_name: string;
  agent_role: string;
  type: ActivityType;
  timestamp: string;

  // Activity-specific data
  message?: string;
  thought?: AgentThought;
  code_change?: CodeChange;
  error_details?: {
    message: string;
    stack?: string;
  };
  task?: {
    id: string;
    title: string;
  };
  metadata?: Record<string, any>;
}

export interface ConversationThread {
  id: string;
  messages: AgentMessage[];
  participants: string[]; // Agent IDs
  created_at: string;
  updated_at: string;
}

export interface AgentWorkSession {
  id: string;
  squad_id: string;
  task_id: string;
  agent_id: string;
  started_at: string;
  ended_at?: string;
  activities: AgentActivity[];
  conversations: ConversationThread[];
  thoughts: AgentThought[];
}
