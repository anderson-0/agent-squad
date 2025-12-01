import { motion } from 'framer-motion';

export function TypingIndicator({ agentName }: { agentName: string }) {
    return (
        <div className="flex items-center gap-2 p-4 text-sm text-muted-foreground">
            <span className="font-medium">{agentName}</span> is thinking
            <div className="flex gap-1">
                <motion.div
                    className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0 }}
                />
                <motion.div
                    className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.2 }}
                />
                <motion.div
                    className="h-1.5 w-1.5 rounded-full bg-muted-foreground/50"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 0.6, repeat: Infinity, delay: 0.4 }}
                />
            </div>
        </div>
    );
}
