# Code Standards - Agent-Squad

## Backend Standards (Python)

### Architecture Principles
- Clean Architecture with domain/application/infrastructure layers
- SOLID principles throughout codebase
- Dependency injection via constructors
- Async/await for all I/O operations

### Code Style
- Black formatter for consistent formatting
- Ruff for linting and import sorting
- MyPy for type checking
- Pydantic for data validation

### Design Patterns
- Template Method: Agent lifecycle in agno_base.py
- Factory: Agent creation in factory.py
- Strategy: LLM provider selection
- Adapter: Framework integrations

### File Organization
```
backend/
├── agents/           # Agent implementations
├── api/v1/          # RESTful endpoints
├── models/          # SQLAlchemy models
├── services/        # Business logic
├── core/            # Infrastructure
└── integrations/    # External services
```

## Frontend Standards (TypeScript)

### Component Architecture
- Next.js App Router with server components default
- Client components only for interactivity
- shadcn/ui components with Tailwind CSS
- Framer Motion for animations

### State Management
- Zustand for global state
- TanStack Query for server state
- React Hook Form with Zod validation
- Local state for UI interactions

### Code Style
- TypeScript strict mode
- ESLint with Next.js config
- Consistent component naming (PascalCase)
- Custom hooks for reusable logic

### File Organization
```
frontend/
├── app/              # Next.js app router
├── components/       # React components
├── stores/          # Zustand stores
├── lib/             # Utilities
└── types/           # TypeScript types
```

## Quality Standards

### Testing
- Backend: pytest with coverage reporting
- Frontend: Component testing with Jest
- Integration tests for API endpoints
- E2E tests for critical user flows

### Documentation
- Docstrings for all public functions
- Type hints for all parameters
- README files for major components
- API documentation with examples

### Security
- JWT authentication with refresh tokens
- Input validation with Pydantic/Zod
- SQL injection prevention via ORM
- XSS protection in frontend

### Performance
- Database connection pooling
- Redis caching for frequent queries
- Code splitting in frontend
- Image optimization with Next.js
