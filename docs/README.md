# Agent Squad Documentation

## 📚 Documentation Index

### Getting Started
- [Main README](../README.md) - Project overview, features, and quick start
- [Implementation Roadmap](../IMPLEMENTATION_ROADMAP.md) - Step-by-step development guide

### Architecture Documentation
- [Architecture Overview](./architecture/overview.md) - High-level system architecture
- [Design Principles](./architecture/design-principles.md) - SOLID, Clean Architecture, DDD
- [Design Patterns](./architecture/design-patterns.md) - Patterns used throughout the system
- [System Components](./architecture/components.md) - Detailed component breakdown
- [Scalability](./architecture/scalability.md) - Horizontal scaling, caching, async processing
- [Performance Optimization](./architecture/performance.md) - Database, API, LLM optimizations
- [Security Architecture](./architecture/security.md) - Auth, encryption, validation
- [Data Flow](./architecture/data-flow.md) - Task execution and message flows
- [Integrations](./architecture/integrations.md) - MCP servers, webhooks, external APIs
- [Monitoring & Observability](./architecture/monitoring.md) - Logging, metrics, tracing

### Guides (Coming Soon)
- API Reference
- Deployment Guide
- Development Setup
- Testing Strategy

### Agent System Prompts
All agent role prompts are in the [`/roles`](../roles) directory:

**Management & Architecture:**
- [Project Manager](../roles/project_manager/default_prompt.md)
- [Tech Lead](../roles/tech_lead/default_prompt.md)
- [Solution Architect](../roles/solution_architect/default_prompt.md)
- [QA Tester](../roles/tester/default_prompt.md)

**Backend Developers:**
- [Node.js + Express](../roles/backend_developer/nodejs_express.md)
- [Node.js + NestJS](../roles/backend_developer/nodejs_nestjs.md)
- [Node.js + Serverless](../roles/backend_developer/nodejs_serverless.md)
- [Python + FastAPI](../roles/backend_developer/python_fastapi.md)
- [Python + Django](../roles/backend_developer/python_django.md)

**Frontend Developers:**
- [React + Next.js](../roles/frontend_developer/react_nextjs.md)

**Specialized Roles:**
- [AI/ML Engineer](../roles/ai_engineer/default_prompt.md)
- [DevOps Engineer](../roles/devops_engineer/default_prompt.md)
- [UI/UX Designer](../roles/designer/default_prompt.md)

---

## 🎯 Quick Navigation

**Planning a feature?** → Check [Design Patterns](./architecture/design-patterns.md)

**Performance issue?** → See [Performance Optimization](./architecture/performance.md)

**Scaling concerns?** → Read [Scalability](./architecture/scalability.md)

**Security review?** → Review [Security Architecture](./architecture/security.md)

**Understanding data flow?** → Study [Data Flow](./architecture/data-flow.md)

**Adding integrations?** → Consult [Integrations](./architecture/integrations.md)

**Setting up monitoring?** → Follow [Monitoring](./architecture/monitoring.md)
