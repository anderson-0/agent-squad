# System Architecture Documentation

This document provides an overview of the Agent Squad system architecture. For detailed information, see the focused documentation in the [`docs/architecture/`](./docs/architecture/) folder.

## 📚 Architecture Documentation

### Core Architecture
- **[Architecture Overview](./docs/architecture/overview.md)** - High-level system architecture, layers, and deployment
- **[Design Principles](./docs/architecture/design-principles.md)** - SOLID principles, Clean Architecture, DDD
- **[Design Patterns](./docs/architecture/design-patterns.md)** - Creational, structural, and behavioral patterns used

### Operational Concerns
- **[Scalability](./docs/architecture/scalability.md)** - Horizontal scaling, caching, database optimization, microservices migration
- **[Performance Optimization](./docs/architecture/performance.md)** - Database, API, LLM, and frontend performance

### Additional Documentation (Coming Soon)
- **System Components** - Detailed component breakdown
- **Security Architecture** - Authentication, authorization, encryption
- **Data Flow** - Task execution and message flows
- **Integrations** - MCP servers, webhooks, external APIs
- **Monitoring & Observability** - Logging, metrics, tracing

---

## Quick Reference

### System Layers

```
Client Layer (Next.js, CLI)
        ↓
API Gateway (Auth, Rate Limiting)
        ↓
Application Layer (FastAPI)
        ↓
Orchestration Layer (Inngest)
        ↓
Agent Layer (AI Agents + A2A Protocol)
        ↓
Intelligence Layer (LLM, RAG, Learning)
        ↓
Data Layer (PostgreSQL, Redis, Pinecone)
        ↓
Integration Layer (MCP, Stripe, Webhooks)
```

See [Architecture Overview](./docs/architecture/overview.md) for detailed diagrams.

### Tech Stack

**Backend**: Python + FastAPI + Prisma + PostgreSQL
**Frontend**: Next.js 14+ + TypeScript + Tailwind CSS
**Orchestration**: Inngest
**AI**: OpenAI (default), agno-agi/agnoframework
**Infrastructure**: Docker + Kubernetes + AWS

See [Architecture Overview](./docs/architecture/overview.md) for complete stack.

### Design Philosophy

1. **Modular Monolith First** - Start simple, extract to microservices only when needed
2. **SOLID Principles** - Maintainable, testable, flexible code
3. **Clean Architecture** - Business logic independent of frameworks
4. **Event-Driven** - Async workflows, loose coupling
5. **Scalable by Design** - Stateless, cacheable, horizontally scalable

See [Design Principles](./docs/architecture/design-principles.md) for details.

### Key Patterns

- **Factory Pattern** - Agent creation
- **Repository Pattern** - Data access abstraction
- **Strategy Pattern** - Algorithm selection (task assignment, etc.)
- **Observer Pattern** - Event-driven reactions
- **Saga Pattern** - Long-running distributed transactions

See [Design Patterns](./docs/architecture/design-patterns.md) for all patterns with examples.

---

## Navigation

**Planning a feature?** → [Design Patterns](./docs/architecture/design-patterns.md)
**Performance issue?** → [Performance Optimization](./docs/architecture/performance.md)
**Scaling concerns?** → [Scalability](./docs/architecture/scalability.md)
**Understanding the system?** → [Architecture Overview](./docs/architecture/overview.md)

For complete documentation index, see [`docs/README.md`](./docs/README.md).

---

## Related Documentation

- [Implementation Roadmap](./IMPLEMENTATION_ROADMAP.md) - Step-by-step development guide
- [Agent System Prompts](./roles/) - Default prompts for all squad member roles
- [Project README](./README.md) - Project overview and features
