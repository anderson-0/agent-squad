import { cn } from '@/lib/utils';
import { Conversation } from './useChat';

interface ConversationListProps {
    conversations: Conversation[];
    activeId: string | null;
    onSelect: (id: string) => void;
}

export function ConversationList({ conversations, activeId, onSelect }: ConversationListProps) {
    return (
        <div className="w-80 border-r bg-muted/10">
            <div className="p-4 font-semibold border-b">Conversations</div>
            <div className="h-[calc(100vh-12rem)] overflow-y-auto">
                <div className="flex flex-col gap-1 p-2">
                    {conversations.map((conv) => (
                        <button
                            key={conv.id}
                            onClick={() => onSelect(conv.id)}
                            className={cn(
                                "flex flex-col items-start gap-1 rounded-lg p-3 text-left text-sm transition-colors hover:bg-accent",
                                activeId === conv.id ? "bg-accent" : "transparent"
                            )}
                        >
                            <div className="flex w-full items-center justify-between">
                                <span className="font-medium">{conv.questionType}</span>
                                <span className="text-xs text-muted-foreground">
                                    {new Date(conv.createdAt).toLocaleDateString()}
                                </span>
                            </div>
                            <div className="text-xs text-muted-foreground line-clamp-2">
                                {conv.messages[0]?.content || "No messages"}
                            </div>
                            <div className="mt-2 flex items-center gap-2">
                                <span className={cn(
                                    "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
                                    conv.state === 'answered' ? "bg-green-50 text-green-700 ring-green-600/20" :
                                        conv.state === 'waiting' ? "bg-yellow-50 text-yellow-700 ring-yellow-600/20" :
                                            "bg-gray-50 text-gray-600 ring-gray-500/10"
                                )}>
                                    {conv.state}
                                </span>
                            </div>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
