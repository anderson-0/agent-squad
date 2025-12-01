/**
 * Agent Work Page
 *
 * Lovable-style split-pane interface for watching agents work in real-time
 */

'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import confetti from 'canvas-confetti';
import {
  Bot,
  Activity,
  MessageCircle,
  Brain,
  Zap,
  Filter,
  Wifi,
  WifiOff,
  Box,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card } from '@/components/ui/card';
import { AgentAvatar } from '@/components/squads/AgentAvatar';
import { ActivityCard } from '@/components/agent-work/ActivityCard';
import { ThoughtCard } from '@/components/agent-work/ThoughtCard';
import { ConversationView } from '@/components/agent-work/ConversationView';
import { SandboxProgressCard } from '@/components/agent-work/SandboxProgressCard';
import { useSSE } from '@/lib/hooks/useSSE';
import { mockSquads } from '@/lib/mock-data/squads';
import {
  mockActivities,
  mockConversations,
  mockThoughts,
} from '@/lib/mock-data/agent-activities';
import type { Agent } from '@/types/squad';
import type { SandboxProgress, SandboxEvent } from '@/types/sandbox';

export default function AgentWorkPage() {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [realtimeActivities, setRealtimeActivities] = useState<any[]>([]);
  const [realtimeThoughts, setRealtimeThoughts] = useState<any[]>([]);
  const [sandboxes, setSandboxes] = useState<Map<string, SandboxProgress>>(new Map());

  // Get all agents from all squads
  const allAgents = mockSquads.flatMap((squad) => squad.agents);
  const activeAgents = allAgents.filter(
    (a) => a.status === 'working' || a.status === 'thinking'
  );

  // SSE Connection for real-time updates
  // Connect to squad stream (you can change this to execution stream)
  const squadId = mockSquads[0]?.id; // Use first squad for demo
  const { isConnected, lastMessage } = useSSE({
    url: squadId ? `/squads/${squadId}/stream` : '',
    autoConnect: !!squadId,
    onMessage: (event) => {
      console.log('[SSE] Received event:', event);

      // Handle different event types
      switch (event.event) {
        case 'status_update':
          // Add to activities
          setRealtimeActivities((prev) => [
            {
              id: event.id || Date.now().toString(),
              agent_id: event.data.agent_id,
              type: 'status_update',
              message: event.data.message || 'Status updated',
              timestamp: new Date().toISOString(),
              metadata: event.data,
            },
            ...prev,
          ]);
          break;

        case 'log':
          // Add to thoughts (agent reasoning)
          setRealtimeThoughts((prev) => [
            {
              id: event.id || Date.now().toString(),
              agent_id: event.data.agent_id,
              content: event.data.message,
              timestamp: new Date().toISOString(),
              metadata: event.data,
            },
            ...prev,
          ]);
          break;

        case 'completed':
          // Trigger confetti on completion
          confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 },
            colors: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b'],
          });
          setRealtimeActivities((prev) => [
            {
              id: event.id || Date.now().toString(),
              agent_id: event.data.agent_id,
              type: 'task_completed',
              message: 'Task completed successfully!',
              timestamp: new Date().toISOString(),
              metadata: event.data,
            },
            ...prev,
          ]);
          break;

        case 'error':
          setRealtimeActivities((prev) => [
            {
              id: event.id || Date.now().toString(),
              agent_id: event.data.agent_id,
              type: 'error',
              message: event.data.error || 'An error occurred',
              timestamp: new Date().toISOString(),
              metadata: event.data,
            },
            ...prev,
          ]);
          break;

        // Sandbox events
        case 'sandbox_created':
        case 'git_operation':
        case 'pr_created':
        case 'sandbox_terminated':
        case 'sandbox_error':
        case 'pr_approved':
        case 'pr_merged':
        case 'pr_closed':
        case 'pr_reopened':
          // Initialize sandbox if it doesn't exist
          setSandboxes((prev) => {
            const sandboxId = event.data.sandbox_id;
            if (!sandboxId) return prev;

            const newMap = new Map(prev);
            if (!newMap.has(sandboxId) && event.event === 'sandbox_created') {
              newMap.set(sandboxId, {
                sandbox_id: sandboxId,
                e2b_id: event.data.e2b_id || '',
                status: 'CREATED',
                workflow_steps: [
                  { id: 'clone', label: 'Clone Repo', status: 'pending' },
                  { id: 'create_branch', label: 'Create Branch', status: 'pending' },
                  { id: 'commit', label: 'Commit Changes', status: 'pending' },
                  { id: 'push', label: 'Push to Remote', status: 'pending' },
                ],
                created_at: event.data.timestamp || new Date().toISOString(),
                last_updated: event.data.timestamp || new Date().toISOString(),
              });
            }
            return newMap;
          });
          break;
      }
    },
    onError: (error) => {
      console.error('[SSE] Connection error:', error);
    },
  });

  // Handler for sandbox events (passed to SandboxProgressCard)
  const handleSandboxEvent = (event: SandboxEvent) => {
    console.log('[Sandbox Event]', event);
    // Events are already handled in SSE onMessage
    // This handler is for component-specific logic if needed
  };

  // Combine mock data with real-time data (real-time first)
  const combinedActivities = [...realtimeActivities, ...mockActivities];
  const combinedThoughts = [...realtimeThoughts, ...mockThoughts];

  // Filter activities by selected agent
  const filteredActivities = selectedAgentId
    ? combinedActivities.filter((a) => a.agent_id === selectedAgentId)
    : combinedActivities;

  const filteredThoughts = selectedAgentId
    ? combinedThoughts.filter((t) => t.agent_id === selectedAgentId)
    : combinedThoughts;

  // Get all messages
  const allMessages = mockConversations.flatMap((c) => c.messages);

  // Trigger confetti on task completion
  useEffect(() => {
    const completedActivity = mockActivities.find(
      (a) => a.type === 'task_completed'
    );
    if (completedActivity) {
      // Delay to match animation
      const timer = setTimeout(() => {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
          colors: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b'],
        });
      }, 500);
      return () => clearTimeout(timer);
    }
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-5rem)] overflow-hidden">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="pb-6"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-pink-600">
              <Bot className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Agent Work</h1>
              <p className="text-sm text-muted-foreground">
                Watch your AI agents collaborate in real-time
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge
              variant={isConnected ? 'default' : 'outline'}
              className={`gap-2 ${
                isConnected
                  ? 'bg-green-600 text-white'
                  : 'text-muted-foreground'
              }`}
            >
              {isConnected ? (
                <Wifi className="h-3 w-3" />
              ) : (
                <WifiOff className="h-3 w-3" />
              )}
              {isConnected ? 'Live' : 'Offline'}
            </Badge>
            <Badge variant="outline" className="gap-2">
              <Activity className="h-3 w-3 text-green-600" />
              {activeAgents.length} Active
            </Badge>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedAgentId(null)}
            >
              <Filter className="h-4 w-4 mr-2" />
              All Agents
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Split Pane Layout */}
      <div className="flex-1 flex gap-6 overflow-hidden">
        {/* Left Sidebar - Agent List (30%) */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="w-full md:w-80 flex-shrink-0 overflow-hidden"
        >
          <Card className="h-full flex flex-col">
            <div className="p-4 border-b">
              <h2 className="font-semibold flex items-center gap-2">
                <Zap className="h-4 w-4 text-yellow-600" />
                Active Agents
              </h2>
              <p className="text-xs text-muted-foreground mt-1">
                Click to focus on an agent
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <AnimatePresence mode="popLayout">
                {allAgents.map((agent, index) => (
                  <motion.div
                    key={agent.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    onClick={() => setSelectedAgentId(agent.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      selectedAgentId === agent.id
                        ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-300 shadow-sm'
                        : 'hover:bg-muted/50 hover:shadow-sm'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <AgentAvatar agent={agent} size="md" index={index} />
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-sm truncate">
                          {agent.name}
                        </h3>
                        <p className="text-xs text-muted-foreground truncate">
                          {agent.role}
                        </p>
                        {agent.current_task_id && (
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                            Working on task...
                          </p>
                        )}
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </Card>
        </motion.div>

        {/* Right Content Area (70%) */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="flex-1 overflow-hidden"
        >
          <Tabs defaultValue="activity" className="h-full flex flex-col">
            <TabsList className="grid w-full max-w-2xl grid-cols-4">
              <TabsTrigger value="activity" className="gap-2">
                <Activity className="h-4 w-4" />
                Activity
              </TabsTrigger>
              <TabsTrigger value="sandboxes" className="gap-2">
                <Box className="h-4 w-4" />
                Sandboxes
                {sandboxes.size > 0 && (
                  <Badge variant="secondary" className="ml-1 h-5 min-w-5 px-1">
                    {sandboxes.size}
                  </Badge>
                )}
              </TabsTrigger>
              <TabsTrigger value="conversations" className="gap-2">
                <MessageCircle className="h-4 w-4" />
                Conversations
              </TabsTrigger>
              <TabsTrigger value="thoughts" className="gap-2">
                <Brain className="h-4 w-4" />
                Thoughts
              </TabsTrigger>
            </TabsList>

            <TabsContent value="activity" className="flex-1 overflow-y-auto mt-6 space-y-3">
              {filteredActivities.length > 0 ? (
                filteredActivities.map((activity, index) => (
                  <ActivityCard
                    key={activity.id}
                    activity={activity}
                    index={index}
                  />
                ))
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <Activity className="h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No activity yet</h3>
                  <p className="text-sm text-muted-foreground">
                    Agent activities will appear here in real-time
                  </p>
                </div>
              )}
            </TabsContent>

            <TabsContent value="sandboxes" className="flex-1 overflow-y-auto mt-6 space-y-3">
              {sandboxes.size > 0 ? (
                Array.from(sandboxes.values()).map((sandbox) => (
                  <SandboxProgressCard
                    key={sandbox.sandbox_id}
                    sandboxId={sandbox.sandbox_id}
                    initialProgress={sandbox}
                    onEvent={handleSandboxEvent}
                  />
                ))
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <Box className="h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No sandboxes yet</h3>
                  <p className="text-sm text-muted-foreground">
                    E2B sandboxes will appear here when agents start working
                  </p>
                </div>
              )}
            </TabsContent>

            <TabsContent
              value="conversations"
              className="flex-1 overflow-y-auto mt-6"
            >
              <ConversationView messages={allMessages} />
            </TabsContent>

            <TabsContent value="thoughts" className="flex-1 overflow-y-auto mt-6 space-y-3">
              {filteredThoughts.length > 0 ? (
                filteredThoughts.map((thought, index) => (
                  <ThoughtCard
                    key={thought.id}
                    thought={thought}
                    index={index}
                  />
                ))
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <Brain className="h-12 w-12 text-muted-foreground/50 mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No thoughts yet</h3>
                  <p className="text-sm text-muted-foreground">
                    Agent reasoning and thoughts will appear here
                  </p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </motion.div>
      </div>
    </div>
  );
}
