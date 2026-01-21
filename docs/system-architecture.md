# System Architecture - Agent-Squad

## Overview

Agent-Squad uses a microservices-inspired architecture with clear separation between frontend, backend, and infrastructure layers. The system orchestrates multiple AI agents using discovery-driven workflows.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Infrastructure│
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Docker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React         │    │   Agent System  │    │   PostgreSQL    │
│   Components    │    │   (Agno)        │    │   Redis         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Architecture

### Frontend Layer
- **Framework:** Next.js 16 with React 19
- **Styling:** Tailwind CSS v4 with shadcn/ui
- **State Management:** Zustand + TanStack Query
- **Real-time:** Server-Sent Events (SSE)

### Backend Layer
- **API Framework:** FastAPI with async support
- **Agent Framework:** Agno for orchestration
- **Database:** PostgreSQL with SQLAlchemy
- **Message Bus:** NATS JetStream
- **Background Tasks:** Celery + Redis

### Agent System
- **Base Class:** AgnoSquadAgent (1,409 LOC)
- **Specialized Agents:** 12 different roles
- **Communication:** NATS message bus
- **Orchestration:** Phase-based workflows
- **Discovery:** Opportunity detection engine

## Data Flow

```
User Request → Frontend → Backend API → Agent System → LLM Providers
     ▲           │           │            │              │
     └───────────┴───────────┴────────────┴─────NATS─────┘
```

## Key Features

### Discovery-Driven Workflows
- Agents spawn tasks dynamically during work
- ML-enhanced opportunity detection
- Value scoring for discovered tasks
- Rationale-based task creation

### Multi-Agent Orchestration
- 12 specialized agent roles
- NATS-based communication
- Conflict resolution mechanisms
- Collaborative task execution

### Real-Time Collaboration
- Live Kanban boards
- SSE streaming updates
- Multi-turn conversations
- Agent status monitoring

## Technology Stack

### Core Technologies
- **Python 3.11+** - Backend development
- **TypeScript** - Frontend development
- **PostgreSQL** - Primary database
- **Redis** - Caching and task queue
- **NATS** - Message broker

### AI/ML Stack
- **Agno** - Agent orchestration framework
- **OpenAI** - GPT models
- **Anthropic** - Claude models
- **Groq** - Fast inference
- **Ollama** - Local models

### Development Tools
- **Docker** - Containerization
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **Inngest** - Durable execution
- **E2B** - Code sandboxing

## Scalability Design

### Horizontal Scaling
- Stateless API servers
- Shared database layer
- Distributed message queue
- Caching layer

### Performance Optimization
- Connection pooling
- Async processing
- Database indexing
- Redis caching

## Security Architecture

### Authentication
- JWT with refresh tokens
- HTTP-only cookies
- CSRF protection
- Rate limiting

### Data Protection
- Encryption at rest
- TLS in transit
- Input validation
- SQL injection prevention

## Monitoring & Observability

### Metrics
- Application performance
- Agent activity
- Task completion rates
- System health

### Logging
- Structured logging with structlog
- Centralized log aggregation
- Error tracking
- Performance monitoring

This architecture supports production deployment with enterprise-grade reliability and scalability.
