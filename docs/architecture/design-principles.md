# Design Principles

## SOLID Principles

### 1. Single Responsibility Principle (SRP)
**Definition**: Each module, class, and function should have one and only one reason to change.

**Bad Example**:
```python
class UserManager:
    def create_user(self, data):
        # User creation logic
        pass

    def send_welcome_email(self, user):
        # Email sending logic
        pass

    def charge_subscription(self, user):
        # Payment logic
        pass
```

**Good Example**:
```python
class UserService:
    """Handles user-related business logic"""
    def create_user(self, data):
        pass

class EmailService:
    """Handles email operations"""
    def send_welcome_email(self, user):
        pass

class PaymentService:
    """Handles payment operations"""
    def charge_subscription(self, user):
        pass
```

### 2. Open/Closed Principle (OCP)
**Definition**: Software entities should be open for extension but closed for modification.

**Implementation via Inheritance**:
```python
from abc import ABC, abstractmethod

# Base class - closed for modification
class BaseAgent(ABC):
    @abstractmethod
    async def process_message(self, message: str) -> str:
        pass

# Extended for specific roles - open for extension
class ProjectManagerAgent(BaseAgent):
    async def process_message(self, message: str) -> str:
        # PM-specific logic
        return await self._analyze_and_delegate(message)

class DeveloperAgent(BaseAgent):
    async def process_message(self, message: str) -> str:
        # Developer-specific logic
        return await self._implement_solution(message)
```

### 3. Liskov Substitution Principle (LSP)
**Definition**: Objects of a superclass should be replaceable with objects of a subclass without breaking the application.

**Example**:
```python
def execute_agent_task(agent: BaseAgent, message: str):
    """Works with any BaseAgent subclass"""
    result = await agent.process_message(message)
    return result

# Both work correctly
pm_agent = ProjectManagerAgent()
dev_agent = DeveloperAgent()

execute_agent_task(pm_agent, "Create plan")  # ✓ Works
execute_agent_task(dev_agent, "Write code")  # ✓ Works
```

### 4. Interface Segregation Principle (ISP)
**Definition**: Clients should not be forced to depend on interfaces they don't use.

**Bad Example**:
```python
class AgentInterface(ABC):
    @abstractmethod
    def process_message(self): pass

    @abstractmethod
    def write_code(self): pass

    @abstractmethod
    def review_code(self): pass

    @abstractmethod
    def run_tests(self): pass

# PM agent forced to implement unnecessary methods
class PMAgent(AgentInterface):
    def write_code(self):
        raise NotImplementedError("PM doesn't write code")
```

**Good Example**:
```python
class MessageProcessor(ABC):
    @abstractmethod
    def process_message(self): pass

class CodeWriter(ABC):
    @abstractmethod
    def write_code(self): pass

class CodeReviewer(ABC):
    @abstractmethod
    def review_code(self): pass

# Each agent implements only what it needs
class PMAgent(MessageProcessor, CodeReviewer):
    def process_message(self): pass
    def review_code(self): pass

class DeveloperAgent(MessageProcessor, CodeWriter):
    def process_message(self): pass
    def write_code(self): pass
```

### 5. Dependency Inversion Principle (DIP)
**Definition**: High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Bad Example**:
```python
class TaskExecutor:
    def __init__(self):
        self.openai_client = OpenAI()  # Direct dependency on concrete class

    async def execute(self, task):
        return await self.openai_client.generate(task)
```

**Good Example**:
```python
# Abstraction
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        pass

# High-level module depends on abstraction
class TaskExecutor:
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider

    async def execute(self, task):
        return await self.llm_provider.generate(task)

# Low-level modules implement abstraction
class OpenAIProvider(LLMProvider):
    async def generate(self, prompt: str) -> str:
        # OpenAI implementation
        pass

class AnthropicProvider(LLMProvider):
    async def generate(self, prompt: str) -> str:
        # Anthropic implementation
        pass

# Dependency injection
executor = TaskExecutor(OpenAIProvider())  # Easy to swap
```

---

## Clean Architecture

### Layer Structure

```
┌─────────────────────────────────────────────┐
│          External Interfaces                │
│  (Web, CLI, External APIs)                  │
└──────────────────┬──────────────────────────┘
                   │ Dependencies point inward
┌──────────────────▼──────────────────────────┐
│       Interface Adapters                    │
│  (Controllers, Presenters, Gateways)        │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│         Use Cases / Application             │
│  (Business Logic, Workflows)                │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              Entities                       │
│  (Core Business Objects)                    │
└─────────────────────────────────────────────┘
```

### Key Rules

1. **Source code dependencies point inward**
   - Outer layers can depend on inner layers
      - Inner layers never depend on outer layers

2. **Inner layers are stable**
   - Core business logic doesn't change when UI changes
   - Entities don't know about databases or APIs

3. **Framework independence**
   - Business logic doesn't depend on FastAPI, Next.js, etc.
   - Can swap frameworks without changing core logic

4. **Testability**
   - Core logic can be tested without UI, database, or external services

### Implementation Example

```python
# Layer 4: Entities (Core Business Logic)
class Squad:
    def __init__(self, name: str, members: List[Member]):
        self.name = name
        self.members = members

    def can_execute_task(self, task: Task) -> bool:
        """Core business rule"""
        has_pm = any(m.role == "project_manager" for m in self.members)
        has_dev = any(m.role.startswith("developer_") for m in self.members)
        return has_pm and has_dev

# Layer 3: Use Cases (Application Logic)
class CreateSquadUseCase:
    def __init__(self, repository: SquadRepository, event_bus: EventBus):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, request: CreateSquadRequest) -> Squad:
        # Validate
        squad = Squad(request.name, request.members)
        if not squad.can_execute_task(Task("test")):
            raise InvalidSquadComposition()

        # Persist
        saved_squad = await self.repository.save(squad)

        # Publish event
        await self.event_bus.publish("squad.created", saved_squad)

        return saved_squad

# Layer 2: Interface Adapters (Controllers)
@router.post("/squads")
async def create_squad(
    request: CreateSquadDTO,
    use_case: CreateSquadUseCase = Depends()
):
    squad = await use_case.execute(request)
    return SquadResponseDTO.from_entity(squad)

# Layer 1: External Interfaces (FastAPI)
app = FastAPI()
app.include_router(router)
```

---

## Domain-Driven Design (DDD)

### Bounded Contexts

Our system is organized into the following bounded contexts:

```
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   User Management   │  │   Squad Management  │  │  Task Execution     │
│                     │  │                     │  │                     │
│  - Users            │  │  - Squads           │  │  - Tasks            │
│  - Authentication   │  │  - Squad Members    │  │  - Executions       │
│  - Subscriptions    │  │  - Configurations   │  │  - Agent Messages   │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘

┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│   Integration Mgmt  │  │  Knowledge Base     │  │   Billing           │
│                     │  │                     │  │                     │
│  - MCP Servers      │  │  - Documents        │  │  - Payments         │
│  - Git/Jira         │  │  - RAG System       │  │  - Invoices         │
│  - Webhooks         │  │  - Embeddings       │  │  - Usage Tracking   │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### Ubiquitous Language

**Squad Domain**:
- **Squad**: Group of AI agents working together
- **Squad Member**: Individual AI agent with a specific role
- **Squad Composition**: The combination of roles in a squad
- **Agent Configuration**: Settings for an agent (LLM provider, model, etc.)

**Task Domain**:
- **Task**: Work item to be completed by squad
- **Task Execution**: Instance of squad working on a task
- **Sub-task**: Smaller piece of work delegated to agent
- **Task Status**: pending, in_progress, blocked, completed

**Agent Domain**:
- **Agent**: AI entity that performs work
- **Role**: Type of agent (PM, Developer, etc.)
- **Specialization**: Specific expertise (Node.js, Python, etc.)
- **A2A Message**: Communication between agents

### Aggregates

**Squad Aggregate** (Root: Squad):
```
Squad
├── Squad Members (entities)
├── Projects (entities)
└── Configurations (value objects)
```

**Task Execution Aggregate** (Root: Task Execution):
```
Task Execution
├── Task (entity)
├── Agent Messages (entities)
├── Execution Logs (value objects)
└── Feedback (entity)
```

### Repository Pattern

```python
# Domain entity
class Squad:
    def __init__(self, id: str, name: str, members: List[SquadMember]):
        self.id = id
        self.name = name
        self.members = members

# Repository interface (in domain layer)
class SquadRepository(ABC):
    @abstractmethod
    async def save(self, squad: Squad) -> Squad:
        pass

    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[Squad]:
        pass

# Repository implementation (in infrastructure layer)
class PrismaSquadRepository(SquadRepository):
    async def save(self, squad: Squad) -> Squad:
        # Prisma-specific implementation
        pass

    async def find_by_id(self, id: str) -> Optional[Squad]:
        # Prisma-specific implementation
        pass
```

---

## Microservices Principles (Future)

### Evolution Path

**Phase 1: Modular Monolith** ⬅️ Start here
- Single deployment
- Clear module boundaries
- Shared database
- Benefits: Simple to develop, easy to deploy

**Phase 2: Extract Heavy Services**
- Intelligence Service (LLM calls, RAG)
- Integration Service (MCP, webhooks)
- Keep core logic together

**Phase 3: Full Microservices** (If needed)
- Complete service separation
- Event-driven communication
- Database per service

### Service Boundaries

When extracting to microservices, consider these boundaries:

```
User Service
├── Authentication
├── User management
└── Subscriptions

Squad Service
├── Squad management
├── Agent configuration
└── Squad lifecycle

Task Service
├── Task management
├── Task execution
├── Workflow orchestration

Intelligence Service (Extract first if needed)
├── LLM calls
├── RAG queries
├── Embeddings
└── Learning pipeline

Integration Service (Extract first if needed)
├── MCP servers
├── Git operations
├── Jira operations
└── Webhooks
```

### Communication Patterns

**Synchronous**: REST/gRPC for immediate responses
**Asynchronous**: Events for workflows and notifications

```python
# Service A publishes event
await event_bus.publish("squad.created", {
    "squad_id": squad.id,
    "user_id": user.id
})

# Service B subscribes and reacts
@event_bus.subscribe("squad.created")
async def handle_squad_created(event):
    await initialize_knowledge_base(event.squad_id)
```

---

## Key Takeaways

1. **SOLID Principles**: Apply consistently for maintainable code
2. **Clean Architecture**: Keep business logic independent of frameworks
3. **DDD**: Organize around business domains, not technical layers
4. **Start Simple**: Begin with modular monolith, extract services only when needed
5. **Depend on Abstractions**: Makes code flexible and testable

## Related Documentation

- [Design Patterns](./design-patterns.md) - Specific patterns we use
- [Components](./components.md) - How components implement these principles
- [Scalability](./scalability.md) - How these principles enable scaling
