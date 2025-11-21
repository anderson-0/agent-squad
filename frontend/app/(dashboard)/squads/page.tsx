/**
 * Squads Page
 *
 * List and manage agent squads with beautiful animations and gamification
 */

'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Plus,
  Filter,
  Sparkles,
  TrendingUp,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SquadCard } from '@/components/squads/SquadCard';
import { mockSquads } from '@/lib/mock-data/squads';
import type { Squad } from '@/types/squad';

type FilterType = 'all' | 'active' | 'paused' | 'completed';

export default function SquadsPage() {
  const [filter, setFilter] = useState<FilterType>('all');

  // Filter squads
  const filteredSquads = mockSquads.filter((squad) => {
    if (filter === 'all') return true;
    return squad.status === filter;
  });

  // Calculate stats
  const totalSquads = mockSquads.length;
  const activeSquads = mockSquads.filter((s) => s.status === 'active').length;
  const totalProgress = Math.round(
    mockSquads.reduce((acc, s) => acc + s.progress, 0) / totalSquads
  );
  const totalXP = mockSquads.reduce((acc, s) => acc + s.xp, 0);

  const filters: { value: FilterType; label: string; count: number }[] = [
    { value: 'all', label: 'All Squads', count: totalSquads },
    {
      value: 'active',
      label: 'Active',
      count: mockSquads.filter((s) => s.status === 'active').length,
    },
    {
      value: 'paused',
      label: 'Paused',
      count: mockSquads.filter((s) => s.status === 'paused').length,
    },
    {
      value: 'completed',
      label: 'Completed',
      count: mockSquads.filter((s) => s.status === 'completed').length,
    },
  ];

  return (
    <div className="space-y-6 pb-20">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="space-y-4"
      >
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-purple-600">
              <Users className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Squads</h1>
              <p className="text-sm text-muted-foreground">
                Manage your AI agent teams
              </p>
            </div>
          </div>

          {/* Desktop Create Button */}
          <Button size="lg" className="hidden md:flex gap-2">
            <Plus className="h-5 w-5" />
            Create Squad
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="p-4 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20"
          >
            <div className="flex items-center gap-2 text-blue-600 mb-1">
              <Users className="h-4 w-4" />
              <span className="text-xs font-medium">Total Squads</span>
            </div>
            <div className="text-2xl font-bold">{totalSquads}</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="p-4 rounded-lg bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20"
          >
            <div className="flex items-center gap-2 text-green-600 mb-1">
              <TrendingUp className="h-4 w-4" />
              <span className="text-xs font-medium">Active</span>
            </div>
            <div className="text-2xl font-bold">{activeSquads}</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="p-4 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20"
          >
            <div className="flex items-center gap-2 text-purple-600 mb-1">
              <Filter className="h-4 w-4" />
              <span className="text-xs font-medium">Avg Progress</span>
            </div>
            <div className="text-2xl font-bold">{totalProgress}%</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.4 }}
            className="p-4 rounded-lg bg-gradient-to-br from-yellow-500/10 to-yellow-600/10 border border-yellow-500/20"
          >
            <div className="flex items-center gap-2 text-yellow-600 mb-1">
              <Sparkles className="h-4 w-4" />
              <span className="text-xs font-medium">Total XP</span>
            </div>
            <div className="text-2xl font-bold">{totalXP.toLocaleString()}</div>
          </motion.div>
        </div>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="flex flex-wrap gap-2"
      >
        {filters.map((f) => (
          <Button
            key={f.value}
            variant={filter === f.value ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilter(f.value)}
            className="gap-2"
          >
            {f.label}
            <Badge
              variant={filter === f.value ? 'secondary' : 'outline'}
              className="ml-1 px-1.5"
            >
              {f.count}
            </Badge>
          </Button>
        ))}
      </motion.div>

      {/* Squad Grid */}
      <AnimatePresence mode="wait">
        {filteredSquads.length > 0 ? (
          <motion.div
            key={filter}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {filteredSquads.map((squad, index) => (
              <SquadCard key={squad.id} squad={squad} index={index} />
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3 }}
            className="flex min-h-[400px] items-center justify-center rounded-xl border-2 border-dashed border-border bg-muted/30"
          >
            <div className="text-center p-8">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{
                  duration: 0.5,
                  type: 'spring',
                  stiffness: 200,
                }}
              >
                <Users className="mx-auto h-16 w-16 text-muted-foreground/50" />
              </motion.div>
              <h3 className="mt-4 text-lg font-semibold">
                No {filter !== 'all' && filter} squads found
              </h3>
              <p className="mt-2 text-sm text-muted-foreground max-w-sm">
                {filter === 'all'
                  ? 'Create your first squad to start organizing your AI agents'
                  : `No squads with status "${filter}"`}
              </p>
              <Button className="mt-6 gap-2" size="lg">
                <Plus className="h-5 w-5" />
                Create Your First Squad
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mobile FAB */}
      <motion.div
        initial={{ opacity: 0, scale: 0 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, delay: 0.6, type: 'spring', stiffness: 200 }}
        className="fixed bottom-20 right-4 md:hidden z-50"
      >
        <Button
          size="lg"
          className="h-14 w-14 rounded-full shadow-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
        >
          <Plus className="h-6 w-6" />
        </Button>
      </motion.div>
    </div>
  );
}
