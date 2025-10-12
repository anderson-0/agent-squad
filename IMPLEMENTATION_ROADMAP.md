# Agent Squad - Detailed Implementation Roadmap

This document provides a detailed, actionable roadmap for implementing the Agent Squad SaaS platform.

## 🎯 Overview

**Total Timeline**: 16-18 weeks (4-4.5 months)
**Team Size**: Can be built by a small team (2-4 developers) or solo
**Tech Stack**: Python/FastAPI backend, Next.js frontend, AWS infrastructure

---

## Phase 1: Foundation & Setup (Week 1)

### Goals
- Set up development environment
- Initialize project structure
- Configure tooling and dependencies

### Tasks

#### Backend Setup
```bash
# Create project structure
mkdir -p agent-squad/{backend,frontend,infrastructure,docs}
cd agent-squad/backend

# Initialize Python project with poetry
poetry init
poetry add fastapi uvicorn[standard] sqlalchemy prisma-client-py \
           pydantic-settings python-jose passlib bcrypt \
           openai pinecone-client inngest stripe

poetry add --dev pytest pytest-asyncio pytest-cov black ruff mypy

# Create folder structure
mkdir -p api/{v1/endpoints,deps} core models schemas services \
         agents workflows integrations db tests
```

#### Frontend Setup
```bash
cd ../frontend

# Create Next.js app
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir

# Install dependencies
npm install @tanstack/react-query zustand zod react-hook-form \
            @hookform/resolvers axios sonner @radix-ui/react-* \
            class-variance-authority clsx tailwind-merge

npm install -D @types/node @types/react prettier eslint-config-prettier
```

#### Database Setup
```bash
# Initialize Prisma
cd backend
npx prisma init

# Create schema (see schema below)
# Edit prisma/schema.prisma
```

**Prisma Schema**:
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-py"
}

model User {
  id              String   @id @default(uuid())
  email           String   @unique
  name            String
  passwordHash    String
  stripeCustomerId String?
  planTier        String   @default("starter") // starter, pro, enterprise
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  organizations   Organization[]
  squads          Squad[]

  @@map("users")
}

model Organization {
  id        String   @id @default(uuid())
  name      String
  ownerId   String
  createdAt DateTime @default(now())

  owner     User     @relation(fields: [ownerId], references: [id])
  squads    Squad[]

  @@map("organizations")
}

model Squad {
  id        String   @id @default(uuid())
  orgId     String
  name      String
  status    String   @default("active") // active, paused, archived
  config    Json     // Squad configuration
  createdAt DateTime @default(now())

  organization   Organization   @relation(fields: [orgId], references: [id])
  members        SquadMember[]
  projects       Project[]
  taskExecutions TaskExecution[]

  @@map("squads")
}

model SquadMember {
  id            String   @id @default(uuid())
  squadId       String
  role          String   // project_manager, backend_developer, etc.
  llmProvider   String   @default("openai") // openai, anthropic, etc.
  llmModel      String   @default("gpt-4")
  systemPrompt  String   @db.Text
  config        Json     // Additional configuration
  createdAt     DateTime @default(now())

  squad         Squad    @relation(fields: [squadId], references: [id])
  sentMessages  AgentMessage[] @relation("SentMessages")
  receivedMessages AgentMessage[] @relation("ReceivedMessages")

  @@map("squad_members")
}

model Project {
  id              String   @id @default(uuid())
  squadId         String
  name            String
  gitRepoUrl      String?
  gitProvider     String?  // github, gitlab, bitbucket
  ticketSystemUrl String?
  createdAt       DateTime @default(now())

  squad           Squad    @relation(fields: [squadId], references: [id])
  tasks           Task[]
  integrations    Integration[]

  @@map("projects")
}

model Task {
  id          String   @id @default(uuid())
  projectId   String
  externalId  String?  // ID from Jira, etc.
  title       String
  description String   @db.Text
  status      String   @default("pending") // pending, in_progress, blocked, completed
  priority    String   @default("medium") // low, medium, high, urgent
  assignedTo  String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  project     Project  @relation(fields: [projectId], references: [id])
  executions  TaskExecution[]

  @@map("tasks")
}

model TaskExecution {
  id          String   @id @default(uuid())
  taskId      String
  squadId     String
  status      String   @default("pending") // pending, in_progress, completed, failed, blocked
  startedAt   DateTime?
  completedAt DateTime?
  logs        Json     // Execution logs
  createdAt   DateTime @default(now())

  task        Task     @relation(fields: [taskId], references: [id])
  squad       Squad    @relation(fields: [squadId], references: [id])
  messages    AgentMessage[]
  feedback    Feedback?

  @@map("task_executions")
}

model AgentMessage {
  id              String   @id @default(uuid())
  taskExecutionId String
  senderId        String
  recipientId     String?  // null for broadcast
  content         String   @db.Text
  messageType     String   // task_assignment, question, response, etc.
  metadata        Json?
  createdAt       DateTime @default(now())

  taskExecution   TaskExecution @relation(fields: [taskExecutionId], references: [id])
  sender          SquadMember   @relation("SentMessages", fields: [senderId], references: [id])
  recipient       SquadMember?  @relation("ReceivedMessages", fields: [recipientId], references: [id])

  @@map("agent_messages")
}

model Feedback {
  id              String   @id @default(uuid())
  taskExecutionId String   @unique
  userId          String
  rating          Int      // 1-5
  comments        String   @db.Text
  createdAt       DateTime @default(now())

  taskExecution   TaskExecution @relation(fields: [taskExecutionId], references: [id])

  @@map("feedback")
}

model LearningInsight {
  id             String   @id @default(uuid())
  squadId        String
  insightText    String   @db.Text
  embedding      Float[]  // Vector embedding for Pinecone
  sourceFeedbackId String?
  createdAt      DateTime @default(now())

  @@map("learning_insights")
}

model Integration {
  id          String   @id @default(uuid())
  projectId   String
  type        String   // git, jira, etc.
  credentials String   @db.Text // Encrypted
  config      Json
  createdAt   DateTime @default(now())

  project     Project  @relation(fields: [projectId], references: [id])
  webhooks    Webhook[]

  @@map("integrations")
}

model Webhook {
  id            String   @id @default(uuid())
  integrationId String
  eventType     String
  secret        String
  url           String
  createdAt     DateTime @default(now())

  integration   Integration @relation(fields: [integrationId], references: [id])

  @@map("webhooks")
}
```

### Deliverables
- ✅ Project structure created
- ✅ Dependencies installed
- ✅ Database schema designed
- ✅ Development environment ready

---

## Phase 2: Authentication & Payments (Weeks 2-3)

### Tasks

#### BetterAuth Integration
```python
# backend/core/auth.py
from better_auth import BetterAuth
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

auth = BetterAuth(secret_key=settings.BETTERAUTH_SECRET)
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    payload = auth.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.user.find_unique(where={"id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

#### Stripe Integration
```python
# backend/services/stripe_service.py
import stripe
from typing import Optional

class StripeService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create_customer(self, email: str, name: str) -> str:
        customer = stripe.Customer.create(email=email, name=name)
        return customer.id

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str
    ):
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session

    async def handle_webhook(self, payload: bytes, sig_header: str):
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

        if event.type == "checkout.session.completed":
            # Handle successful checkout
            pass
        elif event.type == "customer.subscription.deleted":
            # Handle subscription cancellation
            pass

        return {"status": "success"}
```

### Deliverables
- ✅ User registration and login
- ✅ JWT token authentication
- ✅ Stripe checkout flow
- ✅ Subscription management
- ✅ Webhook handling

---

## Phase 3: Agent Framework Integration (Weeks 4-5)

### Tasks

#### Integrate agno-agi Framework
```python
# backend/agents/base_agent.py
from agno import Agent, Context
from typing import List, Dict, Any
import openai

class BaseSquadAgent(Agent):
    def __init__(
        self,
        role: str,
        system_prompt: str,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4"
    ):
        self.role = role
        self.system_prompt = system_prompt
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.client = self._init_llm_client()

    def _init_llm_client(self):
        if self.llm_provider == "openai":
            return openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        elif self.llm_provider == "anthropic":
            # Initialize Anthropic client
            pass
        # Add more providers

    async def process_message(
        self,
        message: str,
        context: Dict[str, Any],
        conversation_history: List[Dict]
    ) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            *conversation_history,
            {"role": "user", "content": message}
        ]

        response = await self.client.chat.completions.create(
            model=self.llm_model,
            messages=messages,
            temperature=0.7
        )

        return response.choices[0].message.content

# Load prompts from files
def load_agent_prompt(role: str, specialization: str = None) -> str:
    filename = f"roles/{role}/"
    if specialization:
        filename += f"{specialization}.md"
    else:
        filename += "default_prompt.md"

    with open(filename, 'r') as f:
        return f.read()
```

#### Agent Factory
```python
# backend/agents/factory.py
from backend.agents.base_agent import BaseSquadAgent, load_agent_prompt

class AgentFactory:
    @staticmethod
    def create_agent(
        role: str,
        specialization: str = None,
        llm_provider: str = "openai",
        llm_model: str = "gpt-4"
    ) -> BaseSquadAgent:
        system_prompt = load_agent_prompt(role, specialization)

        return BaseSquadAgent(
            role=role,
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            llm_model=llm_model
        )
```

### Deliverables
- ✅ Base agent class implemented
- ✅ Agent factory for creating agents
- ✅ Multi-LLM provider support
- ✅ Agent prompt loading system

---

## Phase 4: Inngest Workflows (Weeks 6-7)

### Tasks

#### Task Execution Workflow
```python
# backend/workflows/task_execution.py
from inngest import Inngest, Event
from backend.agents.factory import AgentFactory

inngest = Inngest(app_id="agent-squad")

@inngest.create_function(
    fn_id="execute-task",
    trigger=inngest.trigger.event("squad/task.assigned")
)
async def execute_task(ctx, step):
    event = ctx.event
    task_id = event.data["task_id"]
    squad_id = event.data["squad_id"]

    # Step 1: Load task and squad
    task, squad = await step.run(
        "load-task-squad",
        lambda: load_task_and_squad(task_id, squad_id)
    )

    # Step 2: PM analyzes task
    pm_agent = await step.run(
        "create-pm-agent",
        lambda: AgentFactory.create_agent("project_manager")
    )

    analysis = await step.run(
        "analyze-task",
        lambda: pm_agent.process_message(
            f"Analyze this task and create execution plan: {task.description}",
            context={"task": task, "squad": squad},
            conversation_history=[]
        )
    )

    # Step 3: Delegate to team members
    sub_tasks = parse_sub_tasks(analysis)

    for sub_task in sub_tasks:
        await step.send_event(
            "agent-collaboration",
            {
                "name": "squad/agent.collaborate",
                "data": {
                    "task_execution_id": ctx.event.data["task_execution_id"],
                    "sub_task": sub_task
                }
            }
        )

    return {"status": "delegated", "sub_tasks": len(sub_tasks)}
```

### Deliverables
- ✅ Inngest configured
- ✅ Task execution workflow
- ✅ Agent collaboration workflow
- ✅ Error handling and retries

---

## Phase 5: RAG System (Week 8)

### Tasks

#### Pinecone Setup
```python
# backend/services/rag_service.py
from pinecone import Pinecone, ServerlessSpec
import openai

class RAGService:
    def __init__(self, index_name: str):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(index_name)
        self.openai_client = openai.AsyncOpenAI()

    async def ingest_documents(self, squad_id: str, documents: List[Dict]):
        vectors = []

        for doc in documents:
            embedding = await self._generate_embedding(doc['content'])

            vectors.append({
                'id': f"{squad_id}_{doc['id']}",
                'values': embedding,
                'metadata': {
                    'squad_id': squad_id,
                    'content': doc['content'],
                    'source': doc['source'],
                    'type': doc['type']
                }
            })

        self.index.upsert(vectors=vectors, namespace=squad_id)

    async def query(self, squad_id: str, query: str, top_k: int = 5):
        query_embedding = await self._generate_embedding(query)

        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=squad_id,
            include_metadata=True
        )

        return [match['metadata']['content'] for match in results['matches']]

    async def _generate_embedding(self, text: str):
        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
```

### Deliverables
- ✅ Pinecone integration
- ✅ Document ingestion pipeline
- ✅ Context retrieval for agents
- ✅ Feedback storage system

---

## Phase 6: Frontend Dashboard (Weeks 9-11)

### Key Pages

1. **Landing Page** (`/`)
2. **Dashboard** (`/dashboard`)
3. **Squad Builder** (`/squads/new`)
4. **Squad Detail** (`/squads/[id]`)
5. **Task Board** (`/squads/[id]/tasks`)
6. **Real-time Messages** (`/squads/[id]/messages`)
7. **Settings** (`/settings`)

### Real-time Updates (SSE)
```typescript
// hooks/use-agent-messages.ts
'use client';

import { useEffect, useState } from 'react';

export function useAgentMessages(taskExecutionId: string) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const eventSource = new EventSource(
      `/api/task-executions/${taskExecutionId}/messages/stream`
    );

    eventSource.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setMessages((prev) => [...prev, message]);
    };

    return () => eventSource.close();
  }, [taskExecutionId]);

  return messages;
}
```

### Deliverables
- ✅ Beautiful UI (inspired by Motion)
- ✅ Squad builder interface
- ✅ Real-time message viewer
- ✅ Task board
- ✅ Responsive design

---

## Phase 7: Testing & Deployment (Weeks 12-14)

### Testing
```bash
# Backend tests
pytest tests/ --cov=backend --cov-report=html

# Frontend tests
npm run test
npm run test:e2e
```

### Kubernetes Deployment
```yaml
# infrastructure/k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: your-registry/backend:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: backend-secrets
              key: database-url
```

### Deliverables
- ✅ Comprehensive test suite
- ✅ CI/CD pipeline
- ✅ Kubernetes deployment
- ✅ Monitoring setup
- ✅ Production launch

---

## 🚀 Quick Start for MVP

For rapid prototyping, focus on:

1. **Week 1**: Basic setup + Authentication
2. **Week 2**: Single agent type (Project Manager only)
3. **Week 3**: Simple task execution (no Inngest, direct execution)
4. **Week 4**: Basic frontend dashboard
5. **Week 5**: Test with real tasks

Then iterate and add features incrementally.

---

## 📚 Additional Resources

- FastAPI Documentation: https://fastapi.tiangolo.com/
- Next.js Documentation: https://nextjs.org/docs
- Inngest Documentation: https://www.inngest.com/docs
- Agno Framework: https://github.com/agno-agi/agnoframework
- Pinecone Documentation: https://docs.pinecone.io/

---

## 🤔 Key Decision Points

### 1. Should we build our own agent framework or use agno-agi?
**Recommendation**: Use agno-agi initially, can customize later if needed.

### 2. How to handle agent context windows?
**Recommendation**: Implement RAG + summarization for long conversations.

### 3. How to price based on LLM costs?
**Recommendation**: Track usage, set reasonable limits per tier, optimize prompts.

### 4. How to ensure agent quality?
**Recommendation**: Extensive testing, feedback loop, continuous prompt improvement.

---

**Ready to build? Start with Phase 1! 🚀**
