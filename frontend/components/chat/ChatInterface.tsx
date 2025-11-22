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
        isConnected,
        streamingMessage,
        fetchConversationDetails
    } = useChat(squadId);

    // Load details when active conversation changes
    useEffect(() => {
        if (activeConversationId) {
            fetchConversationDetails(activeConversationId);
        }
    }, [activeConversationId, fetchConversationDetails]);

    // Mock agents for now (since we don't have a full agent fetcher yet)
    // In a real app, we'd fetch squad members
    const mockAgents = {
        'agent-1': { id: 'agent-1', role: 'Product Manager', name: 'Sarah', avatar: '' },
        'agent-2': { id: 'agent-2', role: 'Backend Dev', name: 'Mike', avatar: '' },
        'agent-3': { id: 'agent-3', role: 'Tech Lead', name: 'Alex', avatar: '' },
    };

    const activeConversation = conversations.find(c => c.id === activeConversationId);

    return (
        <Card className="flex h-[calc(100vh-10rem)] w-full overflow-hidden border shadow-sm">
            <ConversationList
                conversations={conversations}
                activeId={activeConversationId}
                onSelect={setActiveConversationId}
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
                        agents={mockAgents}
                    />
                ) : (
                    <div className="flex flex-1 items-center justify-center text-muted-foreground">
                        Select a conversation to view details
                    </div>
                )}
            </div>
        </Card>
    );
}
