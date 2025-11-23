import { cn } from '@/lib/utils';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Message } from './useChat';
import { motion } from 'framer-motion';

interface MessageBubbleProps {
    message: Message;
    isCurrentUser: boolean; // In this context, "current user" might mean the agent we are focusing on, or just layout alignment
    agent?: { role: string; name: string };
}

export function MessageBubble({ message, isCurrentUser, agent }: MessageBubbleProps) {
    const initials = agent?.name
        ? agent.name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2)
        : 'AG';

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "flex w-full gap-3 p-4",
                isCurrentUser ? "flex-row-reverse" : "flex-row"
            )}
        >
            <div className="flex-shrink-0">
                <Avatar className="h-8 w-8 border-2 border-background">
                    <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white font-medium text-xs">
                        {initials}
                    </AvatarFallback>
                </Avatar>
            </div>

            <div className={cn(
                "flex max-w-[80%] flex-col gap-1",
                isCurrentUser ? "items-end" : "items-start"
            )}>
                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-muted-foreground">
                        {agent?.role || 'Agent'}
                    </span>
                    <span className="text-xs text-muted-foreground">
                        {new Date(message.createdAt).toLocaleTimeString()}
                    </span>
                </div>

                <div className={cn(
                    "relative rounded-2xl px-4 py-3 text-sm shadow-sm",
                    isCurrentUser
                        ? "bg-primary text-primary-foreground rounded-tr-none"
                        : "bg-muted text-foreground rounded-tl-none"
                )}>
                    {message.content}
                </div>
            </div>
        </motion.div>
    );
}
