'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';

interface ReviewFeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (feedback: string) => void;
  taskTitle: string;
  hasAvailableAgents: boolean;
}

export function ReviewFeedbackModal({
  isOpen,
  onClose,
  onSubmit,
  taskTitle,
  hasAvailableAgents,
}: ReviewFeedbackModalProps) {
  const [feedback, setFeedback] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = () => {
    if (!feedback.trim()) {
      setError('Please provide feedback for the agent');
      return;
    }

    if (!hasAvailableAgents) {
      setError('No available agents to assign this task');
      return;
    }

    onSubmit(feedback);
    setFeedback('');
    setError('');
  };

  const handleClose = () => {
    setFeedback('');
    setError('');
    onClose();
  };

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
            onClick={handleClose}
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
              className="relative max-w-lg w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <Card className="p-6 shadow-2xl border-2 border-purple-200 dark:border-purple-900/50 bg-gradient-to-br from-purple-50 to-white dark:from-purple-950/20 dark:to-background">
                {/* Close Button */}
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute top-4 right-4 h-8 w-8 p-0"
                  onClick={handleClose}
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
                      className="absolute inset-0 rounded-full bg-purple-500 blur-xl"
                    />
                    <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-400 to-pink-500">
                      <MessageSquare className="h-8 w-8 text-white" />
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
                    Provide Feedback
                  </h2>
                  <p className="text-sm text-muted-foreground text-center mb-1">
                    Why does this task need to return to work?
                  </p>
                  <p className="text-xs font-semibold text-center text-purple-600 dark:text-purple-400 mb-6 truncate">
                    {taskTitle}
                  </p>

                  {/* No Agents Warning */}
                  {!hasAvailableAgents && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mb-4 p-3 rounded-lg bg-orange-50 dark:bg-orange-950/20 border border-orange-200 dark:border-orange-900/50 flex items-start gap-2"
                    >
                      <AlertCircle className="h-4 w-4 text-orange-600 shrink-0 mt-0.5" />
                      <p className="text-xs text-orange-700 dark:text-orange-400">
                        No agents available. Task will be queued until an agent becomes free.
                      </p>
                    </motion.div>
                  )}

                  {/* Textarea */}
                  <div className="mb-4">
                    <Textarea
                      placeholder="e.g., The color scheme needs to be more vibrant, or the API endpoint returns incorrect data..."
                      value={feedback}
                      onChange={(e) => {
                        setFeedback(e.target.value);
                        setError('');
                      }}
                      className="min-h-[120px] resize-none"
                      autoFocus
                    />
                    {error && (
                      <motion.p
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-xs text-red-600 mt-2 flex items-center gap-1"
                      >
                        <AlertCircle className="h-3 w-3" />
                        {error}
                      </motion.p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3">
                    <Button
                      variant="outline"
                      onClick={handleClose}
                      className="flex-1"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleSubmit}
                      className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
                      disabled={!feedback.trim() || !hasAvailableAgents}
                    >
                      Submit & Reassign
                    </Button>
                  </div>
                </motion.div>
              </Card>
            </motion.div>
          </div>
        </>
      )}
    </AnimatePresence>
  );
}
