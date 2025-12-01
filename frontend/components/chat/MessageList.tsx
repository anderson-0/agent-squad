import { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { Message, Agent } from './useChat';

interface MessageListProps {
    messages: Message[];
    streamingMessage: { content: string; agentId: string } | null;
    agents: Record<string, Agent>;
}

export function MessageList({ messages, streamingMessage, agents }: MessageListProps) {
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages, streamingMessage]);

    return (
        <div className="flex-1 p-4 overflow-y-auto">
            <div className="flex flex-col gap-2">
                {messages.map((msg) => (
                    <MessageBubble
                        key={msg.id}
                        message={msg}
                        isCurrentUser={false} // In a squad view, no one is "me", or we could highlight the user's agent
                        agent={agents[msg.senderId]}
                    />
                ))}

                {streamingMessage && (
                    <div className="flex flex-col gap-2">
                        <MessageBubble
                            message={{
                                id: 'streaming',
                                content: streamingMessage.content,
                                senderId: streamingMessage.agentId,
                                recipientId: '',
                                createdAt: new Date().toISOString(),
                                type: 'answer'
                            }}
                            isCurrentUser={false}
                            agent={agents[streamingMessage.agentId]}
                        />
                        <TypingIndicator agentName={agents[streamingMessage.agentId]?.role || 'Agent'} />
                    </div>
                )}

                <div ref={scrollRef} />
            </div>
        </div>
    );
}
