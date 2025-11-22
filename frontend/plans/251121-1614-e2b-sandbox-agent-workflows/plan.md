# E2B Sandbox Integration - Implementation Plan

**Created:** 2025-11-21
**Status:** Planning Complete
**Complexity:** High

## Executive Summary

Integrate E2B cloud sandboxes with agent workflows to enable isolated development environments. Each agent gets dedicated sandbox for cloning repos, creating task branches, committing work, pushing code, and auto-creating PRs.

**Key Technical Decisions:**
- Backend: FastAPI (Python) - E2B SDK native support, async operations
- Git Library: simple-git via Node.js in sandbox (5.9M weekly downloads vs 535K for isomorphic-git)
- GitHub Auth: Fine-grained PATs initially, GitHub Apps for production
- Database: PostgreSQL for sandbox metadata, git context persistence
- Real-time: SSE for status updates, logs streaming

## Implementation Phases

| Phase | Priority | Status | Time (Claude) | Time (Senior) | Time (Junior) |
|-------|----------|--------|---------------|---------------|---------------|
| [01 - Backend Foundation](./phase-01-backend-foundation.md) | P0 | Pending | 30 min | 3-4 hrs | 8-10 hrs |
| [02 - E2B Sandbox Service](./phase-02-e2b-sandbox-service.md) | P0 | Pending | 45 min | 4-6 hrs | 10-12 hrs |
| [03 - Git Operations Service](./phase-03-git-operations-service.md) | P0 | Pending | 40 min | 5-7 hrs | 12-15 hrs |
| [04 - GitHub Integration](./phase-04-github-integration.md) | P0 | Pending | 35 min | 3-4 hrs | 8-10 hrs |
| [05 - SSE Real-Time Updates](./phase-05-sse-realtime-updates.md) | P1 | Pending | 30 min | 4-5 hrs | 10-12 hrs |
| [06 - Frontend Integration](./phase-06-frontend-integration.md) | P0 | Pending | 40 min | 4-5 hrs | 10-12 hrs |
| [07 - UI Enhancements](./phase-07-ui-enhancements.md) | P1 | Pending | 35 min | 3-4 hrs | 8-10 hrs |
| [08 - Testing & Deployment](./phase-08-testing-deployment.md) | P0 | Pending | 60 min | 8-10 hrs | 16-20 hrs |

**Total Estimates:**
- **Claude:** ~4.5 hours (parallel execution possible)
- **Senior Dev:** 34-45 hours (~5-6 days)
- **Junior Dev:** 82-101 hours (~10-13 days)

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Next.js        │  HTTP   │  FastAPI         │  SDK    │  E2B Cloud      │
│  Frontend       │◄───────►│  Backend         │◄───────►│  Sandboxes      │
│                 │         │                  │         │                 │
│  - KanbanBoard  │         │  - Sandbox API   │         │  - Firecracker  │
│  - Agent Work   │         │  - Git Service   │         │    microVMs     │
│  - SSE Client   │         │  - GitHub API    │         │  - Isolated FS  │
└─────────────────┘         │  - SSE Server    │         └─────────────────┘
                            └──────────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  PostgreSQL      │
                            │  - Sandboxes     │
                            │  - Git Context   │
                            │  - Task Metadata │
                            └──────────────────┘
```

## Critical Dependencies

### Phase Dependencies
- Phase 02-04 depend on Phase 01 (backend foundation)
- Phase 05 depends on Phase 02-04 (needs services to emit events)
- Phase 06 depends on Phase 01-05 (API endpoints available)
- Phase 07 depends on Phase 06 (frontend types/stores ready)
- Phase 08 requires all phases complete

### External Dependencies
- E2B API key (free tier available)
- GitHub fine-grained PAT with repo permissions
- PostgreSQL 15+ database
- Node.js 18+ in E2B sandboxes
- Git CLI in E2B sandboxes

## Risk Assessment

**High Risk:**
- E2B sandbox quota limits (unknown concurrent limits)
- GitHub rate limits (5k/hr with PATs)
- Network failures during git operations
- Sandbox crashes with incomplete work

**Medium Risk:**
- Long-running tasks (24hr max session)
- Concurrent agent conflicts on same repo
- Database connection pooling under load

**Mitigation:**
- Implement retry logic with exponential backoff
- Queue system for git operations
- Regular sandbox health checks
- Automatic cleanup on failures
- GitHub Apps for production (15k/hr rate limit)

## Success Criteria

- [ ] Agent can clone repo into sandbox <5 seconds
- [ ] Task branch created automatically (format: `task-{id}`)
- [ ] Conventional commits pushed successfully
- [ ] PR auto-created on GitHub with correct metadata
- [ ] Real-time logs visible in Agent Work page
- [ ] Multiple agents working simultaneously without conflicts
- [ ] Sandbox cleanup on task completion
- [ ] Error recovery handles git failures gracefully

## Next Steps

1. Review all phase files
2. Confirm technical decisions with user
3. Setup backend project structure (Phase 01)
4. Obtain E2B API key and GitHub PAT
5. Begin implementation starting with P0 phases

## Related Documentation

- [Research: E2B Integration](./research/researcher-01-e2b-integration.md)
- [Research: Git & GitHub API](./research/researcher-02-git-github-api.md)
- [Scout: Architecture Analysis](./scout/scout-01-architecture.md)
- [Design Guidelines](../../docs/design-guidelines.md)
