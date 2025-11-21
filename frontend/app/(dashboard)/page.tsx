/**
 * Dashboard Home Page
 *
 * Main dashboard overview with stats and quick actions
 */

'use client';

import { motion } from 'framer-motion';
import { Bot, Users, ClipboardList, MessageSquare, TrendingUp, Activity } from 'lucide-react';

const stats = [
  {
    name: 'Active Squads',
    value: '8',
    change: '+12%',
    changeType: 'positive',
    icon: Users,
  },
  {
    name: 'Running Tasks',
    value: '24',
    change: '+4.75%',
    changeType: 'positive',
    icon: ClipboardList,
  },
  {
    name: 'Active Agents',
    value: '32',
    change: '+54.02%',
    changeType: 'positive',
    icon: Bot,
  },
  {
    name: 'Messages Today',
    value: '127',
    change: '-2.5%',
    changeType: 'negative',
    icon: MessageSquare,
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
      ease: [0.22, 1, 0.36, 1] as const,
    },
  },
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Dashboard
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Welcome back! Here's what's happening with your agent squads today.
        </p>
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.name}
              variants={itemVariants}
              whileHover={{ scale: 1.02, y: -4 }}
              className="group relative overflow-hidden rounded-xl border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              {/* Background gradient on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100" />

              <div className="relative">
                <div className="flex items-center justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <div
                    className={`flex items-center gap-1 text-xs font-medium ${
                      stat.changeType === 'positive'
                        ? 'text-green-600 dark:text-green-400'
                        : 'text-red-600 dark:text-red-400'
                    }`}
                  >
                    <TrendingUp
                      className={`h-3 w-3 ${
                        stat.changeType === 'negative' && 'rotate-180'
                      }`}
                    />
                    {stat.change}
                  </div>
                </div>

                <div className="mt-4">
                  <p className="text-sm font-medium text-muted-foreground">
                    {stat.name}
                  </p>
                  <p className="mt-1 text-3xl font-bold text-foreground">
                    {stat.value}
                  </p>
                </div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Recent Activity */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="rounded-xl border border-border bg-card p-6 shadow-sm"
      >
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold text-foreground">
            Recent Activity
          </h2>
        </div>

        <div className="mt-6 space-y-4">
          {[
            {
              text: 'Squad "Frontend Team" completed task "Design System Update"',
              time: '5 minutes ago',
            },
            {
              text: 'Agent "Code Reviewer" started working on "PR #123"',
              time: '12 minutes ago',
            },
            {
              text: 'New squad "Backend Team" created with 4 agents',
              time: '1 hour ago',
            },
            {
              text: 'Task "API Integration" assigned to "API Squad"',
              time: '2 hours ago',
            },
          ].map((activity, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{
                delay: 0.5 + index * 0.1,
                duration: 0.4,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="flex items-start gap-3 rounded-lg border border-border/50 bg-muted/30 p-4 transition-colors hover:bg-muted/50"
            >
              <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
              <div className="flex-1">
                <p className="text-sm text-foreground">{activity.text}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {activity.time}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
