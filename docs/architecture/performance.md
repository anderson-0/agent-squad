# Performance Optimization

## Database Performance

### Query Optimization

**Use Select to Limit Fields**:
```python
# ❌ BAD: Fetches all fields
user = await db.user.find_unique(where={"id": user_id})

# ✅ GOOD: Fetch only needed fields
user = await db.user.find_unique(
    where={"id": user_id},
    select={"id": True, "email": True, "name": True}
    # Don't fetch passwordHash, createdAt, etc.
)
```

**Avoid N+1 Queries**:
```python
# ❌ BAD: N+1 query problem
squads = await db.squad.find_many()
for squad in squads:
    squad.members = await db.squad_member.find_many(
        where={"squadId": squad.id}
    )

# ✅ GOOD: Single query with join
squads = await db.squad.find_many(
    include={"members": True}
)
```

**Use Pagination**:
```python
async def get_squads_paginated(
    user_id: str,
    page: int = 1,
    page_size: int = 20
) -> PaginatedResponse:
    skip = (page - 1) * page_size

    # Run in parallel
    squads, total = await asyncio.gather(
        db.squad.find_many(
            where={"userId": user_id},
            skip=skip,
            take=page_size,
            include={"members": True}
        ),
        db.squad.count(where={"userId": user_id})
    )

    return PaginatedResponse(
        data=squads,
        page=page,
        page_size=page_size,
        total=total,
        pages=(total + page_size - 1) // page_size
    )
```

**Cursor-Based Pagination for Large Datasets**:
```python
async def get_messages(
    execution_id: str,
    cursor: Optional[str] = None,
    limit: int = 100
):
    return await db.agent_message.find_many(
        where={"taskExecutionId": execution_id},
        take=limit,
        cursor={"id": cursor} if cursor else None,
        order_by={"createdAt": "desc"}
    )
```

### Indexing Strategy

**Frequently Queried Fields**:
```sql
-- Single column indexes
CREATE INDEX idx_squads_user_id ON squads(user_id);
CREATE INDEX idx_tasks_squad_id ON tasks(squad_id);
CREATE INDEX idx_agent_messages_execution_id ON agent_messages(task_execution_id);

-- Composite indexes for common queries
CREATE INDEX idx_tasks_project_status_priority
  ON tasks(project_id, status, priority);

CREATE INDEX idx_executions_squad_status_created
  ON task_executions(squad_id, status, created_at DESC);

-- Partial indexes for common filters
CREATE INDEX idx_active_squads
  ON squads(user_id)
  WHERE status = 'active';

CREATE INDEX idx_pending_tasks
  ON tasks(squad_id, priority)
  WHERE status = 'pending';
```

**Prisma Schema**:
```prisma
model Squad {
  id String @id @default(uuid())
  userId String
  status String @default("active")

  @@index([userId])
  @@index([userId, status])
}

model Task {
  id String @id @default(uuid())
  projectId String
  status String
  priority String

  @@index([projectId, status, priority])
}
```

### Connection Pooling

```python
from prisma import Prisma

# Configure pool
db = Prisma(
    datasource={
        "url": DATABASE_URL,
        "pool": {
            "min": 5,           # Minimum connections
            "max": 20,          # Maximum connections
            "idle_timeout": 30000,  # 30 seconds
            "connection_timeout": 5000  # 5 seconds
        }
    }
)
```

**Sizing Guidelines**:
- Formula: `(num_pods * max_connections_per_pod) < database_max_connections`
- Start with 20 connections per pod
- Monitor connection wait time
- Increase if wait time > 100ms

## API Performance

### Response Compression

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # Only compress responses > 1KB
)
```

### Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Setup
FastAPICache.init(RedisBackend(redis), prefix="api-cache")

# Usage
@router.get("/squads/{squad_id}")
@cache(expire=300)  # Cache for 5 minutes
async def get_squad(squad_id: str):
    return await squad_service.get_by_id(squad_id)

# Cache with dynamic key
@router.get("/squads")
@cache(expire=60)
async def get_user_squads(
    user_id: str = Depends(get_current_user_id)
):
    return await squad_service.get_by_user(user_id)
```

### Async Operations

```python
# ❌ BAD: Sequential operations (slow)
user = await get_user(user_id)
squads = await get_squads(user_id)
notifications = await get_notifications(user_id)

# ✅ GOOD: Parallel operations (fast)
user, squads, notifications = await asyncio.gather(
    get_user(user_id),
    get_squads(user_id),
    get_notifications(user_id)
)
```

### Request Batching

```python
from dataloader import DataLoader

# Batch multiple get_user calls
async def batch_load_users(user_ids: List[str]) -> List[User]:
    users = await db.user.find_many(
        where={"id": {"in": user_ids}}
    )
    # Return in same order as user_ids
    user_map = {u.id: u for u in users}
    return [user_map.get(uid) for uid in user_ids]

user_loader = DataLoader(batch_load_users)

# These get batched into single query
user1 = await user_loader.load("user-1")
user2 = await user_loader.load("user-2")
user3 = await user_loader.load("user-3")
```

## LLM Call Optimization

### Batching Requests

```python
class LLMBatcher:
    def __init__(self, batch_size: int = 10, wait_time: float = 0.5):
        self.batch_size = batch_size
        self.wait_time = wait_time
        self.queue: List[Tuple[str, asyncio.Future]] = []
        self.task = None

    async def add(self, prompt: str) -> str:
        future = asyncio.Future()
        self.queue.append((prompt, future))

        # Start batch processor if not running
        if self.task is None:
            self.task = asyncio.create_task(self._process_loop())

        return await future

    async def _process_loop(self):
        while self.queue:
            await asyncio.sleep(self.wait_time)

            if not self.queue:
                break

            batch = self.queue[:self.batch_size]
            self.queue = self.queue[self.batch_size:]

            await self._process_batch(batch)

        self.task = None

    async def _process_batch(self, batch: List[Tuple[str, asyncio.Future]]):
        prompts = [p for p, _ in batch]

        try:
            # Batch API call
            results = await llm_provider.batch_generate(prompts)

            for (_, future), result in zip(batch, results):
                future.set_result(result)
        except Exception as e:
            for _, future in batch:
                future.set_exception(e)
```

### Caching LLM Responses

```python
import hashlib
import json

async def get_llm_response(
    prompt: str,
    model: str = "gpt-4",
    **kwargs
) -> str:
    # Create cache key
    cache_data = {"prompt": prompt, "model": model, **kwargs}
    cache_key = hashlib.sha256(
        json.dumps(cache_data, sort_keys=True).encode()
    ).hexdigest()

    # Check cache
    cached = await redis.get(f"llm:{cache_key}")
    if cached:
        return cached

    # Generate response
    response = await llm_provider.generate(prompt, model=model, **kwargs)

    # Cache for 24 hours
    await redis.setex(f"llm:{cache_key}", 86400, response)

    return response
```

### Streaming Responses

```python
from fastapi.responses import StreamingResponse

@router.post("/agent/chat/stream")
async def stream_agent_response(message: str):
    async def generate():
        async for chunk in agent.stream_response(message):
            # Server-Sent Events format
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Prompt Optimization

```python
# ❌ BAD: Verbose, wasteful tokens
prompt = """
You are a helpful AI assistant that helps with coding tasks.
Please analyze the following code and provide suggestions for improvement.
Make sure to consider best practices, performance, and maintainability.

Here is the code:
[large code block]

Please provide detailed feedback with examples.
"""

# ✅ GOOD: Concise, clear
prompt = """
Analyze this code for best practices, performance, and maintainability:

[large code block]

Provide specific improvements with examples.
"""
```

### Rate Limiting

```python
from aiolimiter import AsyncLimiter

# 50 requests per minute to OpenAI
llm_limiter = AsyncLimiter(max_rate=50, time_period=60)

async def call_llm(prompt: str) -> str:
    async with llm_limiter:
        return await openai_client.generate(prompt)
```

## Frontend Performance

### Code Splitting

```typescript
// Dynamic imports for heavy components
const SquadBuilder = dynamic(
  () => import('@/components/squad-builder'),
  {
    loading: () => <SquadBuilderSkeleton />,
    ssr: false  // Don't server-render heavy component
  }
);

const AgentMessageViewer = dynamic(
  () => import('@/components/agent-message-viewer'),
  { ssr: false }
);
```

### Image Optimization

```typescript
import Image from 'next/image';

// Automatic optimization
<Image
  src="/avatar.jpg"
  width={40}
  height={40}
  alt="User avatar"
  loading="lazy"       // Lazy load
  quality={75}         // Reduce quality slightly
  placeholder="blur"   // Show blur while loading
/>
```

### Data Fetching

```typescript
// Use React Query for automatic caching
const { data: squads, isLoading } = useQuery({
  queryKey: ['squads', userId],
  queryFn: () => api.getSquads(userId),
  staleTime: 5 * 60 * 1000,      // Fresh for 5 min
  cacheTime: 10 * 60 * 1000,     // Keep in cache 10 min
  refetchOnWindowFocus: false,   // Don't refetch on focus
});

// Prefetch on hover
const prefetchSquad = usePrefetchQuery();

<Link
  href={`/squads/${squad.id}`}
  onMouseEnter={() => {
    prefetchSquad({
      queryKey: ['squad', squad.id],
      queryFn: () => api.getSquad(squad.id)
    })
  }}
>
  {squad.name}
</Link>
```

### Bundle Optimization

```javascript
// next.config.js
module.exports = {
  // Enable SWC minification
  swcMinify: true,

  // Analyze bundle size
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
        // Use lighter date library
        'moment': 'dayjs'
      };
    }
    return config;
  },

  // Optimize fonts
  optimizeFonts: true,

  // Compress output
  compress: true,
};
```

## Monitoring Performance

### Application Metrics

```python
from prometheus_client import Histogram, Counter

# Request latency
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint', 'status']
)

# Usage
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).observe(duration)

    return response
```

### Database Query Monitoring

```python
# Log slow queries
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop()

    if total > 1.0:  # Log queries > 1 second
        logger.warning(
            "Slow query",
            duration=total,
            statement=statement[:200]
        )
```

### LLM Cost Tracking

```python
async def track_llm_usage(
    squad_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int
):
    # Calculate cost
    cost = calculate_cost(model, input_tokens, output_tokens)

    # Store
    await db.llm_usage.create({
        "squadId": squad_id,
        "model": model,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "cost": cost,
        "timestamp": datetime.utcnow()
    })

    # Track metric
    llm_cost_total.labels(squad_id=squad_id, model=model).inc(cost)
```

## Performance Testing

### Load Testing with k6

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up
    { duration: '5m', target: 100 },   // Stay at 100 users
    { duration: '2m', target: 200 },   // Ramp to 200 users
    { duration: '5m', target: 200 },   // Stay at 200 users
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% < 500ms
    http_req_failed: ['rate<0.01'],    // Error rate < 1%
  },
};

export default function () {
  // Test squad listing
  const res = http.get('https://api.example.com/squads');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

## Performance Benchmarks

### Target Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | < 200ms | 95th percentile |
| API Response Time (p99) | < 500ms | 99th percentile |
| Database Query Time | < 50ms | Average |
| LLM Response Time | < 2s | Streaming first token |
| Page Load Time (FCP) | < 1.5s | First Contentful Paint |
| Page Load Time (LCP) | < 2.5s | Largest Contentful Paint |
| Cache Hit Ratio | > 80% | Redis metrics |
| Error Rate | < 0.1% | All requests |

### Core Web Vitals

```typescript
// Monitor Core Web Vitals in Next.js
export function reportWebVitals(metric) {
  if (metric.label === 'web-vital') {
    // Send to analytics
    analytics.track('Web Vital', {
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
    });
  }
}
```

**Targets**:
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

## Related Documentation

- [Scalability](./scalability.md) - Horizontal scaling strategies
- [Monitoring](./monitoring.md) - Observability and alerting
- [Database Design](./components.md) - Database schema optimization
