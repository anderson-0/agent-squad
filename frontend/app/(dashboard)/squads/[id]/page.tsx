/**
 * Squad Detail Page
 *
 * Detailed view of a single squad with Kanban board and agent roster
 */

'use client';

import { useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  TrendingUp,
  Users,
  CheckCircle2,
  Zap,
  Settings,
  Plus,
  Target,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { KanbanBoard } from '@/components/squads/KanbanBoard';
import { AgentAvatar } from '@/components/squads/AgentAvatar';
import { CreateTaskModal } from '@/components/squads/CreateTaskModal';
import { AgentDetailsDialog } from '@/components/squads/AgentDetailsDialog';
import { CreateAgentDialog } from '@/components/squads/CreateAgentDialog';
import { getSquadById } from '@/lib/mock-data/squads';
import type { TaskStatus, Agent } from '@/types/squad';

export default function SquadDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [isCreateTaskModalOpen, setIsCreateTaskModalOpen] = useState(false);
  const [createTaskStatus, setCreateTaskStatus] = useState<TaskStatus>('pending');
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [isCreateAgentModalOpen, setIsCreateAgentModalOpen] = useState(false);

  const squad = getSquadById(id);

  if (!squad) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Squad not found</h2>
          <p className="text-muted-foreground mb-6">
            The squad you're looking for doesn't exist
          </p>
          <Button onClick={() => router.push('/squads')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Squads
          </Button>
        </div>
      </div>
    );
  }

  const handleTaskUpdate = (taskId: string, status: TaskStatus, feedback?: string) => {
    console.log(`Task ${taskId} moved to ${status}`, feedback ? `with feedback: ${feedback}` : '');
    // In real implementation, this would call an API
  };

  const handleCreateTask = (status: TaskStatus = 'pending') => {
    setCreateTaskStatus(status);
    setIsCreateTaskModalOpen(true);
  };

  const handleTaskSubmit = (task: { title: string; description: string; priority: string; status: TaskStatus }) => {
    console.log('Creating task:', task);
    // In real implementation, this would call an API and update the list
    setIsCreateTaskModalOpen(false);
  };

  const handleSettings = () => {
    alert("Settings modal coming soon!");
  };

  const handleAgentClick = (agent: Agent) => {
    setSelectedAgent(agent);
  };

  const handleAgentUpdate = (agentId: string, updates: any) => {
    console.log(`Updating agent ${agentId}:`, updates);
    // In real implementation, call API
    setSelectedAgent(null);
  };

  const handleCreateAgent = (agentData: any) => {
    // Mock subscription check
    if (squad && squad.agents.length >= 5) {
      alert("Subscription limit reached! Upgrade to Pro to add more agents.");
      return;
    }
    console.log("Creating agent:", agentData);
    // In real implementation, call API
    setIsCreateAgentModalOpen(false);
  };

  const completedTasks = squad.tasks.filter((t) => t.status === 'done').length;
  const activeAgents = squad.agents.filter(
    (a) => a.status === 'working' || a.status === 'thinking'
  ).length;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="space-y-4"
      >
        {/* Back Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/squads')}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Squads
        </Button>

        {/* Squad Header */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold tracking-tight">{squad.name}</h1>
              <Badge
                variant="outline"
                className={
                  squad.status === 'active'
                    ? 'bg-green-500/10 border-green-500/20 text-green-600'
                    : squad.status === 'paused'
                      ? 'bg-yellow-500/10 border-yellow-500/20 text-yellow-600'
                      : 'bg-blue-500/10 border-blue-500/20 text-blue-600'
                }
              >
                {squad.status}
              </Badge>
            </div>
            <p className="text-muted-foreground">{squad.description}</p>
          </div>

          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="gap-2" onClick={handleSettings}>
              <Settings className="h-4 w-4" />
              Settings
            </Button>
            <Button size="sm" className="gap-2" onClick={() => handleCreateTask('pending')}>
              <Plus className="h-4 w-4" />
              Add Task
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20"
          >
            <div className="flex items-center gap-2 text-blue-600 mb-1">
              <Target className="h-4 w-4" />
              <span className="text-xs font-medium">Progress</span>
            </div>
            <div className="text-2xl font-bold">{squad.progress}%</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20"
          >
            <div className="flex items-center gap-2 text-green-600 mb-1">
              <CheckCircle2 className="h-4 w-4" />
              <span className="text-xs font-medium">Tasks</span>
            </div>
            <div className="text-2xl font-bold">
              {completedTasks}/{squad.tasks.length}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="p-4 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20"
          >
            <div className="flex items-center gap-2 text-purple-600 mb-1">
              <Users className="h-4 w-4" />
              <span className="text-xs font-medium">Agents</span>
            </div>
            <div className="text-2xl font-bold">
              {activeAgents}/{squad.agents.length}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.4 }}
            className="p-4 rounded-lg bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border border-yellow-500/20"
          >
            <div className="flex items-center gap-2 text-yellow-600 mb-1">
              <Zap className="h-4 w-4" />
              <span className="text-xs font-medium">Level {squad.level}</span>
            </div>
            <div className="text-2xl font-bold">{squad.xp.toLocaleString()} XP</div>
          </motion.div>
        </div>
      </motion.div>

      {/* Tabs */}
      <Tabs defaultValue="board" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="board">Task Board</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
        </TabsList>

        <TabsContent value="board" className="mt-6">
          <KanbanBoard
            tasks={squad.tasks}
            agents={squad.agents}
            onTaskUpdate={handleTaskUpdate}
            onAddTask={handleCreateTask}
          />
        </TabsContent>

        <TabsContent value="agents" className="mt-6">
          <div className="flex justify-end mb-4">
            <Button size="sm" onClick={() => setIsCreateAgentModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Agent
            </Button>
          </div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {squad.agents.map((agent, index) => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="p-4 rounded-lg border bg-card hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleAgentClick(agent)}
              >
                <div className="flex items-start gap-3">
                  <AgentAvatar agent={agent} size="lg" index={index} />
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold truncate">{agent.name}</h4>
                    <p className="text-sm text-muted-foreground truncate">
                      {agent.role}
                    </p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-xs text-muted-foreground">Tasks</div>
                    <div className="text-sm font-semibold mt-1">
                      {agent.stats.tasks_completed}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Success</div>
                    <div className="text-sm font-semibold mt-1">
                      {agent.stats.success_rate}%
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </TabsContent>
      </Tabs>

      {/* Achievements */}
      {squad.achievements.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.5 }}
          className="p-6 rounded-lg border bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-950/20 dark:to-orange-950/20"
        >
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-600" />
            Achievements
          </h3>
          <div className="flex flex-wrap gap-3">
            {squad.achievements.map((achievement) => (
              <motion.div
                key={achievement.id}
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{
                  duration: 0.5,
                  type: 'spring',
                  stiffness: 200,
                }}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-background border hover:shadow-md transition-shadow"
              >
                <span className="text-2xl">{achievement.icon}</span>
                <div>
                  <div className="font-medium text-sm">{achievement.title}</div>
                  <div className="text-xs text-muted-foreground">
                    {achievement.description}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      <CreateTaskModal
        isOpen={isCreateTaskModalOpen}
        onClose={() => setIsCreateTaskModalOpen(false)}
        onSubmit={handleTaskSubmit}
        defaultStatus={createTaskStatus}
      />

      <AgentDetailsDialog
        agent={selectedAgent}
        isOpen={!!selectedAgent}
        onClose={() => setSelectedAgent(null)}
        onSave={handleAgentUpdate}
      />

      <CreateAgentDialog
        isOpen={isCreateAgentModalOpen}
        onClose={() => setIsCreateAgentModalOpen(false)}
        onSubmit={handleCreateAgent}
      />
    </div>
  );
}
