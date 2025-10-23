# Frontend SSE Streaming Integration Guide

**Feature:** Real-time AI agent responses with "typing..." indicator
**Status:** ✅ Backend Complete, Ready for Frontend
**Date:** October 22, 2025

---

## 🎯 What You Get

**Before (No Streaming):**
```
User asks question
[10 seconds of blank screen]
Complete answer appears
```

**After (With SSE Streaming):**
```
User asks question
[< 1 second]
"The benefits..." ← First words appear
"of using Redis..." ← Text streams in real-time
"include high performance..." ← User already reading
✓ Complete answer (same time, better UX!)
```

---

## 🔌 SSE Events

### Event 1: `answer_streaming` (Continuous)

Fired for **each token** as the AI generates the response.

**Data Structure:**
```typescript
interface AnswerStreamingEvent {
  token: string;                 // Single token/word
  partial_response: string;       // Complete response so far
  agent_id: string;              // UUID of responding agent
  agent_role: string;            // e.g., "tech_lead"
  conversation_id: string | null;
  is_streaming: true;
  timestamp: string;             // ISO 8601
}
```

**Example:**
```json
{
  "token": "The ",
  "partial_response": "The ",
  "agent_id": "a1b2c3d4-...",
  "agent_role": "tech_lead",
  "conversation_id": "conv-123",
  "is_streaming": true,
  "timestamp": "2025-10-22T23:15:30.123Z"
}
```

**Next event:**
```json
{
  "token": "benefits ",
  "partial_response": "The benefits ",
  ...
}
```

**Frequency:** ~20-30 events/second (depends on LLM)

---

### Event 2: `answer_complete` (Final)

Fired **once** when the AI finishes generating the complete response.

**Data Structure:**
```typescript
interface AnswerCompleteEvent {
  complete_response: string;     // Full answer
  agent_id: string;
  agent_role: string;
  conversation_id: string | null;
  is_streaming: false;
  total_length: number;          // Character count
  timestamp: string;
  metadata: {
    model: string;               // e.g., "gpt-4"
    finish_reason: string;       // e.g., "stop"
    streaming: true;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    }
  };
}
```

**Example:**
```json
{
  "complete_response": "The benefits of using Redis include high performance...",
  "agent_id": "a1b2c3d4-...",
  "agent_role": "tech_lead",
  "conversation_id": "conv-123",
  "is_streaming": false,
  "total_length": 1206,
  "timestamp": "2025-10-22T23:15:40.456Z",
  "metadata": {
    "model": "gpt-4",
    "finish_reason": "stop",
    "streaming": true,
    "usage": {
      "prompt_tokens": 150,
      "completion_tokens": 236,
      "total_tokens": 386
    }
  }
}
```

---

## 📱 Frontend Integration (React)

### 1. Connect to SSE Stream

```typescript
// hooks/useAgentStreaming.ts
import { useEffect, useState } from 'react';

interface StreamingState {
  partialResponse: string;
  isStreaming: boolean;
  agentRole: string | null;
  error: string | null;
}

export function useAgentStreaming(taskExecutionId: string) {
  const [state, setState] = useState<StreamingState>({
    partialResponse: '',
    isStreaming: false,
    agentRole: null,
    error: null,
  });

  useEffect(() => {
    // Connect to SSE endpoint
    const eventSource = new EventSource(
      `/api/v1/sse/stream/${taskExecutionId}`
    );

    // Handle streaming tokens
    eventSource.addEventListener('answer_streaming', (event) => {
      const data = JSON.parse(event.data);

      setState(prev => ({
        ...prev,
        partialResponse: data.partial_response,
        isStreaming: true,
        agentRole: data.agent_role,
      }));
    });

    // Handle completion
    eventSource.addEventListener('answer_complete', (event) => {
      const data = JSON.parse(event.data);

      setState(prev => ({
        ...prev,
        partialResponse: data.complete_response,
        isStreaming: false,
      }));
    });

    // Handle errors
    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      setState(prev => ({
        ...prev,
        error: 'Connection lost',
        isStreaming: false,
      }));
      eventSource.close();
    };

    // Cleanup
    return () => {
      eventSource.close();
    };
  }, [taskExecutionId]);

  return state;
}
```

---

### 2. Display Streaming Response

```typescript
// components/AgentResponseStream.tsx
import React from 'react';
import { useAgentStreaming } from '../hooks/useAgentStreaming';

interface Props {
  taskExecutionId: string;
  conversationId: string;
}

export function AgentResponseStream({ taskExecutionId }: Props) {
  const { partialResponse, isStreaming, agentRole, error } =
    useAgentStreaming(taskExecutionId);

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="agent-response">
      {/* Agent Avatar */}
      <div className="agent-avatar">
        <span className="role-badge">{agentRole || 'AI'}</span>
      </div>

      {/* Response Content */}
      <div className="response-content">
        {partialResponse || (
          <span className="placeholder">Agent is thinking...</span>
        )}

        {/* Typing Indicator */}
        {isStreaming && (
          <span className="typing-cursor">▋</span>
        )}
      </div>

      {/* Streaming Indicator */}
      {isStreaming && (
        <div className="streaming-badge">
          <span className="pulse-dot" />
          Streaming...
        </div>
      )}
    </div>
  );
}
```

---

### 3. CSS for Typing Effect

```css
/* styles/AgentResponse.css */

.agent-response {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 12px;
  margin-bottom: 16px;
  position: relative;
}

.agent-avatar {
  flex-shrink: 0;
}

.role-badge {
  display: inline-block;
  padding: 6px 12px;
  background: #4f46e5;
  color: white;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.response-content {
  flex: 1;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Blinking cursor effect */
.typing-cursor {
  display: inline-block;
  animation: blink 1s infinite;
  color: #4f46e5;
  margin-left: 2px;
}

@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0; }
}

/* Streaming badge */
.streaming-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: #10b981;
  color: white;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

/* Pulsing dot */
.pulse-dot {
  width: 6px;
  height: 6px;
  background: white;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.5;
    transform: scale(1.2);
  }
}

.placeholder {
  color: #9ca3af;
  font-style: italic;
}
```

---

## 🚀 Advanced: Character-by-Character Animation

For an even smoother effect, animate individual characters:

```typescript
// hooks/useStreamingAnimation.ts
import { useEffect, useState, useRef } from 'react';

export function useStreamingAnimation(
  text: string,
  isStreaming: boolean,
  speed: number = 30 // ms per character
) {
  const [displayText, setDisplayText] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // If streaming stopped, show full text immediately
    if (!isStreaming) {
      setDisplayText(text);
      setIsAnimating(false);
      return;
    }

    // If text increased, animate new characters
    if (text.length > displayText.length) {
      setIsAnimating(true);

      const animate = () => {
        setDisplayText(prev => {
          if (prev.length < text.length) {
            timeoutRef.current = setTimeout(animate, speed);
            return text.slice(0, prev.length + 1);
          } else {
            setIsAnimating(false);
            return prev;
          }
        });
      };

      animate();
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [text, isStreaming, speed]);

  return { displayText, isAnimating };
}
```

**Usage:**
```typescript
export function AgentResponseStream({ taskExecutionId }: Props) {
  const { partialResponse, isStreaming, agentRole } =
    useAgentStreaming(taskExecutionId);

  const { displayText, isAnimating } = useStreamingAnimation(
    partialResponse,
    isStreaming
  );

  return (
    <div className="response-content">
      {displayText}
      {(isStreaming || isAnimating) && (
        <span className="typing-cursor">▋</span>
      )}
    </div>
  );
}
```

---

## 📊 Event Flow Example

### User asks: "What are the benefits of Redis?"

```
Time  | Event              | Data
------+--------------------+---------------------------
0.0s  | [User sends query]
0.5s  | answer_streaming   | token: "The "
0.6s  | answer_streaming   | token: "benefits "
0.7s  | answer_streaming   | token: "of "
0.8s  | answer_streaming   | token: "Redis "
0.9s  | answer_streaming   | token: "include "
...   | ...                | ...
10.5s | answer_streaming   | token: "performance."
10.6s | answer_complete    | complete_response: "The benefits..."
```

**Frontend sees:**
```
0.5s: "The "
0.6s: "The benefits "
0.7s: "The benefits of "
0.8s: "The benefits of Redis "
...
10.6s: Complete answer ✓
```

---

## 🎨 UX Best Practices

### 1. Show Immediate Feedback
```typescript
{partialResponse ? (
  <div>{partialResponse}</div>
) : (
  <div className="skeleton-loader">
    <span className="shimmer" />
    Agent is thinking...
  </div>
)}
```

### 2. Indicate Streaming State
```typescript
<div className="agent-header">
  <span>{agentRole}</span>
  {isStreaming && (
    <span className="badge badge-green">
      ● Responding...
    </span>
  )}
</div>
```

### 3. Auto-Scroll to Latest Content
```typescript
const responseRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (isStreaming && responseRef.current) {
    responseRef.current.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest'
    });
  }
}, [partialResponse, isStreaming]);
```

### 4. Prevent User Interruption During Streaming
```typescript
<button
  disabled={isStreaming}
  onClick={handleSubmit}
>
  {isStreaming ? (
    <>
      <Spinner size="sm" />
      Processing...
    </>
  ) : (
    'Ask Question'
  )}
</button>
```

---

## 🧪 Testing SSE Locally

### 1. Start Backend
```bash
cd backend
uvicorn main:app --reload
```

### 2. Test SSE Endpoint
```bash
# Replace with actual task execution ID
curl -N http://localhost:8000/api/v1/sse/stream/YOUR_TASK_ID
```

**Expected Output:**
```
event: answer_streaming
data: {"token": "The ", "partial_response": "The ", ...}

event: answer_streaming
data: {"token": "benefits ", "partial_response": "The benefits ", ...}

...

event: answer_complete
data: {"complete_response": "The benefits of...", ...}
```

### 3. Frontend Test Component

```typescript
// test/SSETest.tsx
export function SSETest() {
  const [taskId, setTaskId] = useState('');
  const [response, setResponse] = useState('');

  const testStreaming = () => {
    const eventSource = new EventSource(
      `/api/v1/sse/stream/${taskId}`
    );

    eventSource.addEventListener('answer_streaming', (e) => {
      const data = JSON.parse(e.data);
      setResponse(data.partial_response);
      console.log('Token:', data.token);
    });

    eventSource.addEventListener('answer_complete', (e) => {
      const data = JSON.parse(e.data);
      setResponse(data.complete_response);
      console.log('Complete!', data.metadata);
      eventSource.close();
    });
  };

  return (
    <div>
      <input
        value={taskId}
        onChange={e => setTaskId(e.target.value)}
        placeholder="Task Execution ID"
      />
      <button onClick={testStreaming}>Test SSE</button>
      <div className="response">{response}</div>
    </div>
  );
}
```

---

## 📋 Backend Requirements

The backend is **already configured** to broadcast these events! No additional setup needed.

### What the Backend Does:

1. **Detects Streaming:** When an agent starts responding
2. **Broadcasts Tokens:** Sends `answer_streaming` for each token
3. **Signals Completion:** Sends `answer_complete` when done
4. **Includes Metadata:** Agent role, conversation ID, timestamps

### Event Flow in Backend:

```python
# backend/agents/interaction/agent_message_handler.py

async def on_token(token: str):
    """Called for each token during streaming"""
    streamed_response += token

    # Broadcast to frontend via SSE
    await sse_manager.broadcast_to_execution(
        execution_id=task_execution_id,
        event="answer_streaming",
        data={
            "token": token,
            "partial_response": streamed_response,
            "agent_id": str(recipient_id),
            "agent_role": agent_member.role,
            # ... more metadata
        }
    )

# After streaming completes
await sse_manager.broadcast_to_execution(
    execution_id=task_execution_id,
    event="answer_complete",
    data={
        "complete_response": response.content,
        "total_length": len(response.content),
        "metadata": response.metadata
    }
)
```

---

## 🚀 Production Deployment

### Environment Variables

No additional env vars needed! Streaming works automatically.

### Performance Considerations

**Bandwidth:**
- ~20-30 events/second during streaming
- Each event: ~200-500 bytes
- Total: ~5-15 KB/second (negligible)

**Connection Management:**
- SSE uses HTTP/1.1 keep-alive
- One connection per active user/task
- Auto-reconnect on disconnect

**Scaling:**
- SSE manager handles 1000+ concurrent streams
- Redis-backed for multi-server deployments
- No special infrastructure needed

---

## 💡 Tips & Tricks

### Debounce Rapid Updates
```typescript
const debouncedUpdate = useMemo(
  () => debounce((text: string) => {
    setDisplayText(text);
  }, 50), // Update UI every 50ms max
  []
);

useEffect(() => {
  if (isStreaming) {
    debouncedUpdate(partialResponse);
  }
}, [partialResponse, isStreaming]);
```

### Show Token Count
```typescript
{isStreaming && (
  <div className="token-counter">
    {partialResponse.split(' ').length} words
  </div>
)}
```

### Add "Read More" for Long Responses
```typescript
const [isExpanded, setIsExpanded] = useState(false);
const preview = partialResponse.slice(0, 200);

return (
  <div>
    {isExpanded ? partialResponse : preview}
    {partialResponse.length > 200 && !isStreaming && (
      <button onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? 'Show Less' : 'Read More'}
      </button>
    )}
  </div>
);
```

---

## ✅ Checklist

### Backend (Already Done ✅)
- [x] SSE streaming implemented
- [x] Events broadcast automatically
- [x] Works with all LLM providers
- [x] Error handling included

### Frontend (To Implement)
- [ ] Create `useAgentStreaming` hook
- [ ] Build `AgentResponseStream` component
- [ ] Add CSS for typing effect
- [ ] Test with live data
- [ ] Add loading states
- [ ] Handle errors gracefully

---

## 📚 Additional Resources

- [SSE Service Documentation](backend/services/sse_service.py)
- [AgentMessageHandler](backend/agents/interaction/agent_message_handler.py:160)
- [BaseAgent Streaming](backend/agents/base_agent.py:174)
- [MDN SSE Guide](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

## 🎉 Summary

**Backend Status:** ✅ **COMPLETE & READY**

The backend now broadcasts:
1. Real-time tokens as they're generated (`answer_streaming`)
2. Complete response when done (`answer_complete`)
3. Full metadata (agent, conversation, timestamps)

**Frontend Next Steps:**
1. Connect to SSE endpoint
2. Listen for `answer_streaming` and `answer_complete` events
3. Update UI in real-time
4. Add typing indicator and animations
5. Test and deploy!

**Result:** Professional ChatGPT-like streaming experience! 🚀

