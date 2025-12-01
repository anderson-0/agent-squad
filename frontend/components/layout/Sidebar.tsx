/**
 * Sidebar Component
 *
 * Desktop persistent sidebar with smooth animations
 * - Slides in from left on mount
 * - Active route highlighting with left border accent
 * - Icon rotation on active state
 * - Hover animations with scale effect
 */

'use client';

import { motion } from 'framer-motion';
import { Home, Users, ClipboardList, Bot, MessageSquare } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Squads', href: '/squads', icon: Users },
  { name: 'Tasks', href: '/tasks', icon: ClipboardList },
  { name: 'Agent Work', href: '/agent-work', icon: Bot },
  { name: 'Chat', href: '/chat', icon: MessageSquare },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <motion.aside
      initial={{ x: -240, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="hidden md:fixed md:inset-y-0 md:z-40 md:flex md:w-60 md:flex-col"
    >
      <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-sidebar-border bg-sidebar px-6 pb-4">
        {/* Logo */}
        <div className="flex h-16 shrink-0 items-center">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
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
        </div>

        {/* Navigation */}
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-1">
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
                          'group flex gap-x-3 rounded-lg px-3 py-2.5 text-sm font-medium leading-6 transition-all duration-200',
                          'relative overflow-hidden',
                          isActive
                            ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                            : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground'
                        )}
                      >
                        {/* Active indicator - left border */}
                        {isActive && (
                          <motion.div
                            layoutId="sidebar-active-indicator"
                            className="absolute left-0 top-0 h-full w-1 rounded-r-full bg-sidebar-primary"
                            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                          />
                        )}

                        {/* Icon with rotation animation on active */}
                        <motion.div
                          animate={isActive ? { rotate: 360 } : { rotate: 0 }}
                          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                        >
                          <Icon
                            className={cn(
                              'h-5 w-5 shrink-0 transition-colors',
                              isActive
                                ? 'text-sidebar-primary'
                                : 'text-sidebar-foreground/60 group-hover:text-sidebar-foreground'
                            )}
                          />
                        </motion.div>

                        <span className="truncate">{item.name}</span>

                        {/* Hover scale effect */}
                        <motion.div
                          className="absolute inset-0 -z-10"
                          whileHover={{ scale: 1.02 }}
                          transition={{ duration: 0.2 }}
                        />
                      </Link>
                    </motion.li>
                  );
                })}
              </ul>
            </li>

            {/* Bottom section */}
            <li className="mt-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4, duration: 0.3 }}
                className="rounded-lg bg-sidebar-accent/30 px-4 py-3"
              >
                <p className="text-xs font-medium text-sidebar-foreground">
                  Need help?
                </p>
                <p className="mt-1 text-xs text-sidebar-foreground/60">
                  Check out our documentation
                </p>
              </motion.div>
            </li>
          </ul>
        </nav>
      </div>
    </motion.aside>
  );
}
