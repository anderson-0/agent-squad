/**
 * Squad Types
 *
 * Type definitions for squads, agents, and tasks
 */

export type SquadStatus = 'active' | 'paused' | 'completed';
export type AgentStatus = 'idle' | 'thinking' | 'working' | 'completed' | 'error';
export type TaskStatus = 'pending' | 'in_progress' | 'in_review' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface AgentStats {
  tasks_completed: number;
  success_rate: number;
  total_time_hours: number;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: AgentStatus;
  current_task_id?: string;
  avatar_url?: string;
  stats: AgentStats;
}

export interface Subtask {
  id: string;
  title: string;
  completed: boolean;
}

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  assigned_agent_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  subtasks?: Subtask[];
  time_estimate_hours?: number;
  time_elapsed_hours?: number;
}

export interface Squad {
  id: string;
  name: string;
  description: string;
  status: SquadStatus;
  created_at: string;
  updated_at: string;
  progress: number; // 0-100
  level: number; // Gamification: squad level
  xp: number; // Gamification: experience points
  agents: Agent[];
  tasks: Task[];
  achievements: Achievement[];
}

export interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked_at: string;
  rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

export interface ActivityLog {
  id: string;
  squad_id: string;
  type: 'task_created' | 'task_completed' | 'agent_assigned' | 'achievement_unlocked';
  message: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
