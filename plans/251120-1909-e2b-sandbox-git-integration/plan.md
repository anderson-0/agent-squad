# E2B Sandbox Git Integration - Implementation Plans

## Executive Summary

Two distinct approaches for integrating git operations (clone, pull, push) into E2B sandbox environments for agent-squad project.

## Context

**Current State:**
- E2B integration EXISTS for Python execution (`backend/integrations/mcp/servers/python_executor_server.py`)
- Agents use MCP servers for tool access
- Architecture supports async operations via Celery/NATS
- Multiple agents work in parallel on same repository

**Requirements:**
- Isolated sandbox environments per agent
- Git operations: clone, pull, push
- Parallel multi-agent coordination
- Conflict handling and branch management
- Secure credential management

## Approach Comparison

| Aspect | Approach 1: Quick Win | Approach 2: Enterprise Grade |
|--------|----------------------|----------------------------|
| **Implementation Time** | Claude: 30-45 min<br>Senior: 4-6 hrs<br>Junior: 8-12 hrs | Claude: 90-120 min<br>Senior: 2-3 days<br>Junior: 4-6 days |
| **Complexity** | Simple - extend existing MCP server | Complex - new service layer + infrastructure |
| **Files Changed** | 3 core files | 10+ files across services/models/API |
| **Conflict Handling** | Basic retry with rebase | Advanced - distributed locking + conflict resolution engine |
| **Sandbox Lifecycle** | Per-operation (create/destroy) | Pooled with reuse + long-lived sessions |
| **Monitoring** | Basic logging | Comprehensive metrics + dashboards |
| **Risk Level** | Low - minimal surface area | Medium - more moving parts |
| **Scalability** | Good (< 10 concurrent agents) | Excellent (100+ concurrent agents) |
| **Maintenance** | Low effort | Higher effort but better tooling |

## Key Trade-offs

### Approach 1: Quick Win
**Pros:**
- Minimal code changes
- Leverages existing E2B integration
- Fast to implement and test
- Low maintenance overhead
- Simple debugging

**Cons:**
- Creates new sandbox per git operation (cost)
- Basic conflict handling
- No sandbox reuse
- Limited monitoring
- Manual coordination between agents

### Approach 2: Enterprise Grade
**Pros:**
- Sandbox pooling (cost optimization)
- Advanced conflict resolution
- Distributed locking (Redis)
- Comprehensive monitoring
- Battle-tested for scale
- Auto-retry with exponential backoff

**Cons:**
- Longer implementation time
- More infrastructure dependencies (Redis locks)
- Higher complexity
- More code to maintain
- Steeper learning curve

## Recommendation

**For MVP/Prototype:** Use **Approach 1**
- Ship fast, validate concept
- Upgrade to Approach 2 when scaling

**For Production (Day 1):** Use **Approach 2**
- Better architecture foundation
- Avoid technical debt
- Handles edge cases properly

**Hybrid Strategy:**
1. Implement Approach 1 first (validate use case)
2. Run for 2-4 weeks, collect metrics
3. Migrate to Approach 2 based on data

## Implementation Files

### Approach 1 Files
```
backend/integrations/mcp/servers/git_operations_server.py  [NEW]
backend/agents/configuration/mcp_tool_mapping.yaml         [MODIFY]
backend/core/config.py                                      [MODIFY]
```

### Approach 2 Files
```
backend/services/git_sandbox_service.py                    [NEW]
backend/services/sandbox_pool_manager.py                   [NEW]
backend/models/git_sandbox.py                              [NEW]
backend/schemas/git_sandbox.py                             [NEW]
backend/api/v1/endpoints/git_sandbox.py                    [NEW]
backend/agents/configuration/mcp_tool_mapping.yaml         [MODIFY]
backend/core/config.py                                      [MODIFY]
backend/workers/sandbox_cleanup.py                         [NEW]
alembic/versions/009_add_git_sandbox_tables.py            [NEW]
tests/test_git_sandbox_integration.py                      [NEW]
```

## Next Steps

1. Review both detailed approach plans:
   - `approach-01-quick-win.md`
   - `approach-02-enterprise-grade.md`

2. Choose approach based on:
   - Timeline constraints
   - Team resources
   - Scale requirements
   - Production readiness needs

3. Proceed with implementation using selected approach

## Unresolved Questions

1. **Credentials:** Store git tokens in database per-project or environment-wide?
2. **E2B Limits:** Confirm E2B allows outbound SSH/HTTPS connections (likely yes)
3. **Cost Model:** E2B pricing for long-lived vs ephemeral sandboxes?
4. **Git Strategy:** Branch-per-agent or shared-branch-with-locks?
5. **Conflict Threshold:** How many auto-retry attempts before escalating to PM agent?
6. **Cleanup:** Delete agent branches after merge or keep for audit trail?

## Time Investment Summary

| Approach | Claude | Senior Dev | Junior Dev | Complexity |
|----------|--------|-----------|------------|------------|
| Approach 1 | 30-45 min | 4-6 hrs | 8-12 hrs | Simple |
| Approach 2 | 90-120 min | 2-3 days | 4-6 days | Complex |

**Note:** Time estimates include implementation + testing + documentation.
