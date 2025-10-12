# Scalability Architecture

## Overview

Agent Squad is designed to scale horizontally from day one, handling growth in users, squads, and task executions without major architectural changes.

## Horizontal Scalability

### Stateless Application Servers

All application servers are stateless, enabling unlimited horizontal scaling.

```yaml
# kubernetes/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 5  # Scale as needed
  template:
    spec:
      containers:
      - name: backend
        image: backend:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: secrets
              key: database-url
```

**Scaling Strategy**:
- CPU-based autoscaling: Target 70% CPU utilization
- Request-based: Scale up at 80% capacity
- Time-based: Pre-scale before expected peak hours

### Load Balancing

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │  (NGINX/ALB)    │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────┐
    │ Backend Pod 1│  │Backend Pod 2│  │Backend Pod3│
    └──────────────┘  └─────────────┘  └────────────┘
```

**Configuration**:
- Round-robin load balancing
- Health checks every 10s
- Automatic pod replacement on failure
- Session affinity: Not required (stateless)

## Database Scaling

### Read/Write Splitting

```
                    ┌─────────────────────┐
                    │  Application Layer  │
                    └──────────┬──────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
          ┌───────▼────────┐       ┌───────▼────────┐
          │  Write          │       │  Read          │
          │  Operations     │       │  Operations    │
          └───────┬────────┘       └───────┬────────┘
                  │                         │
          ┌───────▼────────┐       ┌───────▼────────┐
          │   Primary DB   │──────▶│  Read Replica  │
          │   (Write)      │ Repli-│  (Read Only)   │
          └────────────────┘ cation└────────────────┘
```

**Implementation**:
```python
# Read from replica
async def get_squads(user_id: str):
    async with get_read_db() as db:
        return await db.squad.find_many(where={"userId": user_id})

# Write to primary
async def create_squad(squad_data: dict):
    async with get_write_db() as db:
        return await db.squad.create(data=squad_data)
```

### Connection Pooling

```python
# Configure Prisma connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Connections per instance
    max_overflow=10,     # Additional connections
    pool_timeout=30,     # Wait time for connection
    pool_recycle=3600    # Recycle connections hourly
)
```

**Sizing Guidelines**:
- Start: 20 connections per backend pod
- Monitor: Connection wait time
- Scale: Increase pool size or add replicas

### Database Partitioning (Future)

When database becomes bottleneck:

**Horizontal Partitioning (Sharding)**:
```python
# Shard by user_id
shard_id = hash(user_id) % NUM_SHARDS
db = get_shard_connection(shard_id)
```

**Vertical Partitioning**:
- Move large/cold data to separate tables
- Archive old task executions
- Separate analytics data

## Caching Architecture

### Multi-Layer Cache Strategy

```
Request
   │
   ▼
┌──────────────────────────────────┐
│  L1: In-Memory Cache             │
│  (LRU, 100MB per pod)            │
│  TTL: 60s                        │
└──────────┬───────────────────────┘
           │ Miss
           ▼
┌──────────────────────────────────┐
│  L2: Redis Cache                 │
│  (Distributed, 10GB cluster)     │
│  TTL: 300-3600s                  │
└──────────┬───────────────────────┘
           │ Miss
           ▼
┌──────────────────────────────────┐
│  L3: Database                    │
│  (Source of truth)               │
└──────────────────────────────────┘
```

### Cache Strategy by Data Type

```python
# User data: 5 minutes (frequently accessed)
@cached(ttl=300, layer="redis")
async def get_user(user_id: str) -> User:
    return await user_repository.get_by_id(user_id)

# Squad config: 1 hour (rarely changes)
@cached(ttl=3600, layer="redis")
async def get_squad_config(squad_id: str) -> SquadConfig:
    return await squad_repository.get_config(squad_id)

# Agent prompts: 24 hours in memory (static)
@cached(ttl=86400, layer="memory")
def get_agent_prompt(role: str) -> str:
    return prompt_loader.load(role)

# Task execution: No cache (real-time)
async def get_task_execution(execution_id: str):
    return await task_repository.get_execution(execution_id)
```

### Cache Invalidation

```python
# Invalidate on write
async def update_squad(squad_id: str, updates: dict):
    squad = await squad_repository.update(squad_id, updates)

    # Invalidate caches
    await cache.delete(f"squad:{squad_id}")
    await cache.delete(f"squad_config:{squad_id}")

    return squad

# Event-based invalidation
@event_bus.subscribe("squad.updated")
async def invalidate_squad_cache(event: Dict):
    await cache.delete(f"squad:{event['squad_id']}")
```

## Asynchronous Processing

### Message Queue Architecture

```
┌────────────────┐       ┌────────────────┐       ┌────────────────┐
│   Web Server   │──────▶│  Message Queue │──────▶│    Workers     │
│  (FastAPI)     │ Enq   │  (Inngest/SQS) │ Deq   │  (Async Tasks) │
└────────────────┘       └────────────────┘       └────────────────┘
       │                                                    │
       │                                                    │
       └────────────────── Results ────────────────────────┘
                     (via SSE or webhook)
```

### Task Categories

**1. Long-Running Tasks** (Inngest)
- Task execution (can take hours/days)
- Code generation
- Large code analysis
- RAG document processing

**2. Scheduled Tasks** (Cron)
- Cleanup old executions
- Aggregate metrics
- Backup data
- Health checks

**3. Event-Driven Tasks** (Webhooks)
- Process Jira updates
- Handle Git events
- Payment events
- User notifications

### Worker Scaling

```yaml
# kubernetes/inngest-worker.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inngest-worker
spec:
  replicas: 3  # Scale based on queue depth
  template:
    spec:
      containers:
      - name: worker
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
```

**Auto-scaling Rules**:
- Scale up: Queue depth > 100 messages
- Scale down: Queue depth < 20 messages
- Min replicas: 2
- Max replicas: 20

## CDN & Asset Delivery

### Static Assets

```
User Request
     │
     ▼
┌──────────────────┐
│   CloudFront     │  ← Edge locations worldwide
│   (CDN)          │
└────────┬─────────┘
         │ Miss
         ▼
┌──────────────────┐
│   S3 Bucket      │  ← Origin server
│   (Assets)       │
└──────────────────┘
```

**Cached Assets**:
- JavaScript/CSS bundles
- Images and media
- Agent prompt files
- Static documentation

**Cache Headers**:
```typescript
// Next.js configuration
module.exports = {
  async headers() {
    return [
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      }
    ]
  }
}
```

## Microservices Migration Path

### Phase 1: Modular Monolith (Current)

```
┌─────────────────────────────────┐
│      Single Application         │
├─────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐ │
│  │Users │  │Squads│  │Tasks │ │
│  └──────┘  └──────┘  └──────┘ │
└───────────────┬─────────────────┘
                │
        ┌───────▼────────┐
        │  Single DB     │
        └────────────────┘
```

**Benefits**:
- Simple deployment
- Easy transactions
- Lower latency
- Single codebase

**When to stay**: < 100k users, < 1000 req/s

### Phase 2: Extract Heavy Services

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Core App   │  │ Intelligence │  │ Integration  │
│              │  │   Service    │  │   Service    │
│ Users/Squads │  │              │  │              │
│    Tasks     │  │  LLM Calls   │  │ MCP Servers  │
└──────┬───────┘  │    RAG       │  │  Webhooks    │
       │          │  Learning    │  │              │
       └──────────┴──────────────┴──────────────────┘
```

**Extract First**:
1. **Intelligence Service**: LLM calls, RAG queries (CPU/memory intensive)
2. **Integration Service**: MCP servers, external APIs (network-bound)

**When to extract**: Database CPU > 80%, latency increasing

### Phase 3: Full Microservices

```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│   User   │ │  Squad   │ │   Task   │ │  Billing │
│ Service  │ │ Service  │ │ Service  │ │ Service  │
└────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │            │
┌────▼─────┐ ┌───▼──────┐ ┌───▼──────┐ ┌───▼──────┐
│  User    │ │  Squad   │ │  Task    │ │ Billing  │
│   DB     │ │   DB     │ │   DB     │ │   DB     │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

**When to go full**: > 1M users, > 10k req/s

## Performance Monitoring

### Key Metrics to Track

**Application Metrics**:
- Request latency (p50, p95, p99)
- Requests per second
- Error rate
- Active connections

**Database Metrics**:
- Query latency
- Connection pool usage
- Read/write ratio
- Slow queries

**Cache Metrics**:
- Hit/miss ratio
- Eviction rate
- Memory usage
- Latency

**Worker Metrics**:
- Queue depth
- Job processing time
- Failed jobs
- Worker utilization

### Auto-Scaling Triggers

```yaml
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
```

## Cost Optimization

### Right-Sizing

**Backend Pods**:
```yaml
resources:
  requests:
    cpu: 250m      # Start small
    memory: 512Mi
  limits:
    cpu: 1000m     # Allow bursting
    memory: 2Gi
```

**Database**:
- Start: db.t3.medium (2 vCPU, 4 GB RAM)
- Monitor: CPU and memory usage
- Scale: Upgrade instance class or add replicas

### Cost-Saving Strategies

1. **Use Spot Instances** for non-critical workloads
2. **Auto-scaling** to match demand
3. **Cache aggressively** to reduce database load
4. **Optimize LLM usage** (see Performance doc)
5. **Archive old data** to cheaper storage
6. **Use reserved instances** for baseline capacity

## Capacity Planning

### Scaling Milestones

| Users | Squads | Tasks/Day | Backend Pods | DB Instance | Redis | Monthly Cost |
|-------|--------|-----------|--------------|-------------|-------|--------------|
| 1K    | 500    | 1K        | 2-3          | t3.medium   | 1GB   | $500         |
| 10K   | 5K     | 10K       | 5-10         | t3.large    | 5GB   | $2K          |
| 100K  | 50K    | 100K      | 20-50        | r5.xlarge   | 20GB  | $10K         |
| 1M    | 500K   | 1M        | 100-200      | r5.4xlarge  | 100GB | $50K         |

*Estimates include compute, database, storage, LLM API costs*

## Related Documentation

- [Performance Optimization](./performance.md) - Detailed optimization techniques
- [Monitoring](./monitoring.md) - Observability and alerting
- [Components](./components.md) - Component-level scaling
