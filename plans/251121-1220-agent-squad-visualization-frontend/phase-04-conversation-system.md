# Phase 4: Conversation System & Threading

**Status**: Pending
**Priority**: P0 (User Requirement: MUST HAVE - Conversations between agents)
**Dependencies**: Phase 1, Phase 2, Phase 3
**Estimated Duration**: Claude (5 hrs) | Senior Dev (3 days) | Junior Dev (5-7 days)

---

## Context

Phase 4 implements the **conversation and threading system** - another critical requirement. This includes agent-to-agent conversations with threading, thought process visualization, user chat ONLY with PM/Tech Lead, and message filtering by role/visibility. End users should NEVER see internal developer agent conversations.

**Related Files**:
- Research: `research/researcher-01-ux-patterns.md` (Slack/Discord threading patterns)
- Backend: `scout/scout-02-backend-api.md` (agent messages, conversation protocol)
- Agent System: `scout/scout-03-agent-system.md` (message types, conversation states)

---

## Overview

**Goal**: Create conversation system with role-based visibility and threading.

**Key Deliverables**:
1. Conversation thread UI (agent-to-agent, agent-to-user)
2. Message filtering by visibility (public vs internal)
3. User chat interface for PM/Tech Lead ONLY
4. Thought process visualization (agent reasoning)
5. Message threading (tree-based for agent-agent, linear for user)
6. Typing indicators
7. Message reactions/acknowledgments
8. Conversation search and filtering

**Dates**:
- Start: TBD (after Phase 3)
- End: TBD
- **Status**: Pending

---

## Key Insights from Research

### From `researcher-01-ux-patterns.md`

**Slack Threads**:
- Reply to message opens thread in side panel
- Keeps main channel clean
- Good for support channels, less so for long discussions

**Discord Threads**:
- Must be named with expiration
- Creates subchannel in sidebar
- Full UI width (more pleasant than Slack)

**Tree Threading (Heim)**:
- Any message can have nested replies
- Subthreads display inline in tree structure
- True branching conversations

**Recommendation for Agent Squad**:
- **Agent-to-agent comms**: Inline tree threads
- **Agent-to-user**: Slack-style side panel threads
- **Thinking indicator**: When agent typing
- **Collapse/expand**: Manage conversation noise

### From `scout-03-agent-system.md`

**Message Types**:
1. `task_assignment` - PM assigns task to agent
2. `status_update` - Status update response
3. `question` - Question from agent (broadcast or direct)
4. `answer` - Answer to question
5. `human_intervention_required` - Escalation to human
6. `code_review_request` - Request code review
7. `code_review_response` - Code review result
8. `task_completion` - Task completed notification
9. `standup` - Daily standup update

**Conversation States**:
- `initiated` - Question sent
- `waiting` - Acknowledged, waiting for answer
- `timeout` - No answer after timeout
- `follow_up` - Sent "are you still there?"
- `escalating` - Escalating to higher level
- `escalated` - Re-routed to different agent
- `answered` - Resolved
- `cancelled` - Asker cancelled

**Visibility Rules** (Critical):
- **Public messages**: User-facing agents (PM, Tech Lead) ↔ User
- **Internal messages**: Developer agents ↔ Developer agents
- **End users**: ONLY see public messages
- **Developers**: See all messages
- **Admins**: See everything with toggle

---

## Requirements

### Functional Requirements

**FR-4.1**: User chat interface for communicating with PM/Tech Lead
**FR-4.2**: Message list showing conversation history
**FR-4.3**: Thread view for agent-to-agent conversations
**FR-4.4**: Visibility filter (show/hide internal conversations)
**FR-4.5**: Typing indicator when agent is responding
**FR-4.6**: Message reactions (👍, ❓, ✅)
**FR-4.7**: Message timestamp (relative + absolute)
**FR-4.8**: Agent identification (avatar, role, name)
**FR-4.9**: Conversation search
**FR-4.10**: Thread collapse/expand
**FR-4.11**: Unread message indicators
**FR-4.12**: "Jump to latest" button

### Non-Functional Requirements

**NFR-4.1**: Real-time message delivery < 200ms
**NFR-4.2**: Smooth scroll animations
**NFR-4.3**: Virtualization for 1000+ messages
**NFR-4.4**: Mobile-responsive (full-screen modal)
**NFR-4.5**: Accessibility (keyboard navigation)
**NFR-4.6**: Message persistence (cached locally)

---

## Architecture

### Component Hierarchy

```
Page: /tasks/[id]/conversations
├── ConversationLayout
│   ├── ConversationSidebar (agent list, filter)
│   │   ├── AgentSelector
│   │   ├── VisibilityToggle (show/hide internal)
│   │   └── ConversationList
│   │       └── ConversationItem (repeated)
│   └── ConversationMain
│       ├── ConversationHeader (agent name, status)
│       ├── MessageList (virtualized)
│       │   └── Message (repeated)
│       │       ├── MessageAvatar
│       │       ├── MessageContent
│       │       ├── MessageMetadata (timestamp, status)
│       │       ├── MessageReactions
│       │       └── ThreadButton (if has replies)
│       │           └── ThreadPanel (slide-in)
│       │               └── ThreadMessage (repeated)
│       └── MessageInput (if user can reply)
│           ├── TextArea
│           ├── SendButton
│           └── TypingIndicator

Component: ThoughtViewer (separate view)
├── ThoughtList
│   └── ThoughtItem (repeated)
│       ├── AgentAvatar
│       ├── ThoughtType (reasoning/planning/decision)
│       ├── ThoughtContent
│       └── Timestamp
```

### Message Visibility Logic

```typescript
enum MessageVisibility {
  PUBLIC = 'public',       // User-facing (PM, Tech Lead ↔ User)
  INTERNAL = 'internal',   // Developer agents ↔ Developer agents
  SYSTEM = 'system',       // System notifications
}

enum UserRole {
  END_USER = 'end_user',       // Only sees PUBLIC messages
  DEVELOPER = 'developer',     // Sees PUBLIC + INTERNAL
  ADMIN = 'admin',             // Sees everything
}

function canSeeMessage(message: Message, userRole: UserRole, showInternal: boolean): boolean {
  // End users NEVER see internal messages
  if (userRole === 'end_user' && message.visibility === 'internal') {
    return false;
  }

  // Developers can toggle internal visibility
  if (userRole === 'developer' && message.visibility === 'internal' && !showInternal) {
    return false;
  }

  // System messages always visible
  if (message.visibility === 'system') {
    return true;
  }

  return true;
}
```

### Message Threading

```
Conversation: "Implement Authentication"
│
├─ PM: "Can you implement JWT auth?"              [PUBLIC]
│  │
│  └─ Tech Lead: "I'll review the approach"       [PUBLIC]
│     │
│     ├─ Backend Dev: "Working on it"             [INTERNAL]
│     │  │
│     │  ├─ Backend Dev: "Question about algo"    [INTERNAL]
│     │  │  └─ Tech Lead: "Use HS256"             [INTERNAL]
│     │  │
│     │  └─ Backend Dev: "Tests failing"          [INTERNAL]
│     │     └─ QA: "I'll check"                   [INTERNAL]
│     │
│     └─ Tech Lead: "Implementation complete"     [PUBLIC]
│        └─ PM: "Great! Ship it"                  [PUBLIC]
```

**End User Sees**:
```
PM: "Can you implement JWT auth?"
├─ Tech Lead: "I'll review the approach"
   └─ Tech Lead: "Implementation complete"
      └─ PM: "Great! Ship it"
```

**Developer Sees** (with internal enabled):
```
(Full tree including all internal messages)
```

### Data Flow

```
User sends message to PM
    ↓
POST /api/v1/agent-messages
    ↓
Backend creates message (visibility: PUBLIC)
    ↓
NATS broadcasts to PM agent
    ↓
PM agent receives and processes
    ↓
PM agent responds
    ↓
SSE broadcasts response to frontend
    ↓
Frontend receives message event
    ↓
TanStack Query updates cache
    ↓
MessageList re-renders with new message
```

---

## Related Code Files

### Files to Create

1. **Types**:
   - `types/message.ts` (Message, MessageVisibility, Conversation, Thread)
   - `types/conversation.ts` (ConversationState, ConversationParticipant)

2. **API/Hooks**:
   - `lib/api/messages.ts` (send message, get messages, get conversation)
   - `lib/hooks/useConversations.ts`
   - `lib/hooks/useMessages.ts`
   - `lib/hooks/useSendMessage.ts`
   - `lib/hooks/useTypingIndicator.ts`

3. **Components - Conversation**:
   - `components/conversations/ConversationLayout.tsx`
   - `components/conversations/ConversationSidebar.tsx`
   - `components/conversations/ConversationList.tsx`
   - `components/conversations/ConversationItem.tsx`
   - `components/conversations/VisibilityToggle.tsx`

4. **Components - Messages**:
   - `components/messages/MessageList.tsx`
   - `components/messages/Message.tsx`
   - `components/messages/MessageAvatar.tsx`
   - `components/messages/MessageContent.tsx`
   - `components/messages/MessageInput.tsx`
   - `components/messages/TypingIndicator.tsx`
   - `components/messages/ThreadPanel.tsx`
   - `components/messages/ThreadMessage.tsx`

5. **Components - Thoughts**:
   - `components/thoughts/ThoughtViewer.tsx`
   - `components/thoughts/ThoughtItem.tsx`

6. **Pages**:
   - `app/(dashboard)/tasks/[id]/conversations/page.tsx`

7. **Store**:
   - `lib/store/conversations.ts` (visibility toggles, selected conversation)

---

## Implementation Steps

### Step 1: Create Message Types

```typescript
// types/message.ts
export enum MessageVisibility {
  PUBLIC = 'public',
  INTERNAL = 'internal',
  SYSTEM = 'system',
}

export enum MessageType {
  TASK_ASSIGNMENT = 'task_assignment',
  STATUS_UPDATE = 'status_update',
  QUESTION = 'question',
  ANSWER = 'answer',
  HUMAN_INTERVENTION_REQUIRED = 'human_intervention_required',
  CODE_REVIEW_REQUEST = 'code_review_request',
  CODE_REVIEW_RESPONSE = 'code_review_response',
  TASK_COMPLETION = 'task_completion',
  STANDUP = 'standup',
}

export interface Message {
  id: string;
  task_execution_id: string;
  sender_id: string;
  sender_name: string;
  sender_role: AgentRole;
  recipient_id?: string;
  recipient_name?: string;
  content: string;
  message_type: MessageType;
  visibility: MessageVisibility;
  metadata?: Record<string, any>;
  conversation_id?: string;
  parent_message_id?: string;
  has_replies: boolean;
  reply_count: number;
  reactions?: Record<string, string[]>; // { "👍": ["user1", "user2"] }
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  task_execution_id: string;
  participant_ids: string[];
  participants: ConversationParticipant[];
  last_message: Message;
  unread_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationParticipant {
  agent_id: string;
  agent_name: string;
  agent_role: AgentRole;
  is_typing: boolean;
}
```

### Step 2: Determine Message Visibility

```typescript
// lib/utils/message-visibility.ts
import type { Message, MessageVisibility } from '@/types/message';
import type { AgentRole } from '@/types/squad';

const USER_FACING_ROLES: AgentRole[] = ['project_manager', 'tech_lead'];

export function determineMessageVisibility(
  senderRole: AgentRole,
  recipientRole?: AgentRole
): MessageVisibility {
  // If sender is user-facing agent, message is PUBLIC
  if (USER_FACING_ROLES.includes(senderRole)) {
    return 'public';
  }

  // If recipient is user-facing agent, message is PUBLIC
  if (recipientRole && USER_FACING_ROLES.includes(recipientRole)) {
    return 'public';
  }

  // Otherwise, internal developer communication
  return 'internal';
}

export function canUserSeeMessage(
  message: Message,
  userRole: 'end_user' | 'developer' | 'admin',
  showInternal: boolean
): boolean {
  // End users NEVER see internal messages
  if (userRole === 'end_user' && message.visibility === 'internal') {
    return false;
  }

  // Developers can toggle internal visibility
  if (userRole === 'developer' && message.visibility === 'internal' && !showInternal) {
    return false;
  }

  // System messages always visible
  if (message.visibility === 'system') {
    return true;
  }

  return true;
}
```

### Step 3: Create Messages API

```typescript
// lib/api/messages.ts
import apiClient from './client';
import type { Message } from '@/types/message';

export const messagesApi = {
  list: async (executionId: string): Promise<Message[]> => {
    const response = await apiClient.get(
      `/task-executions/${executionId}/messages`
    );
    return response.data;
  },

  send: async (executionId: string, data: {
    recipient_id?: string;
    content: string;
    message_type: string;
    parent_message_id?: string;
  }): Promise<Message> => {
    const response = await apiClient.post('/agent-messages', {
      task_execution_id: executionId,
      ...data,
    });
    return response.data;
  },

  addReaction: async (messageId: string, emoji: string): Promise<void> => {
    await apiClient.post(`/agent-messages/${messageId}/reactions`, { emoji });
  },

  removeReaction: async (messageId: string, emoji: string): Promise<void> => {
    await apiClient.delete(`/agent-messages/${messageId}/reactions/${emoji}`);
  },
};
```

### Step 4: Create useMessages Hook with Filtering

```typescript
// lib/hooks/useMessages.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { messagesApi } from '@/lib/api/messages';
import { sseService } from '@/lib/realtime/sse';
import { getAccessToken } from '@/lib/store/auth';
import { canUserSeeMessage } from '@/lib/utils/message-visibility';
import { useAuthStore } from '@/lib/store/auth';
import { useConversationStore } from '@/lib/store/conversations';
import type { Message } from '@/types/message';

export function useMessages(executionId: string) {
  const queryClient = useQueryClient();
  const userRole = useAuthStore((state) => state.user?.role || 'end_user');
  const showInternal = useConversationStore((state) => state.showInternal);

  // Fetch messages
  const { data: allMessages, isLoading } = useQuery<Message[]>({
    queryKey: ['messages', executionId],
    queryFn: () => messagesApi.list(executionId),
  });

  // Filter messages based on visibility
  const messages = allMessages?.filter((msg) =>
    canUserSeeMessage(msg, userRole, showInternal)
  );

  // Subscribe to real-time updates
  useEffect(() => {
    const token = getAccessToken();
    const eventSource = sseService.connect(
      `${process.env.NEXT_PUBLIC_API_URL}/sse/execution/${executionId}`,
      token
    );

    eventSource.addEventListener('message', (event) => {
      const message = JSON.parse(event.data);

      queryClient.setQueryData<Message[]>(
        ['messages', executionId],
        (old = []) => [...old, message]
      );
    });

    return () => {
      sseService.disconnect();
    };
  }, [executionId, queryClient]);

  return { messages: messages || [], isLoading };
}
```

### Step 5: Create Conversation Store

```typescript
// lib/store/conversations.ts
import { create } from 'zustand';

interface ConversationState {
  showInternal: boolean;
  selectedConversationId: string | null;
  typingAgents: Record<string, boolean>; // { agentId: isTyping }

  toggleShowInternal: () => void;
  setSelectedConversation: (id: string | null) => void;
  setAgentTyping: (agentId: string, isTyping: boolean) => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
  showInternal: false,
  selectedConversationId: null,
  typingAgents: {},

  toggleShowInternal: () =>
    set((state) => ({ showInternal: !state.showInternal })),

  setSelectedConversation: (id) =>
    set({ selectedConversationId: id }),

  setAgentTyping: (agentId, isTyping) =>
    set((state) => ({
      typingAgents: { ...state.typingAgents, [agentId]: isTyping },
    })),
}));
```

### Step 6: Create Message Components

```typescript
// components/messages/Message.tsx
'use client';

import { formatDistanceToNow } from 'date-fns';
import { MessageAvatar } from './MessageAvatar';
import { MessageContent } from './MessageContent';
import { MessageReactions } from './MessageReactions';
import { ThreadButton } from './ThreadButton';
import { Badge } from '@/components/ui/badge';
import type { Message as MessageType } from '@/types/message';

interface MessageProps {
  message: MessageType;
  onThreadClick?: () => void;
}

export function Message({ message, onThreadClick }: MessageProps) {
  const visibilityColors = {
    public: 'bg-blue-100 text-blue-800',
    internal: 'bg-gray-100 text-gray-800',
    system: 'bg-purple-100 text-purple-800',
  };

  return (
    <div className="flex items-start gap-3 p-4 hover:bg-gray-50 transition-colors">
      <MessageAvatar
        name={message.sender_name}
        role={message.sender_role}
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-semibold text-sm">{message.sender_name}</span>
          <Badge className={`text-xs ${visibilityColors[message.visibility]}`}>
            {message.visibility}
          </Badge>
          <span className="text-xs text-gray-500">
            {formatDistanceToNow(new Date(message.created_at), { addSuffix: true })}
          </span>
        </div>

        <MessageContent content={message.content} />

        <div className="mt-2 flex items-center gap-2">
          <MessageReactions
            reactions={message.reactions || {}}
            onReact={(emoji) => {
              // Handle reaction
            }}
          />

          {message.has_replies && (
            <ThreadButton
              replyCount={message.reply_count}
              onClick={onThreadClick}
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

### Step 7: Create Message Input

```typescript
// components/messages/MessageInput.tsx
'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { messagesApi } from '@/lib/api/messages';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send } from 'lucide-react';

interface MessageInputProps {
  executionId: string;
  recipientId?: string;
  recipientName?: string;
  onSent?: () => void;
}

export function MessageInput({
  executionId,
  recipientId,
  recipientName,
  onSent,
}: MessageInputProps) {
  const [content, setContent] = useState('');
  const queryClient = useQueryClient();

  const sendMutation = useMutation({
    mutationFn: (data: { content: string }) =>
      messagesApi.send(executionId, {
        content: data.content,
        recipient_id: recipientId,
        message_type: 'question',
      }),
    onSuccess: () => {
      setContent('');
      queryClient.invalidateQueries(['messages', executionId]);
      onSent?.();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (content.trim()) {
      sendMutation.mutate({ content });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 border-t">
      {recipientName && (
        <div className="text-sm text-gray-600 mb-2">
          Sending to: <span className="font-medium">{recipientName}</span>
        </div>
      )}

      <div className="flex gap-2">
        <Textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Type your message..."
          className="flex-1 resize-none"
          rows={3}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <Button
          type="submit"
          disabled={!content.trim() || sendMutation.isPending}
          className="self-end"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
```

### Step 8: Create Visibility Toggle

```typescript
// components/conversations/VisibilityToggle.tsx
'use client';

import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { useConversationStore } from '@/lib/store/conversations';
import { Eye, EyeOff } from 'lucide-react';

export function VisibilityToggle() {
  const showInternal = useConversationStore((state) => state.showInternal);
  const toggleShowInternal = useConversationStore((state) => state.toggleShowInternal);

  return (
    <div className="flex items-center gap-2 p-4 border-b">
      <div className="flex items-center gap-2 flex-1">
        {showInternal ? (
          <Eye className="h-4 w-4 text-gray-600" />
        ) : (
          <EyeOff className="h-4 w-4 text-gray-400" />
        )}
        <Label htmlFor="show-internal" className="cursor-pointer">
          Show internal conversations
        </Label>
      </div>
      <Switch
        id="show-internal"
        checked={showInternal}
        onCheckedChange={toggleShowInternal}
      />
    </div>
  );
}
```

### Step 9: Create Conversation Page

```typescript
// app/(dashboard)/tasks/[id]/conversations/page.tsx
'use client';

import { useParams } from 'next/navigation';
import { useMessages } from '@/lib/hooks/useMessages';
import { useTaskDetail } from '@/lib/hooks/useTaskDetail';
import { Message } from '@/components/messages/Message';
import { MessageInput } from '@/components/messages/MessageInput';
import { VisibilityToggle } from '@/components/conversations/VisibilityToggle';
import { useAuthStore } from '@/lib/store/auth';

export default function ConversationsPage() {
  const params = useParams();
  const taskId = params.id as string;

  const { task } = useTaskDetail(taskId);
  const { messages, isLoading } = useMessages(taskId);
  const user = useAuthStore((state) => state.user);

  // Get PM or Tech Lead for user to chat with
  const pmAgent = task?.squad?.members?.find((m) => m.role === 'project_manager');

  return (
    <div className="flex flex-col h-[calc(100vh-64px)]">
      <div className="border-b p-4">
        <h2 className="text-2xl font-bold">Conversations</h2>
        <p className="text-gray-600 mt-1">Chat with your AI team</p>
      </div>

      <VisibilityToggle />

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div>Loading...</div>
        ) : (
          messages.map((message) => (
            <Message key={message.id} message={message} />
          ))
        )}
      </div>

      {pmAgent && (
        <MessageInput
          executionId={taskId}
          recipientId={pmAgent.id}
          recipientName={pmAgent.name}
        />
      )}
    </div>
  );
}
```

---

## Todo List

### P0 - Critical Path

- [ ] Create message and conversation types
- [ ] Create message visibility utility functions
- [ ] Create messages API client
- [ ] Create useMessages hook with filtering
- [ ] Create conversation store (Zustand)
- [ ] Build Message component
- [ ] Build MessageAvatar component
- [ ] Build MessageContent component
- [ ] Build MessageInput component
- [ ] Build VisibilityToggle component
- [ ] Build conversations page
- [ ] Implement real-time message delivery
- [ ] Test visibility filtering (end user vs developer)
- [ ] Add message reactions
- [ ] Add typing indicators

### P1 - Important

- [ ] Build ThreadPanel component
- [ ] Build ThreadMessage component
- [ ] Implement message threading (tree structure)
- [ ] Add conversation search
- [ ] Add unread message indicators
- [ ] Add "jump to latest" button
- [ ] Build ThoughtViewer component
- [ ] Add message timestamps (relative + absolute)
- [ ] Implement virtualization for 1000+ messages
- [ ] Add mobile-responsive layout

### P2 - Nice to Have

- [ ] Add message editing
- [ ] Add message deletion
- [ ] Add file attachments
- [ ] Add code snippet formatting
- [ ] Add emoji picker for reactions
- [ ] Add @mentions
- [ ] Add conversation pinning
- [ ] Add conversation archiving

---

## Success Criteria

### Functional Criteria
✅ End users ONLY see public messages (PM/Tech Lead)
✅ Developers can toggle internal message visibility
✅ Real-time messages appear instantly
✅ Typing indicators show when agents responding
✅ Message threading displays correctly
✅ User can send messages to PM/Tech Lead

### Technical Criteria
✅ Message visibility filtering works correctly
✅ SSE delivers messages in real-time
✅ Message list virtualization handles 1000+ messages
✅ TypeScript types match backend schemas
✅ Component re-renders optimized

### Performance Criteria
✅ Message delivery latency < 200ms
✅ Message list renders 1000 messages < 500ms
✅ Typing indicator updates < 100ms

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Visibility filtering bugs | High | Critical | Comprehensive testing, unit tests |
| Message ordering issues | Medium | High | Timestamp-based ordering, server authority |
| Threading complexity | High | Medium | Start with linear, add tree later |
| Real-time sync conflicts | Medium | High | Optimistic updates + conflict resolution |

---

## Security Considerations

### Critical Security
- **Visibility enforcement**: Backend MUST validate visibility rules
- **Message authorization**: Verify sender/recipient permissions
- **Content sanitization**: Prevent XSS in message content
- **Rate limiting**: Prevent message spam

---

## Next Steps

After completing Phase 4:
1. **Review**: Ensure all P0 todos completed
2. **Test**: Visibility filtering with different user roles
3. **Proceed**: Start Phase 5 (Polish & Performance)
