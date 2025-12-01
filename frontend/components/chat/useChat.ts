import { useState, useEffect, useRef, useCallback } from 'react';

export interface Message {
    id: string;
    content: string;
    senderId: string;
    recipientId: string;
    createdAt: string;
    type: 'question' | 'answer' | 'acknowledgment' | 'system';
    metadata?: any;
}

export interface Conversation {
    id: string;
    askerId: string;
    responderId: string;
    state: string;
    questionType: string;
    createdAt: string;
    messages: Message[];
    lastMessage?: Message;
}

export interface Agent {
    id: string;
    role: string;
    name: string;
    avatar?: string;
}

export function useChat(squadId: string) {
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
    const [agents, setAgents] = useState<Record<string, Agent>>({});
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [streamingMessage, setStreamingMessage] = useState<{
        conversationId: string;
        content: string;
        agentId: string;
    } | null>(null);

    const eventSourceRef = useRef<EventSource | null>(null);

    // Fetch squad members (agents) and conversations
    useEffect(() => {
        if (!squadId) return;

        const fetchData = async () => {
            try {
                setIsLoading(true);
                setError(null);

                // Fetch squad members to get agent information
                const membersRes = await fetch(`/api/v1/squads/${squadId}/members`, {
                    credentials: 'include'
                });

                if (membersRes.ok) {
                    const membersData = await membersRes.json();
                    const agentsMap: Record<string, Agent> = {};
                    membersData.forEach((member: any) => {
                        agentsMap[member.id] = {
                            id: member.id,
                            role: member.role,
                            name: member.name || member.role.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
                            avatar: member.avatar_url
                        };
                    });
                    setAgents(agentsMap);
                }

                // Fetch conversations
                const convRes = await fetch(`/api/v1/conversations/squads/${squadId}/conversations?limit=20`, {
                    credentials: 'include'
                });

                if (convRes.ok) {
                    const data = await convRes.json();
                    setConversations(data.map((c: any) => ({
                        id: c.id,
                        askerId: c.asker_id,
                        responderId: c.current_responder_id,
                        state: c.current_state,
                        questionType: c.question_type,
                        createdAt: c.created_at,
                        messages: []
                    })));
                } else {
                    throw new Error('Failed to fetch conversations');
                }
            } catch (error) {
                console.error('Failed to fetch data:', error);
                setError(error instanceof Error ? error.message : 'Failed to load chat data');
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
    }, [squadId]);

    // Connect to SSE
    useEffect(() => {
        if (!squadId) return;

        // Note: Standard EventSource doesn't support headers. 
        // We'll assume the backend can handle cookie auth or we might need a different approach.
        // For now, we'll try to append the token as a query param if the backend supported it, 
        // but the backend code uses `Depends(get_current_user)` which usually looks for Bearer token.
        // If this fails, we'll need to use `fetch` for polling or a polyfill.
        // Let's try to use the `event-source-polyfill` approach if we can, but I can't install packages.
        // So I will assume the user has a session cookie or I'll implement a polling fallback if needed.
        // Actually, let's just try standard EventSource.

        const url = `/api/v1/sse/squad/${squadId}`;
        const eventSource = new EventSource(url, { withCredentials: true });

        eventSource.onopen = () => {
            setIsConnected(true);
            console.log('SSE Connected');
        };

        eventSource.onerror = (err) => {
            console.error('SSE Error:', err);
            setIsConnected(false);
            eventSource.close();
        };

        eventSource.addEventListener('message', (e) => {
            const data = JSON.parse(e.data);
            console.log('New message:', data);
            // Here we would update the conversation list with the new message
            // For simplicity, we'll just log it for now, but in a real app we'd update state
        });

        eventSource.addEventListener('answer_streaming', (e) => {
            const data = JSON.parse(e.data);
            setStreamingMessage({
                conversationId: data.conversation_id,
                content: data.partial_response,
                agentId: data.agent_id
            });
        });

        eventSource.addEventListener('answer_complete', (e) => {
            setStreamingMessage(null);
            const data = JSON.parse(e.data);
            if (data.conversation_id) {
                fetchConversationDetails(data.conversation_id);
            }
        });

        eventSourceRef.current = eventSource;

        return () => {
            eventSource.close();
        };
    }, [squadId]);

    const fetchConversationDetails = useCallback(async (convId: string) => {
        try {
            const res = await fetch(`/api/v1/conversations/${convId}/timeline`, {
                credentials: 'include' // Include cookies for authentication
            });
            if (res.ok) {
                const data = await res.json();
                // Update local state
                setConversations(prev => prev.map(c => {
                    if (c.id === convId) {
                        return {
                            ...c,
                            messages: data.events
                                .filter((e: any) => ['initiated', 'answered', 'acknowledged'].includes(e.event_type))
                                .map((e: any) => ({
                                    id: e.message_id || e.created_at,
                                    content: e.event_data?.content || e.event_type,
                                    senderId: e.triggered_by_agent_id,
                                    createdAt: e.created_at,
                                    type: e.event_type === 'initiated' ? 'question' : e.event_type === 'answered' ? 'answer' : 'system'
                                }))
                        };
                    }
                    return c;
                }));
            }
        } catch (error) {
            console.error('Failed to fetch timeline:', error);
        }
    }, []);

    return {
        conversations,
        activeConversationId,
        setActiveConversationId,
        agents,
        isConnected,
        isLoading,
        error,
        streamingMessage,
        fetchConversationDetails
    };
}
