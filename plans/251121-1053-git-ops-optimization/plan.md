# Git Operations MCP Server Optimization Plan

**Plan ID:** 251121-1053-git-ops-optimization
**Created:** 2025-11-21 10:57
**Status:** Planning Complete
**Complexity:** High

---

## Executive Summary

Comprehensive optimization plan reducing token usage by 90% (6,000→600 tokens), P95 latency by 75-94% (8s→0.5-2s), and metrics overhead by 90% (5-10ms→<1ms) while maintaining all functionality and security.

**Current Baseline:**
- 1,006-line monolithic server with 5 separate MCP tools
- Full git clones for all operations (~60s medium repos)
- 11 Prometheus metrics generating 10,000+ time series
- E2B sandboxes: cold start (1-3s), 1-hour cache TTL
- Metrics overhead: 5-10ms per operation

**Optimization Targets:**
- **Token Usage:** 6,000 → 600 tokens (90% reduction)
- **P95 Latency:** 8s → 0.5-2s (75-94% reduction)
- **Metrics Overhead:** 5-10ms → <1ms (90% reduction)
- **Cache Hit Rate:** 50% → 85% (70% improvement)
- **Time Series:** 10,000+ → 18 (99.8% reduction)

---

## Strategic Approach

Three-phase implementation prioritizing:
1. **Quick Wins** - Immediate high-impact optimizations (1-2 days)
2. **Architecture Refactor** - Long-term maintainability (2-3 days)
3. **Advanced Optimizations** - Performance ceiling (2-3 days)

---

## Phase Status

| Phase | Description | Status | Priority | Duration |
|-------|-------------|--------|----------|----------|
| [Phase 1](./phase-01-quick-wins.md) | Quick Wins: Shallow clones + metrics | Not Started | P0 | 1-2 days |
| [Phase 2](./phase-02-architecture-refactor.md) | Modular architecture + code execution | Not Started | P1 | 2-3 days |
| [Phase 3](./phase-03-advanced-optimizations.md) | E2B templates + dynamic cache | Not Started | P2 | 2-3 days |

---

## Key Insights from Research

### Token Optimization (90% reduction possible)
1. **MCP Code Execution Pattern** (-4,500 tokens)
   - Single `execute_code` tool vs 5 tool schemas
   - 98.7% context reduction per Anthropic Engineering Blog 2025

2. **Modular Architecture** (-800 tokens)
   - 50-line facade + modules vs 900-line monolith
   - Load 50 lines instead of 1,006 (95% reduction)

3. **Label Optimization** (18 vs 10,000+ time series)
   - 3 strategic labels: operation, status, error_type
   - Drop unbounded: repo_url, branch_name, user_id, commit_hash

4. **Minimal Documentation** (-200 tokens)
   - Concise docstrings + type hints
   - 85% reduction in prose

### Performance Optimization (85-95% latency reduction)
1. **Shallow Git Clones** (70-90% faster)
   - Chromium: 95m → 6m (93% reduction)
   - GitLab: 6m → 6.5s (98.3% reduction)

2. **E2B Sandbox Templates** (96-99% faster init)
   - Cold start: 1-3s → 200ms (template-based)
   - Firecracker microVM boot: <125ms

3. **Metrics Batching** (66-83% overhead reduction)
   - Scrape interval: 15s → 60s (75% data reduction)
   - Fire-and-forget async recording

4. **Dynamic Cache TTL** (50% → 85% hit rate)
   - Active repos: 2-hour TTL
   - Idle repos: 30-min TTL
   - Top 10 repos: indefinite

---

## Success Criteria

### Phase 1: Quick Wins
- ✅ Shallow clones reduce clone time by 70-90%
- ✅ Metrics overhead <1ms (from 5-10ms)
- ✅ Time series reduced to 18 (from 10,000+)
- ✅ All tests pass, no regressions

### Phase 2: Architecture Refactor
- ✅ Token usage <1,000 (from 6,000)
- ✅ Modular structure: facade + 6 modules
- ✅ Code execution pattern implemented
- ✅ All 5 git operations functional

### Phase 3: Advanced Optimizations
- ✅ E2B sandbox init <200ms (from 1-3s)
- ✅ Cache hit rate >80% (from 50%)
- ✅ P95 latency <2s (from 8s)
- ✅ Token usage ~600 (target)

---

## Risk Assessment

### High Risk Items
1. **Shallow Clone Compatibility** (Phase 1, P0)
   - Risk: Push operations fail without full history
   - Mitigation: Use full clones for push, shallow for status/diff
   - Fallback: Toggle via config flag

2. **Code Execution Pattern Adoption** (Phase 2, P1)
   - Risk: MCP clients may not support pattern yet
   - Mitigation: Maintain both tool schemas and code execution
   - Fallback: Gradual migration, feature flag

3. **E2B Template Maintenance** (Phase 3, P2)
   - Risk: Stale packages, security vulnerabilities
   - Mitigation: Automated weekly rebuilds
   - Fallback: Graceful degradation to standard sandboxes

### Medium Risk Items
1. **Metrics cardinality reduction** may reduce debugging granularity
2. **Cache TTL changes** could increase E2B costs temporarily
3. **Module refactoring** requires comprehensive testing

---

## Constraints & Requirements

### Must Maintain
- ✅ All 5 git operations (clone, status, diff, pull, push)
- ✅ MCP protocol interface compatibility
- ✅ E2B sandbox isolation and security
- ✅ Credential management (GitHub tokens)
- ✅ Retry logic for push conflicts
- ✅ Monitoring capabilities (Prometheus)

### Must Not Break
- ✅ Existing MCP clients consuming git operations
- ✅ Agent isolation (branch-per-agent pattern)
- ✅ Sandbox caching mechanism
- ✅ Error handling and reporting

---

## Time Estimates

| Phase | Claude | Senior Dev | Junior Dev |
|-------|--------|------------|------------|
| Phase 1: Quick Wins | 2-3 hours | 1-2 days | 2-3 days |
| Phase 2: Architecture | 4-6 hours | 2-3 days | 4-5 days |
| Phase 3: Advanced | 3-4 hours | 2-3 days | 3-4 days |
| **Total** | **9-13 hours** | **5-8 days** | **9-12 days** |

**Complexity:** High (architectural changes, performance tuning, metrics redesign)

---

## Implementation Order

### Phase 1: Quick Wins (Days 1-2)
1. Implement shallow clone flag
2. Optimize Prometheus labels (18 time series)
3. Implement metrics batching
4. Add fire-and-forget async metrics
5. Update scrape interval to 60s

### Phase 2: Architecture Refactor (Days 3-5)
1. Extract modules (facade, operations, sandbox, metrics, utils)
2. Implement code execution pattern (single tool)
3. Maintain backward compatibility (dual interface)
4. Comprehensive testing
5. Update documentation

### Phase 3: Advanced Optimizations (Days 6-8)
1. Build E2B git-optimized template
2. Implement template-based sandbox creation
3. Add dynamic TTL caching logic
4. Implement connection pooling (2-3 warm sandboxes)
5. Performance validation

---

## Related Files

**Current Implementation:**
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/integrations/mcp/servers/git_operations_server.py` (1,006 lines)
- `/home/anderson/Documents/git/anderson-0/agent-squad/backend/monitoring/prometheus_metrics.py` (190 lines)

**Test Files:**
- `/home/anderson/Documents/git/anderson-0/agent-squad/test_mcp_git_operations.py`
- `/home/anderson/Documents/git/anderson-0/agent-squad/demo_github_mcp_test.py`

**Research Reports:**
- `./research/researcher-01-token-optimization.md`
- `./research/researcher-02-performance-optimization.md`

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1 implementation (quick wins)
3. Validate Phase 1 results before Phase 2
4. Progressive rollout with feature flags
5. Monitor metrics and adjust

---

## Unresolved Questions

1. **E2B Pricing Model:** Does pooling increase costs vs current 1-hour cache?
2. **MCP Client Capabilities:** Which clients support code execution pattern?
3. **Production Traffic Patterns:** Current cache hit rate and operation distribution?
4. **Error Budget:** Acceptable regression threshold during rollout?
5. **Template Security:** Automated CVE scanning for E2B templates?

---

**End of Plan Overview**
