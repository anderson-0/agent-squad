'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Users, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface WIPLimitModalProps {
  isOpen: boolean;
  onClose: () => void;
  availableAgents: number;
  tasksInProgress: number;
}

export function WIPLimitModal({
  isOpen,
  onClose,
  availableAgents,
  tasksInProgress,
}: WIPLimitModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
            onClick={onClose}
          />

          {/* Modal */}
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.9, y: 20 }}
              transition={{
                duration: 0.3,
                ease: [0.22, 1, 0.36, 1] as const,
              }}
              className="relative max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="p-6 shadow-2xl border-2 border-orange-200 dark:border-orange-900/50 bg-gradient-to-br from-orange-50 to-white dark:from-orange-950/20 dark:to-background">
                {/* Close Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute top-4 right-4 h-8 w-8 p-0"
                  onClick={onClose}
                >
                  <X className="h-4 w-4" />
                </Button>

                {/* Icon */}
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{
                    delay: 0.1,
                    type: 'spring',
                    stiffness: 200,
                    damping: 15,
                  }}
                  className="flex justify-center mb-4"
                >
                  <div className="relative">
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [0.5, 0.2, 0.5],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }}
                      className="absolute inset-0 rounded-full bg-orange-500 blur-xl"
                    />
                    <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-red-500">
                      <AlertTriangle className="h-8 w-8 text-white" />
                    </div>
                  </div>
                </motion.div>

                {/* Content */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2, duration: 0.3 }}
                >
                  <h2 className="text-xl font-bold text-center mb-2">
                    No Available Agents
                  </h2>
                  <p className="text-sm text-muted-foreground text-center mb-6">
                    All agents are currently busy. Please wait for an agent to become
                    available before moving more tasks to "In Progress".
                  </p>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <motion.div
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3, duration: 0.3 }}
                      className="p-4 rounded-lg bg-background border-2 border-orange-200 dark:border-orange-900/50"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Users className="h-4 w-4 text-orange-600" />
                        <span className="text-xs font-semibold text-muted-foreground">
                          Available
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-orange-600">
                        {availableAgents}
                      </div>
                    </motion.div>

                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3, duration: 0.3 }}
                      className="p-4 rounded-lg bg-background border-2 border-blue-200 dark:border-blue-900/50"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="h-4 w-4 text-blue-600" />
                        <span className="text-xs font-semibold text-muted-foreground">
                          In Progress
                        </span>
                      </div>
                      <div className="text-2xl font-bold text-blue-600">
                        {tasksInProgress}
                      </div>
                    </motion.div>
                  </div>

                  {/* Action */}
                  <Button
                    onClick={onClose}
                    className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
                  >
                    Got it
                  </Button>
                </motion.div>
              </Card>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
