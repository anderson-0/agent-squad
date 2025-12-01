/**
 * Analytics Page
 *
 * Dashboard for squad performance metrics
 */

'use client';

import { motion } from 'framer-motion';
import { BarChart3 } from 'lucide-react';
import { AnalyticsDashboard } from '@/components/analytics/AnalyticsDashboard';
import { useSearchParams } from 'next/navigation';

export default function AnalyticsPage() {
    const searchParams = useSearchParams();
    const squadId = searchParams.get('squadId') || 'default-squad-id'; // Fallback

    return (
        <div className="space-y-6 h-full flex flex-col overflow-y-auto">
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
                className="px-6 pt-6"
            >
                <div className="flex items-center gap-3">
                    <BarChart3 className="h-8 w-8 text-primary" />
                    <h1 className="text-3xl font-bold tracking-tight text-foreground">
                        Analytics
                    </h1>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">
                    Performance metrics and insights for your agent squads
                </p>
            </motion.div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2, duration: 0.5 }}
                className="flex-1"
            >
                <AnalyticsDashboard squadId={squadId} />
            </motion.div>
        </div>
    );
}
