import { cn } from '@/lib/utils';
import { Conversation, Agent } from './useChat';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface ConversationListProps {
    conversations: Conversation[];
    activeId: string | null;
    onSelect: (id: string) => void;
    agents?: Record<string, Agent>;
}

export function ConversationList({ conversations, activeId, onSelect, agents = {} }: ConversationListProps) {
    const getAgentInitials = (agentId: string) => {
        const agent = agents[agentId];
        if (!agent?.name) return 'AG';
        return agent.name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    const getAgentName = (agentId: string) => {
        return agents[agentId]?.name || agents[agentId]?.role || 'Unknown Agent';
    };

    return (
        <div className="w-80 border-r bg-muted/10">
            <div className="p-4 font-semibold border-b">
                Conversations
                <span className="ml-2 text-xs font-normal text-muted-foreground">
                    ({conversations.length})
                </span>
            </div>
            <div className="h-[calc(100vh-12rem)] overflow-y-auto">
                <div className="flex flex-col gap-1 p-2">
                    {conversations.length === 0 ? (
                        <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
                            <p className="text-sm">No conversations yet</p>
                        </div>
                    ) : (
                        conversations.map((conv) => (
                            <button
                                key={conv.id}
                                onClick={() => onSelect(conv.id)}
                                className={cn(
                                    "flex flex-col items-start gap-2 rounded-lg p-3 text-left text-sm transition-colors hover:bg-accent",
                                    activeId === conv.id ? "bg-accent" : "transparent"
                                )}
                            >
                                {/* Agent Avatars */}
                                <div className="flex items-center gap-2">
                                    <div className="flex -space-x-2">
                                        <Avatar className="h-6 w-6 border-2 border-background">
                                            <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-[10px]">
                                                {getAgentInitials(conv.askerId)}
                                            </AvatarFallback>
                                        </Avatar>
                                        <Avatar className="h-6 w-6 border-2 border-background">
                                            <AvatarFallback className="bg-gradient-to-br from-green-500 to-teal-600 text-white text-[10px]">
                                                {getAgentInitials(conv.responderId)}
                                            </AvatarFallback>
                                        </Avatar>
                                    </div>
                                    <span className="text-xs text-muted-foreground">
                                        {getAgentName(conv.askerId)} → {getAgentName(conv.responderId)}
                                    </span>
                                </div>

                                {/* Question Type & Date */}
                                <div className="flex w-full items-center justify-between">
                                    <span className="font-medium">{conv.questionType.replace('_', ' ')}</span>
                                    <span className="text-xs text-muted-foreground">
                                        {new Date(conv.createdAt).toLocaleDateString()}
                                    </span>
                                </div>

                                {/* Preview */}
                                <div className="text-xs text-muted-foreground line-clamp-2">
                                    {conv.messages[0]?.content || "Click to view conversation"}
                                </div>

                                {/* State Badge */}
                                <div className="mt-1 flex items-center gap-2">
                                    <span className={cn(
                                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
                                        conv.state === 'answered' ? "bg-green-50 text-green-700 ring-green-600/20" :
                                        conv.state === 'acknowledged' ? "bg-blue-50 text-blue-700 ring-blue-600/20" :
                                        conv.state === 'waiting' || conv.state === 'initiated' ? "bg-yellow-50 text-yellow-700 ring-yellow-600/20" :
                                        "bg-gray-50 text-gray-600 ring-gray-500/10"
                                    )}>
                                        {conv.state}
                                    </span>
                                </div>
                            </button>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
