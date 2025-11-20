# Scaling to 1 Million Users - Complete Architecture Plan

**Current Capacity:** 5,000-10,000 users
**Target Capacity:** 1,000,000 users
**Scale Factor:** 100-200x increase
**Estimated Timeline:** 12-18 months
**Estimated Cost:** $50,000-150,000/month at full scale

---

## 🎯 Executive Summary

**The Brutal Truth:**
Scaling to 1 million users is NOT just "add more servers". It requires fundamental architectural changes across every layer of the system.

**Key Challenges:**
1. **LLM API Rate Limits** - Hard bottleneck at ~3 workflows/sec per API key
2. **Database Scalability** - Single PostgreSQL won't handle 1M users
3. **Global Latency** - Users worldwide need <100ms responses
4. **Cost Optimization** - At scale, every penny matters
5. **Reliability** - 99.99% uptime required (4.38 minutes downtime/month)

**This Document Provides:**
- Realistic capacity calculations
- Required infrastructure changes (10 phases)
- Cost estimates at scale
- Timeline and milestones
- Team requirements

---

## 📊 Understanding 1 Million Users

### Usage Pattern Analysis

**Realistic Assumptions:**
```
Total users: 1,000,000
Daily active users (DAU): 20% = 200,000 users/day
Peak concurrent users: 5% = 50,000 users
Workflows per user per day: 2

Daily workflows: 200,000 × 2 = 400,000 workflows/day
Workflows per second (average): 400,000 / 86,400 = 4.6 workflows/sec
Workflows per second (peak, 3x): 4.6 × 3 = 13.8 workflows/sec
```

**The Problem:**
```
Required capacity: 13.8 workflows/sec (peak)
Current LLM limit: 2.8 workflows/sec (single OpenAI key)

Gap: 13.8 ÷ 2.8 = 5x more capacity needed JUST for LLM
```

**This is BEFORE considering:**
- Database load
- Memory usage
- Network bandwidth
- Storage requirements
- Global latency

---

## 🚨 Critical Bottlenecks at 1M Scale

### 1. LLM API Rate Limits (HARDEST PROBLEM)

**OpenAI Limits (GPT-4):**
```
Tier 1 (default): 500 req/min = 2.8 workflows/sec
Tier 5 (max):     10,000 req/min = 55 workflows/sec

To reach Tier 5: Spend $1,000/month for 6+ months
```

**Required at 1M Users:**
```
Peak: 13.8 workflows/sec

Options:
1. Single provider (Tier 5):     55 workflows/sec ✅ (enough)
2. Multiple OpenAI accounts:     5 × 2.8 = 14 workflows/sec ✅
3. Multi-provider strategy:      OpenAI + Anthropic + others = 20+ workflows/sec ✅
```

**Recommended: Multi-Provider Strategy**

### 2. Database (PostgreSQL Won't Scale)

**Problem:**
```
1M users × 3 agents = 3M agent configurations
200K DAU × 2 workflows = 400K executions/day
400K executions × 100 queries = 40M queries/day
= 463 queries/second average
= 1,389 queries/second peak (3x)

Single PostgreSQL: ~1,000 queries/sec max
```

**Solution Required:**
- Database sharding (horizontal partitioning)
- Read replicas (5-10 replicas)
- Connection pooling (PgBouncer)
- Query optimization
- Aggressive caching (Redis cluster)

### 3. Memory & CPU

**Current (Phase 1):**
```
Workers: 5
Agents per worker: 100
Total memory: 75 GB
```

**At 1M Users:**
```
Unique squad configs: ~10,000 (most users use templates)
Workers needed: 10,000 / 100 = 100 workers
Memory needed: 100 × 15 GB = 1.5 TB
CPU needed: 100 × 2 cores = 200 cores
```

### 4. Network Bandwidth

**Estimate:**
```
API requests: 50,000 concurrent users × 10 requests/min = 8,333 req/sec
Average response: 50 KB
Bandwidth: 8,333 × 50 KB = 416 MB/sec = 3.3 Gbps

Add:
- SSE streaming: +1 Gbps
- Static assets: +500 Mbps
- Database replication: +500 Mbps

Total: ~6 Gbps required
```

### 5. Storage

**Database Storage:**
```
Users: 1M × 5 KB = 5 GB
Squads: 1M × 10 KB = 10 GB
Executions (1 year): 400K/day × 365 × 100 KB = 14.6 TB
Messages (1 year): 400K × 3 agents × 10 messages × 5 KB = 60 TB
Agent data (Agno): 1M users × 50 KB = 50 GB

Total: ~75 TB (with compression)
```

**Vector Storage (Pinecone):**
```
Code embeddings: 100M vectors × 1.5 KB = 150 GB
Cost: ~$500-1,000/month
```

---

## 🏗️ Required Architecture Changes

### Phase 1: Inngest Integration ✅ COMPLETE
**Status:** Done
**Capacity:** 5K-10K users

### Phase 2: Agent Pool ⏳ NEXT
**Timeline:** 1 week
**Capacity:** 10K-25K users
**Changes:**
- Agent instance pooling
- 60% faster agent creation
- 70% less memory

### Phase 3: Redis Caching ⏳ PENDING
**Timeline:** 2 weeks
**Capacity:** 25K-50K users
**Changes:**
- Redis cluster (3 nodes)
- 70-90% fewer DB queries
- Cache invalidation

### Phase 4: Database Optimization ⏳ PENDING
**Timeline:** 1 week
**Capacity:** 50K-100K users
**Changes:**
- PgBouncer connection pooling
- Database indexes
- Query optimization
- Vacuum tuning

### Phase 5: Read Replicas 🔴 NEW
**Timeline:** 2 weeks
**Capacity:** 100K-200K users
**Changes:**
- 5-10 PostgreSQL read replicas
- Read/write splitting
- Replication lag monitoring
- Automatic failover

**Architecture:**
```
┌──────────────┐
│ Primary DB   │ ← Writes only
│ (PostgreSQL) │
└──────┬───────┘
       │ Replicate
       ├──────────────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Replica1 │   │ Replica2 │   │ Replica3 │...│ Replica10│
│ (Read)   │   │ (Read)   │   │ (Read)   │   │ (Read)   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
```

**Cost:** $500-1,000/month (10 replicas)

### Phase 6: Database Sharding 🔴 NEW
**Timeline:** 4-6 weeks
**Capacity:** 200K-500K users
**Changes:**
- Horizontal partitioning by user_id
- Shard coordinator
- Cross-shard queries
- Shard rebalancing

**Sharding Strategy:**
```
Shard Key: user_id % 10

Shard 0: user_id ending in 0 (100K users)
Shard 1: user_id ending in 1 (100K users)
...
Shard 9: user_id ending in 9 (100K users)

Each shard: 100K users, ~7.5 TB data
```

**Cost:** $5,000-10,000/month (10 shards with replicas)

### Phase 7: Multi-LLM Provider Strategy 🔴 NEW
**Timeline:** 2-3 weeks
**Capacity:** Unlimited workflows (rate limit perspective)
**Changes:**
- Support multiple LLM providers simultaneously
- Intelligent provider selection
- Fallback chains
- Cost optimization

**Providers:**
```
1. OpenAI (GPT-4, GPT-4-turbo)
   - Tier 5: 10,000 req/min
   - Cost: $0.03/1K tokens (input), $0.06/1K tokens (output)
   - Use for: Premium users, complex tasks

2. Anthropic (Claude 3.5 Sonnet)
   - 4,000 req/min
   - Cost: $0.003/1K tokens (input), $0.015/1K tokens (output)
   - Use for: High quality, longer context

3. Google (Gemini Pro)
   - 60 req/min (free tier), 1,000 req/min (paid)
   - Cost: $0.00025/1K tokens (input), $0.0005/1K tokens (output)
   - Use for: Cost optimization, high volume

4. Groq (Llama 3, Mixtral)
   - 30 req/sec (free tier), 100+ req/sec (paid)
   - Cost: $0.0001/1K tokens
   - Use for: Fast, cheap workloads

5. Azure OpenAI
   - Dedicated capacity (no rate limits)
   - Cost: $0.03/1K tokens + commitment ($1,000-10,000/month)
   - Use for: Guaranteed capacity

6. AWS Bedrock (Claude, Llama)
   - On-demand or provisioned throughput
   - Cost: Variable
   - Use for: Enterprise customers
```

**Load Balancing Strategy:**
```python
class LLMRouter:
    def select_provider(self, user, task):
        if user.is_premium:
            return "openai"  # Best quality

        if task.requires_long_context:
            return "anthropic"  # Claude has 200K context

        if task.is_simple:
            return "groq"  # Fastest, cheapest

        # Load balance across providers based on current load
        return self.least_loaded_provider()
```

**Total Capacity:**
```
OpenAI (Tier 5):     55 workflows/sec
Anthropic:           22 workflows/sec
Google Gemini:       5 workflows/sec
Groq:                30 workflows/sec
Azure OpenAI:        Unlimited (provisioned)

Combined: 100+ workflows/sec ✅
```

**Cost Optimization:**
```
Cheap tasks (70%): Groq ($0.0001/1K tokens)
Standard tasks (25%): Google Gemini ($0.0005/1K tokens)
Complex tasks (5%): OpenAI/Anthropic ($0.03/1K tokens)

Average cost per workflow: ~$0.02 (vs $0.15 with OpenAI only)
Savings: 86% on LLM costs
```

### Phase 8: Multi-Region Deployment 🔴 NEW
**Timeline:** 6-8 weeks
**Capacity:** Global users with <100ms latency
**Changes:**
- Deploy in 3-5 regions worldwide
- Geographic load balancing
- Data replication
- Region-specific databases

**Regions:**
```
1. US-East (Virginia)      - Americas
2. EU-West (Ireland)       - Europe, Africa
3. AP-Southeast (Singapore) - Asia Pacific
4. US-West (Oregon)        - West Coast US
5. SA-East (São Paulo)     - South America (optional)
```

**Architecture:**
```
                    ┌──────────────────┐
                    │  Global CDN      │
                    │  (Cloudflare)    │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ US-East  │   │ EU-West  │   │ AP-SE    │
        │          │   │          │   │          │
        │ API Pods │   │ API Pods │   │ API Pods │
        │ Workers  │   │ Workers  │   │ Workers  │
        │ DB (RW)  │   │ DB (RO)  │   │ DB (RO)  │
        └──────────┘   └──────────┘   └──────────┘
             │              │              │
             └──────────────┴──────────────┘
                      │ Cross-region
                      │ Replication
```

**Database Strategy:**
```
- Primary (RW): US-East
- Replicas (RO): EU-West, AP-SE
- Cross-region replication: <1 second lag
- Eventual consistency (acceptable for this use case)
```

**Cost:** $15,000-30,000/month (3 regions)

### Phase 9: Advanced Observability 🔴 NEW
**Timeline:** 3-4 weeks
**Capacity:** Monitor 1M+ users reliably
**Changes:**
- Distributed tracing (Jaeger/Tempo)
- Metrics aggregation (Prometheus cluster)
- Log aggregation (ELK/Loki)
- APM (DataDog/New Relic)
- Real-time alerting

**Monitoring Stack:**
```
1. Metrics: Prometheus + Thanos (long-term storage)
   - Request rates
   - Error rates
   - Latency percentiles (p50, p95, p99)
   - Resource usage
   - LLM API usage

2. Logs: Loki + Grafana
   - Centralized logging
   - Log search and analysis
   - Error tracking

3. Traces: Tempo
   - Distributed request tracing
   - Identify bottlenecks
   - Dependency mapping

4. APM: DataDog (recommended for scale)
   - Application performance monitoring
   - Real-user monitoring (RUM)
   - Database query analysis
   - Cost: $5,000-15,000/month
```

**Alerting:**
```
- PagerDuty for on-call rotation
- Slack integration
- Escalation policies
- SLA monitoring (99.99% uptime)
```

**Cost:** $5,000-20,000/month

### Phase 10: Cost Optimization & Efficiency 🔴 NEW
**Timeline:** Ongoing
**Capacity:** Same capacity at 30-50% lower cost
**Changes:**
- Spot instances for workers (70% savings)
- Reserved instances for databases (40% savings)
- LLM provider arbitrage
- Aggressive caching
- Compression
- Data archival

**Optimization Strategies:**

**1. Compute (Workers):**
```
Current: On-demand instances
Cost: 100 workers × $0.10/hour = $10/hour = $7,200/month

Optimized: 80% spot instances + 20% on-demand
Cost:
  - 80 spot workers × $0.03/hour = $2.40/hour
  - 20 on-demand × $0.10/hour = $2.00/hour
  - Total: $4.40/hour = $3,168/month

Savings: 56% ($4,032/month)
```

**2. Database:**
```
Current: On-demand RDS
Cost: 10 shards × $500/month = $5,000/month

Optimized: Reserved instances (1-year)
Cost: 10 shards × $300/month = $3,000/month

Savings: 40% ($2,000/month)
```

**3. LLM Costs:**
```
Current: 100% OpenAI
Cost: 400K workflows/day × $0.15 = $60K/day = $1.8M/month

Optimized: Multi-provider with cost routing
Cost:
  - 70% Groq: 280K × $0.005 = $1,400/day
  - 25% Google: 100K × $0.02 = $2,000/day
  - 5% OpenAI: 20K × $0.15 = $3,000/day
  - Total: $6,400/day = $192K/month

Savings: 89% ($1.6M/month) 🤯
```

**4. Storage:**
```
Tiered storage strategy:
- Hot data (last 30 days): SSD ($0.10/GB/month)
- Warm data (30-90 days): HDD ($0.04/GB/month)
- Cold data (90+ days): Glacier ($0.004/GB/month)

75 TB →
  - 5 TB hot: 5,000 × $0.10 = $500/month
  - 20 TB warm: 20,000 × $0.04 = $800/month
  - 50 TB cold: 50,000 × $0.004 = $200/month
  - Total: $1,500/month (vs $7,500/month for all SSD)

Savings: 80% ($6,000/month)
```

---

## 💰 Cost Analysis at 1M Users

### Infrastructure Costs (Monthly)

| Component | Configuration | Cost |
|-----------|--------------|------|
| **Compute** | | |
| API Pods | 50 pods × $100 | $5,000 |
| Background Workers | 100 workers × $32 (spot) | $3,168 |
| | | |
| **Database** | | |
| Primary Database | 1 × large instance | $1,000 |
| Database Shards | 10 shards × $300 (reserved) | $3,000 |
| Read Replicas | 10 replicas × $200 | $2,000 |
| PgBouncer | 5 instances × $50 | $250 |
| | | |
| **Caching** | | |
| Redis Cluster | 3 nodes × $500 | $1,500 |
| | | |
| **Message Bus** | | |
| NATS Cluster | 3 nodes × $300 | $900 |
| | | |
| **Workflow Engine** | | |
| Inngest Pro | 400K workflows/day | $500 |
| | | |
| **LLM Providers** | | |
| OpenAI (5% of workflows) | 20K workflows/day × $0.15 | $3,000 |
| Anthropic (10%) | 40K workflows/day × $0.10 | $4,000 |
| Google Gemini (20%) | 80K workflows/day × $0.02 | $1,600 |
| Groq (65%) | 260K workflows/day × $0.005 | $1,300 |
| | | |
| **Vector DB** | | |
| Pinecone | 100M vectors | $1,000 |
| | | |
| **CDN & Networking** | | |
| Cloudflare Enterprise | Global CDN | $2,000 |
| Bandwidth | 6 Gbps × $0.02/GB | $3,000 |
| | | |
| **Monitoring & Observability** | | |
| DataDog | 100 hosts + APM | $10,000 |
| PagerDuty | On-call management | $500 |
| | | |
| **Storage** | | |
| Object Storage (S3) | 75 TB tiered | $1,500 |
| Database Backups | 100 TB compressed | $1,000 |
| | | |
| **Load Balancers** | | |
| Application LB | 3 regions × $200 | $600 |
| | | |
| **Total Infrastructure** | | **$46,818/month** |

### Additional Costs

| Category | Cost/Month |
|----------|------------|
| DevOps Team | $40,000 (2 engineers) |
| On-call Support | $10,000 |
| Security & Compliance | $5,000 |
| **Total Operational** | **$55,000/month** |

### Grand Total

```
Infrastructure: $46,818/month
Operational:    $55,000/month
─────────────────────────────────
Total:         $101,818/month

At 1M users: ~$0.10 per user per month
```

**Revenue Needed:**
```
Break-even: $101,818/month ÷ 1M users = $0.10/user/month
With 40% margin: $0.17/user/month
With profit: $5-20/user/month (typical SaaS)
```

### Cost Breakdown by Category

```
LLM Costs:         $9,900  (9.7%)   ← Optimized from $1.8M!
Compute:           $8,168  (8.0%)
Database:          $7,250  (7.1%)
Monitoring:        $10,500 (10.3%)
Team/Ops:          $55,000 (54.0%)
Other:             $10,000 (9.8%)
```

---

## 🏢 Required Team at Scale

### Engineering Team

| Role | Count | Salary/Year | Responsibilities |
|------|-------|-------------|------------------|
| **Platform Engineers** | 3 | $150K | Infrastructure, scaling |
| **Backend Engineers** | 5 | $140K | Features, optimization |
| **DevOps/SRE** | 3 | $160K | Reliability, deployment |
| **Database Engineers** | 2 | $160K | Sharding, optimization |
| **Frontend Engineers** | 3 | $130K | UI/UX, performance |
| **ML Engineers** | 2 | $150K | Agent optimization, ML |
| **QA Engineers** | 2 | $110K | Testing, automation |
| **Security Engineer** | 1 | $170K | Security, compliance |
| **Engineering Manager** | 1 | $180K | Team management |
| **Total** | **22** | **$3.2M/year** | |

### Operations Team

| Role | Count | Salary/Year |
|------|-------|-------------|
| On-call Support | 4 | $80K |
| Customer Success | 10 | $70K |
| **Total** | **14** | **$1.02M/year** |

### Grand Total Team Cost

```
Engineering: $3.2M/year = $267K/month
Operations:  $1.02M/year = $85K/month
────────────────────────────────────────
Total:      $4.22M/year = $352K/month
```

---

## 📅 Implementation Timeline

### Months 1-2: Foundation (Phase 2-4)
- ✅ Agent Pool
- ✅ Redis Caching
- ✅ Database Optimization
- **Capacity:** 25K-100K users

### Months 3-4: Database Scaling (Phase 5-6)
- ✅ Read Replicas
- ✅ Database Sharding (start)
- **Capacity:** 100K-200K users

### Months 5-7: LLM & Reliability (Phase 6-7)
- ✅ Database Sharding (complete)
- ✅ Multi-LLM Provider Strategy
- **Capacity:** 200K-500K users

### Months 8-10: Global Scale (Phase 8-9)
- ✅ Multi-Region Deployment
- ✅ Advanced Observability
- **Capacity:** 500K-800K users

### Months 11-12: Optimization (Phase 10)
- ✅ Cost Optimization
- ✅ Performance Tuning
- **Capacity:** 800K-1M users

### Months 13-18: Scale & Stabilize
- ✅ Handle growth to 1M users
- ✅ Continuous optimization
- ✅ Team scaling
- **Capacity:** 1M+ users ✅

---

## 🎯 Critical Success Factors

### 1. Multi-LLM Provider Strategy (HIGHEST PRIORITY)

**Why:**
- LLM rate limits are THE bottleneck
- Single provider = single point of failure
- Cost savings: 89% ($1.6M/month)

**Implementation:**
```python
# Priority order for implementation
1. Add Groq (1 week) - Immediate 30x capacity increase
2. Add Google Gemini (1 week) - Cost savings
3. Add Anthropic (1 week) - Quality option
4. Add Azure OpenAI (2 weeks) - Enterprise reliability
5. Intelligent routing (2 weeks) - Cost optimization
```

### 2. Database Sharding

**Why:**
- Single DB = 1,000 queries/sec max
- 1M users = 1,389 queries/sec peak
- MUST shard to scale

**Risk:**
- Most complex change
- Requires data migration
- Can't easily undo

### 3. Team Growth

**Why:**
- Current team: 1-2 people?
- Need: 22+ engineers
- Can't scale system without team

**Hiring Plan:**
```
Month 1-3:   Hire 2 platform engineers
Month 4-6:   Hire 2 backend + 1 DevOps
Month 7-9:   Hire 2 DB engineers + 1 DevOps
Month 10-12: Hire remaining team
```

### 4. Funding

**Why:**
- Infrastructure: $100K/month
- Team: $350K/month
- Total: $450K/month burn rate
- Need: $8M+ Series A minimum

---

## 🚨 Risks & Mitigation

### Risk 1: LLM Provider Changes

**Risk:** Provider changes rates, limits, or terms
**Impact:** CRITICAL
**Probability:** MEDIUM
**Mitigation:**
- Multi-provider from day 1
- Contract negotiations
- Self-hosted LLM backup (Ollama cluster)

### Risk 2: Database Migration Failure

**Risk:** Sharding migration loses data
**Impact:** CATASTROPHIC
**Probability:** LOW
**Mitigation:**
- Extensive testing
- Blue-green migration
- Rollback plan
- Zero-downtime migration

### Risk 3: Runaway Costs

**Risk:** Costs spiral out of control
**Impact:** HIGH
**Probability:** HIGH
**Mitigation:**
- Cost monitoring and alerts
- Per-user cost caps
- Aggressive optimization
- Spot instances

### Risk 4: Team Scaling

**Risk:** Can't hire fast enough
**Impact:** HIGH
**Probability:** MEDIUM
**Mitigation:**
- Start hiring early
- Competitive compensation
- Remote-first (global talent)
- Offshore team augmentation

---

## 📈 Phased Rollout Strategy

### Phase A: 0-100K Users (Months 1-4)
**Focus:** Foundation
**Investment:** $200K
**Monthly Cost:** $20K
**Revenue Required:** $2K/month (break-even at $0.20/user)

### Phase B: 100K-500K Users (Months 5-9)
**Focus:** Scaling
**Investment:** $1M
**Monthly Cost:** $60K
**Revenue Required:** $12K/month (break-even at $0.12/user)

### Phase C: 500K-1M Users (Months 10-18)
**Focus:** Optimization
**Investment:** $3M
**Monthly Cost:** $100K
**Revenue Required:** $100K/month (break-even at $0.10/user)

---

## ✅ Checklist for 1M Users

### Technical
- [ ] Multi-LLM provider (OpenAI + Anthropic + Google + Groq)
- [ ] Database sharding (10 shards minimum)
- [ ] Read replicas (10+ replicas)
- [ ] Redis cluster (3+ nodes)
- [ ] Multi-region deployment (3+ regions)
- [ ] Agent pool optimization
- [ ] Aggressive caching (90%+ cache hit rate)
- [ ] CDN for static assets
- [ ] Spot instances for workers
- [ ] Advanced monitoring (DataDog/New Relic)

### Operations
- [ ] 99.99% uptime SLA
- [ ] 24/7 on-call rotation
- [ ] Incident response procedures
- [ ] Disaster recovery plan
- [ ] Security audits (annual)
- [ ] Compliance (SOC 2, GDPR)

### Team
- [ ] 22+ engineers
- [ ] DevOps/SRE team (3+)
- [ ] Database specialists (2+)
- [ ] On-call support (4+)
- [ ] Customer success (10+)

### Business
- [ ] $8M+ funding secured
- [ ] $5-20/user/month pricing
- [ ] Customer acquisition strategy
- [ ] Churn < 5%/month

---

## 🎯 Bottom Line

### Can We Scale to 1M Users?

**YES, but:**

1. **Required Investment:** $4-8M over 18 months
2. **Required Team:** 22+ engineers (currently 1-2?)
3. **Required Time:** 12-18 months minimum
4. **Required Changes:** 10 major architectural phases
5. **Monthly Cost at Scale:** ~$100K infrastructure + $350K team = $450K/month

### Realistic Path

**Current → 100K users:**
- Timeline: 6 months
- Cost: $500K
- Team: 5-8 engineers
- **ACHIEVABLE**

**100K → 500K users:**
- Timeline: 12 months
- Cost: $2M
- Team: 15-20 engineers
- **CHALLENGING but DOABLE**

**500K → 1M users:**
- Timeline: 18 months
- Cost: $5M
- Team: 25-30 engineers
- **REQUIRES SERIES A+**

### The Real Question

**Do you have:**
- $5-8M in funding? (or revenue to support it)
- 12-18 month runway?
- Ability to hire 20+ engineers?
- Product-market fit proven at 10K-100K users?

**If NO to any:** Focus on getting to 100K users first, prove PMF, then raise Series A for 1M scale.

**If YES to all:** Follow this plan, it's achievable!

---

**Version:** 1.0
**Last Updated:** 2025-11-03
**Author:** Agent-Squad Team
