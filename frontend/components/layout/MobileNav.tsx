/**
 * Mobile Navigation Component
 *
 * Slide-in drawer for mobile devices
 * - AnimatePresence for enter/exit animations
 * - Backdrop with blur effect
 * - Staggered nav items animation
 * - Spring physics for smooth drawer motion
 */

'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Home, Users, ClipboardList, Bot, MessageSquare, X } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useMobileMenuStore } from '@/lib/stores/useMobileMenuStore';
import { cn } from '@/lib/utils';
import { useEffect } from 'react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Squads', href: '/squads', icon: Users },
  { name: 'Tasks', href: '/tasks', icon: ClipboardList },
  { name: 'Agent Work', href: '/agent-work', icon: Bot },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
];

export function MobileNav() {
  const { isOpen, close } = useMobileMenuStore();
  const pathname = usePathname();

  // Close drawer on route change
  useEffect(() => {
    close();
  }, [pathname, close]);

  // Prevent body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm md:hidden"
            onClick={close}
            aria-hidden="true"
          />

          {/* Drawer */}
          <motion.aside
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed inset-y-0 left-0 z-40 w-[280px] bg-sidebar shadow-xl md:hidden"
          >
            <div className="flex h-full flex-col overflow-y-auto px-6 pb-6">
              {/* Header with close button */}
              <div className="flex h-16 shrink-0 items-center justify-between">
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1, duration: 0.3 }}
                  className="flex items-center gap-2"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary/70">
                    <Bot className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <span className="text-lg font-semibold text-sidebar-foreground">
                    Agent Squad
                  </span>
                </motion.div>

                <motion.button
                  initial={{ opacity: 0, rotate: -90 }}
                  animate={{ opacity: 1, rotate: 0 }}
                  transition={{ delay: 0.1, duration: 0.3 }}
                  onClick={close}
                  className="flex h-10 w-10 items-center justify-center rounded-lg text-sidebar-foreground hover:bg-sidebar-accent"
                  aria-label="Close menu"
                >
                  <X className="h-5 w-5" />
                </motion.button>
              </div>

              {/* Navigation */}
              <nav className="mt-8 flex flex-1 flex-col">
                <ul role="list" className="space-y-1">
                  {navigation.map((item, index) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;

                    return (
                      <motion.li
                        key={item.name}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.1 + index * 0.05, duration: 0.3 }}
                      >
                        <Link
                          href={item.href}
                          className={cn(
                            'group flex gap-x-3 rounded-lg px-4 py-3 text-base font-medium leading-6 transition-all duration-200',
                            'relative overflow-hidden',
                            'min-h-[48px] items-center', // WCAG touch target
                            isActive
                              ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                              : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
                          )}
                        >
                          {/* Active indicator */}
                          {isActive && (
                            <motion.div
                              layoutId="mobile-active-indicator"
                              className="absolute left-0 top-0 h-full w-1 rounded-r-full bg-sidebar-primary"
                              transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                            />
                          )}

                          {/* Icon */}
                          <Icon
                            className={cn(
                              'h-6 w-6 shrink-0 transition-colors',
                              isActive
                                ? 'text-sidebar-primary'
                                : 'text-sidebar-foreground/60 group-hover:text-sidebar-foreground'
                            )}
                          />

                          <span className="truncate">{item.name}</span>
                        </Link>
                      </motion.li>
                    );
                  })}
                </ul>

                {/* Bottom section */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4, duration: 0.3 }}
                  className="mt-auto rounded-lg bg-sidebar-accent/30 px-4 py-3"
                >
                  <p className="text-sm font-medium text-sidebar-foreground">
                    Need help?
                  </p>
                  <p className="mt-1 text-xs text-sidebar-foreground/60">
                    Check out our documentation
                  </p>
                </motion.div>
              </nav>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
