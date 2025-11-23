import { useEffect } from 'react';
import { useChat } from './useChat';
import { ConversationList } from './ConversationList';
import { MessageList } from './MessageList';
import { Card } from '@/components/ui/card';
import { Loader2 } from 'lucide-react';

interface ChatInterfaceProps {
    squadId: string;
}

export function ChatInterface({ squadId }: ChatInterfaceProps) {
    const {
        conversations,
        activeConversationId,
        setActiveConversationId,
        agents,
        isConnected,
        isLoading,
        error,
        streamingMessage,
        fetchConversationDetails
    } = useChat(squadId);

    // Load details when active conversation changes
    useEffect(() => {
        if (activeConversationId) {
            fetchConversationDetails(activeConversationId);
        }
    }, [activeConversationId, fetchConversationDetails]);

    const activeConversation = conversations.find(c => c.id === activeConversationId);

    if (isLoading) {
        return (
            <Card className="flex h-[calc(100vh-10rem)] w-full items-center justify-center border shadow-sm">
                <div className="flex flex-col items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-8 w-8 animate-spin" />
                    <p>Loading conversations...</p>
                </div>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="flex h-[calc(100vh-10rem)] w-full items-center justify-center border shadow-sm">
                <div className="flex flex-col items-center gap-2 text-destructive">
                    <p className="font-medium">Failed to load chat</p>
                    <p className="text-sm text-muted-foreground">{error}</p>
                </div>
            </Card>
        );
    }

    return (
        <Card className="flex h-[calc(100vh-10rem)] w-full overflow-hidden border shadow-sm">
            <ConversationList
                conversations={conversations}
                activeId={activeConversationId}
                onSelect={setActiveConversationId}
                agents={agents}
            />

            <div className="flex flex-1 flex-col bg-background">
                <div className="flex items-center justify-between border-b p-4">
                    <div className="flex items-center gap-2">
                        <h2 className="font-semibold">
                            {activeConversation?.questionType || "Select a conversation"}
                        </h2>
                        {isConnected && (
                            <span className="flex h-2 w-2 rounded-full bg-green-500" title="Connected" />
                        )}
                    </div>
                </div>

                {activeConversation ? (
                    <MessageList
                        messages={activeConversation.messages}
                        streamingMessage={streamingMessage}
                        agents={agents}
                    />
                ) : (
                    <div className="flex flex-1 items-center justify-center text-muted-foreground">
                        {conversations.length === 0 ? (
                            <div className="flex flex-col items-center gap-2">
                                <p className="font-medium">No conversations yet</p>
                                <p className="text-sm">Agents will appear here when they start collaborating</p>
                            </div>
                        ) : (
                            'Select a conversation to view details'
                        )}
                    </div>
                )}
            </div>
        </Card>
    );
}
