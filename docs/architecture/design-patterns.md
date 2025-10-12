# Design Patterns

This document catalogs all design patterns used in Agent Squad, organized by category.

## Creational Patterns

### 1. Factory Pattern
**Usage**: Agent creation

**Problem**: Need to create different types of agents based on role and specialization.

**Solution**:
```python
class AgentFactory:
    def __init__(
        self,
        llm_providers: Dict[str, LLMProvider],
        message_bus: MessageBus,
        prompt_loader: PromptLoader
    ):
        self.llm_providers = llm_providers
        self.message_bus = message_bus
        self.prompt_loader = prompt_loader

    def create(
        self,
        role: str,
        specialization: Optional[str] = None,
        config: Dict[str, Any] = None
    ) -> BaseAgent:
        """Factory method to create agents"""
        # Load system prompt
        system_prompt = self.prompt_loader.load(role, specialization)

        # Get LLM provider
        provider_name = config.get("llm_provider", "openai")
        llm_provider = self.llm_providers[provider_name]

        # Create agent based on role
        agent_class = self._get_agent_class(role)

        return agent_class(
            agent_id=str(uuid.uuid4()),
            role=role,
            system_prompt=system_prompt,
            llm_provider=llm_provider,
            message_bus=self.message_bus,
            **config
        )

# Usage
agent = AgentFactory.create(
    role="backend_developer",
    specialization="nodejs_express",
    config={"llm_provider": "openai", "llm_model": "gpt-4"}
)
```

### 2. Builder Pattern
**Usage**: Squad creation with complex configuration

**Problem**: Squad has many optional components and requires validation.

**Solution**:
```python
class SquadBuilder:
    def __init__(self):
        self._squad = {}
        self._members = []
        self._projects = []

    def with_name(self, name: str) -> 'SquadBuilder':
        self._squad['name'] = name
        return self

    def add_member(
        self,
        role: str,
        specialization: Optional[str] = None,
        config: Dict = None
    ) -> 'SquadBuilder':
        self._members.append({
            'role': role,
            'specialization': specialization,
            'config': config or {}
        })
        return self

    def with_project(self, project_id: str) -> 'SquadBuilder':
        self._projects.append(project_id)
        return self

    def build(self) -> Squad:
        # Validation
        if not self._squad.get('name'):
            raise ValueError("Squad must have a name")

        if len(self._members) < 2:
            raise ValueError("Squad must have at least 2 members")

        roles = [m['role'] for m in self._members]
        if 'project_manager' not in roles:
            raise ValueError("Squad must have a project manager")

        # Create squad
        return Squad(
            name=self._squad['name'],
            members=self._members,
            projects=self._projects
        )

# Usage
squad = SquadBuilder() \
    .with_name("Backend Team") \
    .add_member("project_manager") \
    .add_member("backend_developer", "python_fastapi") \
    .add_member("tester") \
    .with_project("proj-123") \
    .build()
```

### 3. Singleton Pattern
**Usage**: Database connection, cache manager

**Problem**: Need exactly one instance of shared resources.

**Solution**:
```python
class DatabaseConnection:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db = Prisma()
        return cls._instance

    async def connect(self):
        if not self.db.is_connected():
            await self.db.connect()

    async def disconnect(self):
        if self.db.is_connected():
            await self.db.disconnect()

# Usage (always returns same instance)
db1 = DatabaseConnection()
db2 = DatabaseConnection()
assert db1 is db2  # True
```

---

## Structural Patterns

### 1. Adapter Pattern
**Usage**: LLM provider abstraction

**Problem**: Different LLM providers have different APIs.

**Solution**:
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict],
        **kwargs
    ) -> str:
        pass

class OpenAIAdapter(LLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        messages: List[Dict],
        **kwargs
    ) -> str:
        response = await self.client.chat.completions.create(
            model=kwargs.get('model', 'gpt-4'),
            messages=messages,
            **kwargs
        )
        return response.choices[0].message.content

class AnthropicAdapter(LLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        messages: List[Dict],
        **kwargs
    ) -> str:
        response = await self.client.messages.create(
            model=kwargs.get('model', 'claude-3-opus-20240229'),
            messages=messages,
            **kwargs
        )
        return response.content[0].text

# Usage (same interface for all providers)
provider = OpenAIAdapter(api_key)  # or AnthropicAdapter
result = await provider.generate(messages)
```

### 2. Decorator Pattern
**Usage**: Caching, logging, metrics

**Problem**: Need to add cross-cutting concerns without modifying core logic.

**Solution**:
```python
def cached(ttl: int = 300):
    """Cache decorator with TTL"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try cache first
            cached_result = await cache.get(cache_key)
            if cached_result:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator

def logged(level: str = "INFO"):
    """Logging decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.log(level, f"Calling {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                logger.log(level, f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {str(e)}")
                raise
        return wrapper
    return decorator

# Usage
@cached(ttl=600)
@logged(level="DEBUG")
async def get_squad_by_id(squad_id: str) -> Squad:
    return await squad_repository.get_by_id(squad_id)
```

### 3. Proxy Pattern
**Usage**: Rate limiting for LLM calls

**Problem**: Need to control access to expensive LLM API calls.

**Solution**:
```python
class RateLimitedLLMProxy(LLMProvider):
    def __init__(
        self,
        provider: LLMProvider,
        rate_limiter: RateLimiter
    ):
        self.provider = provider
        self.rate_limiter = rate_limiter

    async def generate(
        self,
        messages: List[Dict],
        **kwargs
    ) -> str:
        # Acquire rate limit token
        async with self.rate_limiter.acquire():
            return await self.provider.generate(messages, **kwargs)

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []

    @asynccontextmanager
    async def acquire(self):
        # Wait if rate limit exceeded
        while len(self._get_recent_requests()) >= self.max_requests:
            await asyncio.sleep(0.1)

        self.requests.append(time.time())
        try:
            yield
        finally:
            pass

# Usage
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
llm = RateLimitedLLMProxy(OpenAIAdapter(), rate_limiter)
```

---

## Behavioral Patterns

### 1. Strategy Pattern
**Usage**: Task assignment strategies

**Problem**: Different algorithms for assigning tasks to agents.

**Solution**:
```python
class TaskAssignmentStrategy(ABC):
    @abstractmethod
    def assign(self, task: Task, squad: Squad) -> str:
        """Return agent_id to assign task to"""
        pass

class RoundRobinStrategy(TaskAssignmentStrategy):
    def __init__(self):
        self.current_index = 0

    def assign(self, task: Task, squad: Squad) -> str:
        eligible_agents = [
            m for m in squad.members
            if self._can_handle(m, task)
        ]
        agent = eligible_agents[self.current_index % len(eligible_agents)]
        self.current_index += 1
        return agent.id

class SkillBasedStrategy(TaskAssignmentStrategy):
    def assign(self, task: Task, squad: Squad) -> str:
        # Match task requirements with agent skills
        for member in squad.members:
            if self._skills_match(member, task):
                return member.id
        raise NoEligibleAgentError()

class WorkloadBalancedStrategy(TaskAssignmentStrategy):
    def assign(self, task: Task, squad: Squad) -> str:
        # Assign to agent with least current workload
        agent_workloads = self._get_current_workloads(squad)
        return min(agent_workloads.items(), key=lambda x: x[1])[0]

# Usage (easily swappable)
class TaskService:
    def __init__(self, strategy: TaskAssignmentStrategy):
        self.strategy = strategy

    async def assign_task(self, task: Task, squad: Squad):
        agent_id = self.strategy.assign(task, squad)
        await self.create_assignment(task.id, agent_id)

# Can swap strategies
service = TaskService(SkillBasedStrategy())
# or
service = TaskService(WorkloadBalancedStrategy())
```

### 2. Observer Pattern
**Usage**: Event system for reactive behaviors

**Problem**: Multiple components need to react to events without tight coupling.

**Solution**:
```python
class EventPublisher:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable):
        if event_type in self.subscribers:
            self.subscribers[event_type].remove(handler)

    async def publish(self, event_type: str, data: Dict):
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                await handler(data)

# Subscribers
async def send_notification(data: Dict):
    await notification_service.send(
        user_id=data['user_id'],
        message=f"Task {data['task_id']} completed"
    )

async def update_metrics(data: Dict):
    await metrics_service.increment("tasks_completed")

async def trigger_learning(data: Dict):
    await learning_service.process_feedback(data['task_id'])

# Setup
events = EventPublisher()
events.subscribe("task.completed", send_notification)
events.subscribe("task.completed", update_metrics)
events.subscribe("task.completed", trigger_learning)

# Publish (all subscribers notified)
await events.publish("task.completed", {
    "task_id": "123",
    "user_id": "user-456"
})
```

### 3. Chain of Responsibility
**Usage**: Message routing through handlers

**Problem**: Different message types need different handling logic.

**Solution**:
```python
class MessageHandler(ABC):
    def __init__(self):
        self.next_handler: Optional[MessageHandler] = None

    def set_next(self, handler: 'MessageHandler') -> 'MessageHandler':
        self.next_handler = handler
        return handler

    async def handle(self, message: Message):
        if self.can_handle(message):
            return await self.process(message)
        elif self.next_handler:
            return await self.next_handler.handle(message)
        else:
            raise ValueError(f"No handler for message type: {message.type}")

    @abstractmethod
    def can_handle(self, message: Message) -> bool:
        pass

    @abstractmethod
    async def process(self, message: Message):
        pass

class TaskAssignmentHandler(MessageHandler):
    def can_handle(self, message: Message) -> bool:
        return message.type == "task_assignment"

    async def process(self, message: Message):
        # Handle task assignment
        pass

class QuestionHandler(MessageHandler):
    def can_handle(self, message: Message) -> bool:
        return message.type == "question"

    async def process(self, message: Message):
        # Handle question
        pass

class CodeReviewHandler(MessageHandler):
    def can_handle(self, message: Message) -> bool:
        return message.type == "code_review"

    async def process(self, message: Message):
        # Handle code review
        pass

# Setup chain
task_handler = TaskAssignmentHandler()
question_handler = QuestionHandler()
code_review_handler = CodeReviewHandler()

task_handler.set_next(question_handler).set_next(code_review_handler)

# Process message (routed through chain)
await task_handler.handle(incoming_message)
```

### 4. Template Method
**Usage**: Common agent workflow with customizable steps

**Problem**: All agents follow similar workflow but with different implementations.

**Solution**:
```python
class BaseAgent(ABC):
    async def receive_message(self, message: Message):
        """Template method - defines workflow"""
        # Step 1: Validate (common)
        if not self._validate_message(message):
            return

        # Step 2: Pre-process (common)
        self._add_to_history(message)

        # Step 3: Retrieve context (common)
        context = await self._get_context(message)

        # Step 4: Process (customizable - subclass implements)
        response = await self.process(message, context)

        # Step 5: Post-process (common)
        if response:
            await self.send_message(response)

    @abstractmethod
    async def process(self, message: Message, context: Dict) -> Optional[Message]:
        """Subclasses implement this"""
        pass

    def _validate_message(self, message: Message) -> bool:
        return message.recipient_id == self.agent_id

    def _add_to_history(self, message: Message):
        self.conversation_history.append(message)

    async def _get_context(self, message: Message) -> Dict:
        return await self.rag_service.query(message.content)

# Subclass implements only the variable part
class DeveloperAgent(BaseAgent):
    async def process(self, message: Message, context: Dict) -> Optional[Message]:
        # Developer-specific processing
        code = await self._generate_code(message, context)
        return Message(content=code, type="code_response")
```

---

## Architectural Patterns

### 1. Repository Pattern
**Usage**: Data access abstraction

**Benefit**: Decouples business logic from data storage.

```python
class SquadRepository(ABC):
    @abstractmethod
    async def save(self, squad: Squad) -> Squad:
        pass

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Squad]:
        pass

class PrismaSquadRepository(SquadRepository):
    async def save(self, squad: Squad) -> Squad:
        # Prisma implementation
        pass
```

### 2. Unit of Work
**Usage**: Transaction management

**Benefit**: Ensures multiple operations succeed or fail together.

```python
class UnitOfWork:
    async def __aenter__(self):
        self.db = await get_db()
        await self.db.execute("BEGIN")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.db.execute("ROLLBACK")
        else:
            await self.db.execute("COMMIT")

# Usage
async with UnitOfWork() as uow:
    await squad_repository.save(squad)
    await member_repository.save_all(members)
    # Both succeed or both fail
```

### 3. Saga Pattern
**Usage**: Distributed transactions in workflows

**Benefit**: Handles long-running, multi-step processes with compensation.

```python
@inngest.create_function(fn_id="execute-task")
async def execute_task(ctx, step):
    try:
        # Step 1
        execution = await step.run("init", lambda: init_execution())

        # Step 2
        context = await step.run("load-context", lambda: load_context())

        # Step 3
        result = await step.run("pm-analysis", lambda: analyze())

        return result

    except Exception as e:
        # Compensation
        await step.run("compensate", lambda: rollback_execution())
        raise
```

## Pattern Selection Guide

| Scenario | Pattern | Why |
|----------|---------|-----|
| Creating objects with complex initialization | Builder, Factory | Encapsulates creation logic |
| Need single instance of resource | Singleton | Shared state management |
| Multiple implementations of interface | Strategy, Adapter | Swap implementations easily |
| Adding behavior without modifying code | Decorator | Open/Closed principle |
| Controlling access to resource | Proxy | Rate limiting, caching |
| Multiple handlers for request | Chain of Responsibility | Flexible routing |
| React to events | Observer | Loose coupling |
| Common algorithm with variations | Template Method | Code reuse |
| Isolate data access | Repository | Testability, flexibility |

## Related Documentation

- [Design Principles](./design-principles.md) - Underlying principles
- [Components](./components.md) - How components use these patterns
- [Scalability](./scalability.md) - Patterns for scale
