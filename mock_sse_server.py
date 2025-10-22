#!/usr/bin/env python3
"""
Mock SSE Server for CLI Testing

A simple SSE server that generates mock agent messages to test the CLI client.
No database or full backend required - just pure SSE streaming.

Usage:
    # Terminal 1: Start the mock server
    python mock_sse_server.py

    # Terminal 2: Run the CLI client
    python -m backend.cli.stream_agent_messages \
      --execution-id test-execution-123 \
      --base-url http://localhost:8000 \
      --token dummy-token
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import time
import threading
from uuid import uuid4
from datetime import datetime


class SSEHandler(BaseHTTPRequestHandler):
    """Simple SSE handler"""

    def do_GET(self):
        """Handle GET requests"""
        if self.path.startswith('/api/v1/sse/execution/'):
            self.handle_sse()
        elif self.path == '/api/v1/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
        else:
            self.send_error(404)

    def handle_sse(self):
        """Handle SSE streaming"""
        print(f"📡 Client connected: {self.client_address}")

        # Send SSE headers
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Send initial connection message
        self.send_sse_event('connected', {'message': 'Connected to stream'})

        # Start sending test messages
        self.send_test_conversation()

    def send_sse_event(self, event: str, data: dict):
        """Send an SSE event"""
        try:
            message = f"event: {event}\n"
            message += f"data: {json.dumps(data)}\n\n"
            self.wfile.write(message.encode('utf-8'))
            self.wfile.flush()
        except Exception as e:
            print(f"❌ Error sending event: {e}")

    def send_test_conversation(self):
        """Send a realistic conversation between agents"""
        execution_id = "test-execution-123"
        backend_dev_id = str(uuid4())
        tech_lead_id = str(uuid4())

        # Realistic conversation
        messages = [
            {
                "delay": 1,
                "message_id": str(uuid4()),
                "sender_id": backend_dev_id,
                "sender_role": "backend_developer",
                "sender_name": "Backend Dev (FastAPI)",
                "sender_specialization": "python_fastapi",
                "recipient_id": tech_lead_id,
                "recipient_role": "tech_lead",
                "recipient_name": "Tech Lead",
                "content": "How should I implement caching for the user API? We're seeing response times of 2-3 seconds.",
                "message_type": "question",
                "metadata": {"priority": "high"},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            },
            {
                "delay": 2,
                "message_id": str(uuid4()),
                "sender_id": tech_lead_id,
                "sender_role": "tech_lead",
                "sender_name": "Tech Lead",
                "recipient_id": backend_dev_id,
                "recipient_role": "backend_developer",
                "recipient_name": "Backend Dev (FastAPI)",
                "content": "Use Redis for caching. Here's why:\n- Fast in-memory storage\n- TTL support for automatic expiration\n- Industry standard for API caching\n\nCache user data with 5-minute TTL. Invalidate on updates.",
                "message_type": "answer",
                "metadata": {},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            },
            {
                "delay": 3,
                "message_id": str(uuid4()),
                "sender_id": backend_dev_id,
                "sender_role": "backend_developer",
                "sender_name": "Backend Dev (FastAPI)",
                "sender_specialization": "python_fastapi",
                "recipient_id": tech_lead_id,
                "recipient_role": "tech_lead",
                "recipient_name": "Tech Lead",
                "content": "Progress: 25% | Status: In Progress\nImplemented Redis caching layer with 5-minute TTL.\nNext: Testing cache invalidation logic.",
                "message_type": "status_update",
                "metadata": {"progress": 25},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            },
            {
                "delay": 2,
                "message_id": str(uuid4()),
                "sender_id": tech_lead_id,
                "sender_role": "tech_lead",
                "sender_name": "Tech Lead",
                "recipient_id": backend_dev_id,
                "recipient_role": "backend_developer",
                "recipient_name": "Backend Dev (FastAPI)",
                "content": "Did you add cache invalidation on user updates? That's critical for data consistency.",
                "message_type": "question",
                "metadata": {},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            },
            {
                "delay": 2,
                "message_id": str(uuid4()),
                "sender_id": backend_dev_id,
                "sender_role": "backend_developer",
                "sender_name": "Backend Dev (FastAPI)",
                "sender_specialization": "python_fastapi",
                "recipient_id": tech_lead_id,
                "recipient_role": "tech_lead",
                "recipient_name": "Tech Lead",
                "content": "Yes! Added cache invalidation in the update_user() endpoint. Also added tests to verify cache is cleared on updates.",
                "message_type": "answer",
                "metadata": {},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            },
            {
                "delay": 2,
                "message_id": str(uuid4()),
                "sender_id": backend_dev_id,
                "sender_role": "backend_developer",
                "sender_name": "Backend Dev (FastAPI)",
                "sender_specialization": "python_fastapi",
                "recipient_id": tech_lead_id,
                "recipient_role": "tech_lead",
                "recipient_name": "Tech Lead",
                "content": "Code review needed!\n\nPR: https://github.com/org/repo/pull/123\nChanges: Added Redis caching for user API\n\nImplemented:\n✓ Redis cache layer\n✓ 5-minute TTL\n✓ Cache invalidation on updates\n✓ Unit tests (95% coverage)\n✓ Integration tests\n\nResponse times improved from 2.5s → 150ms!",
                "message_type": "code_review_request",
                "metadata": {"pr_number": 123},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            },
            {
                "delay": 3,
                "message_id": str(uuid4()),
                "sender_id": tech_lead_id,
                "sender_role": "tech_lead",
                "sender_name": "Tech Lead",
                "recipient_id": backend_dev_id,
                "recipient_role": "backend_developer",
                "recipient_name": "Backend Dev (FastAPI)",
                "content": "Code Review: APPROVED ✅\n\nGreat work! A few observations:\n\n✅ Excellent cache implementation\n✅ Good test coverage\n✅ Proper error handling\n\n💡 Minor suggestion: Consider adding cache warming for frequently accessed users.\n\nReady to merge!",
                "message_type": "code_review_response",
                "metadata": {"approved": True},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            },
            {
                "delay": 2,
                "message_id": str(uuid4()),
                "sender_id": backend_dev_id,
                "sender_role": "backend_developer",
                "sender_name": "Backend Dev (FastAPI)",
                "sender_specialization": "python_fastapi",
                "recipient_id": None,
                "recipient_role": "broadcast",
                "recipient_name": "All Agents",
                "content": "🎉 Task completed!\n\nImplemented Redis caching for user API:\n- Response times: 2.5s → 150ms (94% improvement)\n- Cache hit rate: ~85%\n- Zero data consistency issues\n- Full test coverage\n\nPR merged to main. Ready for deployment!",
                "message_type": "task_completion",
                "metadata": {"completed": True},
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_thread_id": "thread-auth-123"
            }
        ]

        print()
        print("=" * 70)
        print("  SIMULATING AGENT CONVERSATION")
        print("=" * 70)
        print()

        for i, msg in enumerate(messages, 1):
            # Wait before sending
            time.sleep(msg["delay"])

            # Remove delay from message before sending
            msg_copy = msg.copy()
            del msg_copy["delay"]

            # Send the message
            print(f"📨 Sending message {i}/{len(messages)}: {msg['message_type']}")
            print(f"   {msg['sender_name']} → {msg['recipient_name']}")
            print(f"   {msg['content'][:50]}...")
            print()

            self.send_sse_event('message', msg_copy)

        print("=" * 70)
        print("✅ All messages sent! Keeping connection alive...")
        print("=" * 70)
        print()

        # Keep connection alive with heartbeats
        try:
            while True:
                time.sleep(15)
                self.send_sse_event('heartbeat', {'timestamp': datetime.utcnow().isoformat()})
        except Exception:
            print(f"📡 Client disconnected: {self.client_address}")

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def run_server(port=8000):
    """Run the mock SSE server"""
    server = HTTPServer(('localhost', port), SSEHandler)

    print()
    print("=" * 70)
    print("  MOCK SSE SERVER FOR CLI TESTING")
    print("=" * 70)
    print()
    print(f"🚀 Server running on http://localhost:{port}")
    print()
    print("📡 SSE endpoint: http://localhost:{port}/api/v1/sse/execution/test-execution-123")
    print()
    print("🎯 TO TEST THE CLI:")
    print("   Open another terminal and run:")
    print()
    print("   python -m backend.cli.stream_agent_messages \\")
    print("     --execution-id test-execution-123 \\")
    print("     --base-url http://localhost:8000 \\")
    print("     --token dummy-token")
    print()
    print("=" * 70)
    print()
    print("Press Ctrl+C to stop the server")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down server...")
        server.shutdown()


if __name__ == '__main__':
    run_server()
