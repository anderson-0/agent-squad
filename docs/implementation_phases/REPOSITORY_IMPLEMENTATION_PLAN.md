# Repository Digestion System - Implementation Plan

## Executive Summary

**Objective:** Build a repository understanding system that enables developer agents to work with real-time git repositories with full context awareness.

**Chosen Strategy:** Incremental implementation building from Strategy 4 → Strategy 7 → Strategy 8

**Timeline:** 4-5 weeks
- Phase 1 (Weeks 1-2): Strategy 4 (Dependency Graph) - Production ready
- Phase 2 (Week 3): Strategy 7 (+ Folder Summaries) - Enhanced with AI
- Phase 3 (Weeks 4-5): Strategy 8 (+ Vector Search) - Optional enhancement

**Expected Outcomes:**
- Phase 1: 85% context accuracy, < 2s build time, zero AI costs
- Phase 2: 90% context accuracy, -7% wasted tokens, minimal AI costs
- Phase 3: 93% context accuracy, +7% file recall, better NL understanding

---

## 🧩 Strategy Breakdown & Evolution

### Strategy 4: Dependency Graph (Foundation)

**What it is:**
Uses code structure analysis to understand repositories. Builds a graph of file dependencies (imports) and uses graph traversal to find related files.

**Core Components:**
- Repository scanner (file inventory, tech stack detection)
- Import parsers (Python, JavaScript/TypeScript)
- Dependency graph builder (forward & reverse edges)
- File ranking algorithm (multi-factor scoring)
- Smart context builder (keyword + graph-based search)
- File watcher (real-time updates)

**What it provides:**
- ✅ Understands code structure and dependencies
- ✅ Fast file discovery (< 1 second)
- ✅ Real-time freshness via file watching
- ✅ Works completely offline (no external deps)
- ✅ 85% context accuracy
- ✅ Explainable results (shows why files included)

**Limitations:**
- ❌ No high-level understanding of folder purposes
- ❌ Agent must infer module organization
- ❌ No semantic understanding (keyword matching only)

**Key Metrics:**
- Context accuracy: 85%
- Context build time: < 2 seconds
- Token utilization: > 70%
- Cache hit rate: > 80%
- Cost: $0 (infrastructure only)

---

### Strategy 5: AI-Powered Folder Summaries (Orientation Layer)

**What it is:**
Generates concise AI summaries (200-500 tokens) for each code folder, describing purpose, key files, and functionality.

**Core Components:**
- Folder identification (finds relevant folders for task)
- AI summarization (Claude/GPT-4 generates summaries)
- Summary caching (LRU cache, invalidate on changes)
- Selective summarization (only module folders, skip utils/tests)

**What it provides:**
- ✅ High-level understanding of repository organization
- ✅ Quick orientation for agents (knows where to look)
- ✅ Reduces wasted context on wrong modules
- ✅ Helpful for large, multi-module codebases

**Limitations:**
- ❌ Requires LLM for summary generation
- ❌ Small AI cost (~$0.001 per folder)
- ❌ Summaries can go stale (mitigated by invalidation)

**Note:** Strategy 5 is NOT implemented standalone - it's always combined with Strategy 4 to create Strategy 7.

---

### Strategy 7: Dependency Graph + Folder Summaries (Hybrid Excellence)

**What it is:**
**Strategy 4 + Strategy 5** - Combines structural understanding (dependency graph) with high-level orientation (folder summaries).

**How they work together:**
1. **Folder summaries** provide overview → Agent knows which modules are relevant
2. **Dependency graph** provides precision → Agent gets exact files needed
3. **Two-tier context** = Summaries (orientation) + Full files (execution)

**Architecture:**
```python
class EnhancedContextBuilder(DependencyGraphContextBuilder):
    """Extends Strategy 4, adds folder summaries"""

    async def build_context(self, task: str) -> AgentContext:
        # 1. Identify relevant folders for task
        folders = await self._identify_relevant_folders(task)

        # 2. Generate summaries (lazy, cached)
        for folder in folders:
            await self._summarize_folder(folder)

        # 3. Use Strategy 4 for file discovery & ranking
        return await super().build_context(task)
```

**Key Improvements over Strategy 4:**
- ✅ +5% context accuracy (85% → 90%)
- ✅ -7% wasted tokens (15% → 8%)
- ✅ Faster agent navigation (knows where to look)
- ✅ Better file discovery (avoids wrong modules)
- ✅ Still fast (warm cache = same speed as Strategy 4)

**Key Metrics:**
- Context accuracy: 90% (+5%)
- Wasted tokens: 8% (-7% improvement)
- Build time (warm): < 2 seconds
- Build time (cold): 1-2 seconds (first-time summary gen)
- Cost: ~$0.41/month per repo

**When to use:**
- Complex multi-module codebases
- Agents working on unfamiliar repositories
- Teams valuing +5% accuracy for ~$20/month (50 repos)

---

### Strategy 8: Strategy 7 + Vector Search (Semantic Enhancement)

**What it is:**
**Strategy 7 + Vector Similarity Search** - Adds semantic understanding to find conceptually related files beyond keyword/dependency matches.

**How it enhances Strategy 7:**
```python
class VectorEnhancedContextBuilder(EnhancedContextBuilder):
    """Extends Strategy 7, adds vector search"""

    async def _find_relevant_files(self, task: str) -> set[str]:
        # 1. Get Strategy 7 results (keyword + dependency + folders)
        candidates = await super()._find_relevant_files(task)

        # 2. Add vector similarity search
        semantic_files = await self._search_by_similarity(task, top_k=15)

        # 3. Combine both approaches
        return candidates | semantic_files
```

**What vector search adds:**
- ✅ Semantic understanding ("login" ≈ "authentication" ≈ "auth")
- ✅ Natural language query handling
- ✅ Cross-domain file discovery (finds implicit relationships)
- ✅ Pattern recognition (finds similar code structures)
- ✅ Better for new features (finds examples to follow)

**Key Improvements over Strategy 7:**
- ✅ +3% context accuracy (90% → 93%)
- ✅ +7% file discovery recall (85% → 92%)
- ✅ +15% natural language task performance (80% → 95%)
- ✅ -2% wasted tokens (8% → 6%)
- ⚠️ +0.2s per query (vector search time)

**Key Metrics:**
- Context accuracy: 93% (+3%)
- File recall: 92% (+7%)
- Natural language tasks: 95% (+15%)
- Build time: 0.7 seconds (+0.2s)
- Cost: ~$0.41/month per repo (same as Strategy 7)

**When to use:**
- Heavy natural language queries
- New feature development (finding patterns)
- Cross-domain work (analytics + payments)
- Large teams with diverse use cases
- Already have Pinecone infrastructure

---

## 🎯 Strategy Comparison Summary

| Aspect | Strategy 4 | Strategy 7 | Strategy 8 |
|--------|-----------|-----------|-----------|
| **Foundation** | Dependency Graph | Strategy 4 + Folder Summaries | Strategy 7 + Vector Search |
| **Context Accuracy** | 85% | 90% (+5%) | 93% (+3%) |
| **File Recall** | 85% | 85% | 92% (+7%) |
| **Wasted Tokens** | 15% | 8% (-7%) | 6% (-2%) |
| **Build Time** | 0.5s | 0.5s (warm) / 1-2s (cold) | 0.7s |
| **NL Query Performance** | 70% | 80% | 95% (+15%) |
| **External Dependencies** | None | None | Pinecone + Embeddings |
| **Cost per Repo** | $0 | ~$0.41/month | ~$0.41/month |
| **Lines of Code** | ~1000 | +~200 | +~150 |
| **Breaking Changes** | N/A | Zero (extends S4) | Zero (extends S7) |

### Key Insight: Incremental Value Stack

```
Strategy 4: Foundation
├── Dependency graph understanding
├── File ranking & caching
└── Real-time file watching
    ↓
Strategy 7: + Orientation Layer
├── Everything from Strategy 4
├── + Folder summaries (knows WHERE to look)
└── + Better navigation (-7% wasted tokens)
    ↓
Strategy 8: + Semantic Layer
├── Everything from Strategy 7
├── + Vector similarity (knows WHAT'S related)
└── + Natural language understanding (+15% NL tasks)
```

Each strategy **extends** the previous one without breaking changes. You can:
- ✅ Stop at Strategy 4 (solid foundation, zero AI costs)
- ✅ Stop at Strategy 7 (excellent accuracy, minimal costs)
- ✅ Add Strategy 8 later (optional enhancement for specific use cases)

---

## 🎯 Why This Approach?

### The Incremental Strategy

We're implementing **Strategy 4 first**, then extending to **Strategy 7**, rather than building Strategy 7 from scratch.

### Key Rationale

#### 1. **Deliver Value Faster**
- Working system in production after 2 weeks
- Users get 85% context accuracy (Strategy 4) immediately
- Don't wait 3 weeks for 90% accuracy (Strategy 7)
- Validates architecture with real usage before adding complexity

#### 2. **Lower Risk**
- Test dependency graph independently before adding AI layer
- Each phase has clear success/failure criteria
- Can stop at Strategy 4 if it meets needs
- Easier to debug (fewer moving parts initially)

#### 3. **No Breaking Changes**
- Strategy 7 extends Strategy 4 via inheritance
- Existing code continues to work unchanged
- Can run both strategies simultaneously (A/B testing)
- Easy rollback if Strategy 7 underperforms

#### 4. **Cost Validation**
- Strategy 4 has zero AI costs
- Validate that dependency graph works before investing in AI summaries
- Measure actual token savings to justify AI costs
- Can optimize Strategy 4 before adding summaries

#### 5. **Learn & Adapt**
- Gather real usage metrics from Strategy 4
- Understand which folders agents access most
- Optimize summarization based on actual patterns
- Make data-driven decisions about Strategy 7 features

---

## 📊 Benefits vs Alternative Approaches

### Comparison with Other Implementation Strategies

| Approach | Time to Value | Risk | Flexibility | Total Time | Cost |
|----------|---------------|------|-------------|------------|------|
| **Build Strategy 7 from scratch** | 3 weeks | High | Low | 3 weeks | Medium |
| **Build Strategy 4 → Strategy 7** | 2 weeks | Low | High | 3 weeks | Medium |
| **Build Strategy 3 (Semantic)** | 4-5 weeks | High | Medium | 4-5 weeks | Very High |
| **Build Strategy 1 (Full Context)** | 1 week | Very Low | None | 1 week | Very High |

### Why Not Build Strategy 7 Directly?

**Reasons to avoid building Strategy 7 from scratch:**

1. **Higher Initial Complexity**
   - Two systems to build simultaneously
   - Harder to isolate bugs
   - More integration points to test

2. **Delayed Feedback**
   - 3 weeks before seeing any results
   - Can't validate dependency graph works
   - Might discover issues late

3. **Sunken Cost Fallacy**
   - If summaries don't help, harder to roll back
   - Already invested 3 weeks in combined system
   - Incremental approach allows stopping at Strategy 4

4. **Optimization Blindness**
   - Don't know what to optimize without usage data
   - Might summarize wrong folders
   - Can't tune based on real patterns

### Why Not Use Strategy 3 (Semantic Search)?

**Reasons to avoid semantic search:**

1. **External Dependencies**
   - Requires vector database (Pinecone, Weaviate, etc.)
   - Requires embedding API (OpenAI, Cohere, etc.)
   - More infrastructure to maintain

2. **Higher Costs**
   - Embedding all files: ~$50-200 per repo initially
   - Re-embedding on changes: ongoing cost
   - Storage costs for vectors

3. **Slower Initial Indexing**
   - 1-5 seconds per file to embed
   - Large repos take 30-60 minutes
   - Blocks system startup

4. **Ignores Code Structure**
   - Doesn't understand imports/dependencies
   - Can miss related files with different wording
   - No understanding of call graphs

---

## 🏗️ Architecture Design Principles

### 1. **Extensibility Through Inheritance**

```python
# Base class defines contract
class RepositoryContextBuilder(ABC):
    @abstractmethod
    async def build_context(self, task: str) -> AgentContext:
        pass

# Strategy 4 implements full functionality
class DependencyGraphContextBuilder(RepositoryContextBuilder):
    async def build_context(self, task: str) -> AgentContext:
        # Complete implementation

# Strategy 7 extends, doesn't replace
class EnhancedContextBuilder(DependencyGraphContextBuilder):
    async def build_context(self, task: str) -> AgentContext:
        # Add summaries, then call parent
        return await super().build_context(task)
```

**Benefits:**
- Zero code duplication
- Changes to Strategy 4 automatically benefit Strategy 7
- Easy to add Strategy 8, 9, etc. later
- Clear separation of concerns

### 2. **Configuration Over Code Changes**

```python
# Factory pattern for zero-change switching
def create_context_builder(repo_path: str) -> RepositoryContextBuilder:
    if config.STRATEGY == "enhanced":
        return EnhancedContextBuilder(repo_path)
    else:
        return DependencyGraphContextBuilder(repo_path)

# Usage never changes
context_builder = create_context_builder(repo_path)
```

**Benefits:**
- Toggle strategies via environment variable
- A/B testing without code deployment
- Instant rollback in emergency
- Gradual rollout (10% → 50% → 100%)

### 3. **Graceful Degradation**

```python
class EnhancedContextBuilder(DependencyGraphContextBuilder):
    async def _build_overview(self) -> str:
        try:
            # Try to add summaries
            if self.enable_summaries:
                return await self._build_overview_with_summaries()
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")

        # Fallback to Strategy 4
        return await super()._build_overview()
```

**Benefits:**
- System never fails due to summaries
- AI service outages don't break system
- Automatic fallback to known-good behavior

### 4. **Observable & Measurable**

```python
# Built-in metrics
context_builder.metrics.context_accuracy  # 85% → 90%
context_builder.metrics.wasted_tokens     # 15% → 8%
context_builder.metrics.build_time_ms     # Track performance
context_builder.metrics.summary_cache_hits # Measure caching
```

**Benefits:**
- Data-driven decisions
- Easy to compare strategies
- Identify optimization opportunities
- Justify AI costs with metrics

---

## 📅 Detailed Implementation Plan

### 📅 Phase 1: Strategy 4 Implementation (Weeks 1-2)

**Overview:**
- **Objective:** Build production-ready dependency graph-based context builder
- **Timeline:** 10 days (2 weeks)
- **Deliverable:** Strategy 4 with 85% context accuracy, < 2s build time, zero AI costs
- **Success Criteria:**
  - Context accuracy ≥ 85% on test repository
  - Build time < 2 seconds for 500-file repos
  - Cache hit rate > 80%
  - Zero breaking changes to existing agent system

---

#### Week 1: Core Infrastructure & Dependency Graph (Part 1)

#### Day 1: Project Setup & Base Architecture

**Tasks:**
- [ ] Create module structure
  ```
  backend/agents/repository/
  ├── __init__.py
  ├── base.py              # Abstract base class
  ├── dependency_graph.py  # Strategy 4 implementation
  ├── enhanced.py          # Strategy 7 (Week 3)
  ├── factory.py           # Builder factory
  ├── models.py            # Data models
  └── utils/
      ├── parsers.py       # Import parsers
      ├── file_watcher.py  # File system watching
      └── token_counter.py # Token estimation
  ```

- [ ] Define data models
  ```python
  # backend/agents/repository/models.py

  @dataclass
  class RepositoryIndex:
      """Repository metadata"""
      name: str
      repo_path: str
      tech_stack: list[str]
      entry_points: list[str]
      structure: dict
      file_inventory: dict[str, FileInfo]
      created_at: datetime

  @dataclass
  class FileInfo:
      """File metadata"""
      path: str
      size: int
      language: str
      last_modified: datetime
      imports: list[str]
      exports: list[str]

  @dataclass
  class AgentContext:
      """Context provided to agent"""
      task: str
      overview: str
      files: list[tuple[str, str, float]]  # (path, content, score)
      signatures: list[tuple[str, str, float]]  # (path, signature, score)
      token_count: int
      max_tokens: int

  @dataclass
  class DependencyGraph:
      """Dependency graph structure"""
      graph: dict[str, list[str]]  # file -> dependencies
      reverse_graph: dict[str, list[str]]  # file -> dependents
      last_modified: dict[str, datetime]
  ```

- [ ] Create abstract base class
  ```python
  # backend/agents/repository/base.py

  from abc import ABC, abstractmethod

  class RepositoryContextBuilder(ABC):
      """Base class for repository context building"""

      @abstractmethod
      async def initialize(self) -> None:
          """Initialize the context builder"""
          pass

      @abstractmethod
      async def build_context(
          self,
          task: str,
          max_tokens: int = 8000
      ) -> AgentContext:
          """Build context for agent task"""
          pass

      @abstractmethod
      async def refresh(self) -> None:
          """Refresh repository state"""
          pass
  ```

- [ ] Set up configuration
  ```python
  # backend/config.py

  class RepositoryConfig:
      # Strategy selection
      REPOSITORY_STRATEGY: str = os.getenv(
          "REPOSITORY_STRATEGY",
          "dependency_graph"
      )

      # Performance tuning
      MAX_CONTEXT_TOKENS: int = 8000
      FILE_CACHE_SIZE: int = 100
      DEPENDENCY_GRAPH_CACHE_TTL: int = 3600  # 1 hour

      # File watching
      ENABLE_FILE_WATCHING: bool = True
      FILE_WATCH_DEBOUNCE_MS: int = 500

      # Ignored patterns (like .gitignore)
      IGNORED_PATTERNS: list[str] = [
          "node_modules",
          "__pycache__",
          "*.pyc",
          ".git",
          "venv",
          ".venv",
          "dist",
          "build"
      ]
  ```

**Deliverables:**
- Module structure created
- Data models defined
- Base class implemented
- Configuration system ready

**Success Criteria:**
- [ ] All imports work
- [ ] Models can be instantiated
- [ ] Config loads from environment
- [ ] Unit tests pass

---

#### Day 2: Repository Scanner

**Tasks:**
- [ ] Implement directory tree builder
  ```python
  # backend/agents/repository/dependency_graph.py

  class DependencyGraphContextBuilder(RepositoryContextBuilder):

      async def _scan_repository(self) -> RepositoryIndex:
          """Scan repository and build index"""
          return RepositoryIndex(
              name=self._get_repo_name(),
              repo_path=self.repo_path,
              tech_stack=await self._detect_tech_stack(),
              entry_points=await self._find_entry_points(),
              structure=await self._build_directory_tree(),
              file_inventory=await self._catalog_files(),
              created_at=datetime.utcnow()
          )

      async def _build_directory_tree(
          self,
          max_depth: int = 3
      ) -> dict:
          """
          Build directory tree structure

          Returns:
          {
              "backend/": {
                  "api/": ["agents.py", "conversations.py"],
                  "models/": ["agent.py", "conversation.py"],
                  "services/": ["orchestrator.py"]
              },
              "tests/": {...}
          }
          """
          tree = {}

          for root, dirs, files in os.walk(self.repo_path):
              # Filter out ignored patterns
              dirs[:] = [d for d in dirs if not self._is_ignored(d)]

              # Calculate depth
              rel_path = os.path.relpath(root, self.repo_path)
              depth = len(rel_path.split(os.sep))

              if depth > max_depth:
                  continue

              # Add to tree
              tree[rel_path] = {
                  "files": [f for f in files if not self._is_ignored(f)],
                  "dirs": dirs
              }

          return tree

      def _is_ignored(self, path: str) -> bool:
          """Check if path matches ignored patterns"""
          from pathspec import PathSpec

          spec = PathSpec.from_lines('gitwildmatch', config.IGNORED_PATTERNS)
          return spec.match_file(path)
  ```

- [ ] Implement tech stack detection
  ```python
  async def _detect_tech_stack(self) -> list[str]:
      """Detect technology stack from files"""
      tech_stack = set()

      # Check for common files
      checks = {
          "requirements.txt": "Python",
          "Pipfile": "Python",
          "setup.py": "Python",
          "package.json": "JavaScript/Node.js",
          "Cargo.toml": "Rust",
          "go.mod": "Go",
          "pom.xml": "Java/Maven",
          "build.gradle": "Java/Gradle",
          "Gemfile": "Ruby",
          "composer.json": "PHP"
      }

      for file, tech in checks.items():
          if os.path.exists(os.path.join(self.repo_path, file)):
              tech_stack.add(tech)

      # Check for frameworks
      if os.path.exists(os.path.join(self.repo_path, "package.json")):
          pkg = json.load(open(os.path.join(self.repo_path, "package.json")))
          deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

          if "react" in deps:
              tech_stack.add("React")
          if "vue" in deps:
              tech_stack.add("Vue")
          if "next" in deps:
              tech_stack.add("Next.js")

      return list(tech_stack)
  ```

- [ ] Implement entry point finder
  ```python
  async def _find_entry_points(self) -> list[str]:
      """Find main entry points"""
      entry_points = []

      # Common entry point files
      candidates = [
          "main.py",
          "app.py",
          "__main__.py",
          "index.js",
          "index.ts",
          "server.js",
          "main.go",
          "src/main.rs"
      ]

      for candidate in candidates:
          full_path = os.path.join(self.repo_path, candidate)
          if os.path.exists(full_path):
              entry_points.append(candidate)

      # Find files with if __name__ == "__main__"
      for root, _, files in os.walk(self.repo_path):
          for file in files:
              if file.endswith(".py"):
                  full_path = os.path.join(root, file)
                  with open(full_path, 'r') as f:
                      content = f.read()
                      if '__name__ == "__main__"' in content:
                          rel_path = os.path.relpath(full_path, self.repo_path)
                          entry_points.append(rel_path)

      return entry_points
  ```

- [ ] Implement file cataloging
  ```python
  async def _catalog_files(self) -> dict[str, FileInfo]:
      """Catalog all source files"""
      inventory = {}

      # Extensions to include
      source_extensions = {
          ".py", ".js", ".ts", ".tsx", ".jsx",
          ".go", ".rs", ".java", ".cpp", ".c",
          ".rb", ".php", ".cs", ".swift"
      }

      for root, _, files in os.walk(self.repo_path):
          for file in files:
              ext = os.path.splitext(file)[1]
              if ext not in source_extensions:
                  continue

              full_path = os.path.join(root, file)
              rel_path = os.path.relpath(full_path, self.repo_path)

              if self._is_ignored(rel_path):
                  continue

              stat = os.stat(full_path)

              inventory[rel_path] = FileInfo(
                  path=rel_path,
                  size=stat.st_size,
                  language=self._detect_language(ext),
                  last_modified=datetime.fromtimestamp(stat.st_mtime),
                  imports=[],  # Will be filled by dependency graph
                  exports=[]   # Will be filled by dependency graph
              )

      return inventory
  ```

**Deliverables:**
- Repository scanner implemented
- Directory tree builder working
- Tech stack detection functional
- Entry point finder working
- File cataloger complete

**Success Criteria:**
- [ ] Scans agent-squad repository in < 2 seconds
- [ ] Correctly identifies Python + FastAPI + React
- [ ] Finds main.py and index.tsx as entry points
- [ ] Catalogs 100+ source files
- [ ] Respects .gitignore patterns

---

#### Day 3: Import Parsers

**Tasks:**
- [ ] Implement Python import parser
  ```python
  # backend/agents/repository/utils/parsers.py

  import ast
  from typing import List

  class PythonImportParser:
      """Parse Python imports using AST"""

      @staticmethod
      async def parse_imports(file_path: str) -> List[str]:
          """
          Extract imports from Python file

          Returns: List of imported module paths
          """
          imports = []

          try:
              with open(file_path, 'r') as f:
                  tree = ast.parse(f.read(), filename=file_path)

              for node in ast.walk(tree):
                  if isinstance(node, ast.Import):
                      for alias in node.names:
                          imports.append(alias.name)

                  elif isinstance(node, ast.ImportFrom):
                      if node.module:
                          imports.append(node.module)

              return imports

          except Exception as e:
              logger.warning(f"Failed to parse {file_path}: {e}")
              return []

      @staticmethod
      def resolve_import_path(
          import_name: str,
          current_file: str,
          repo_path: str
      ) -> str:
          """
          Resolve import to actual file path

          Example:
          - Import: "backend.models.agent"
          - Resolves to: "backend/models/agent.py"
          """
          # Handle relative imports
          if import_name.startswith("."):
              current_dir = os.path.dirname(current_file)
              # ... handle relative path resolution

          # Handle absolute imports
          parts = import_name.split(".")
          possible_paths = [
              os.path.join(repo_path, *parts) + ".py",
              os.path.join(repo_path, *parts, "__init__.py")
          ]

          for path in possible_paths:
              if os.path.exists(path):
                  return os.path.relpath(path, repo_path)

          return None
  ```

- [ ] Implement JavaScript/TypeScript import parser
  ```python
  import re
  from typing import List

  class JavaScriptImportParser:
      """Parse JavaScript/TypeScript imports"""

      # Regex patterns for imports
      IMPORT_PATTERNS = [
          r'import\s+.*\s+from\s+[\'"](.+?)[\'"]',  # import X from 'Y'
          r'require\([\'"](.+?)[\'"]\)',             # require('Y')
          r'import\([\'"](.+?)[\'"]\)'               # import('Y')
      ]

      @staticmethod
      async def parse_imports(file_path: str) -> List[str]:
          """Extract imports from JS/TS file"""
          imports = []

          try:
              with open(file_path, 'r') as f:
                  content = f.read()

              for pattern in JavaScriptImportParser.IMPORT_PATTERNS:
                  matches = re.finditer(pattern, content)
                  for match in matches:
                      import_path = match.group(1)
                      imports.append(import_path)

              return imports

          except Exception as e:
              logger.warning(f"Failed to parse {file_path}: {e}")
              return []

      @staticmethod
      def resolve_import_path(
          import_name: str,
          current_file: str,
          repo_path: str
      ) -> str:
          """Resolve JS/TS import to file path"""

          # Handle relative imports
          if import_name.startswith("."):
              current_dir = os.path.dirname(
                  os.path.join(repo_path, current_file)
              )
              resolved = os.path.normpath(
                  os.path.join(current_dir, import_name)
              )
          else:
              # Assume node_modules (external) - skip
              return None

          # Try different extensions
          for ext in [".js", ".ts", ".tsx", ".jsx", "/index.js", "/index.ts"]:
              full_path = resolved + ext
              if os.path.exists(full_path):
                  return os.path.relpath(full_path, repo_path)

          return None
  ```

- [ ] Create unified parser interface
  ```python
  class ImportParser:
      """Unified interface for all parsers"""

      PARSERS = {
          ".py": PythonImportParser,
          ".js": JavaScriptImportParser,
          ".ts": JavaScriptImportParser,
          ".tsx": JavaScriptImportParser,
          ".jsx": JavaScriptImportParser
      }

      @staticmethod
      async def parse_file(file_path: str, repo_path: str) -> List[str]:
          """Parse imports from any supported file"""
          ext = os.path.splitext(file_path)[1]

          parser_class = ImportParser.PARSERS.get(ext)
          if not parser_class:
              return []

          parser = parser_class()
          imports = await parser.parse_imports(
              os.path.join(repo_path, file_path)
          )

          # Resolve to actual file paths
          resolved = []
          for imp in imports:
              path = parser.resolve_import_path(imp, file_path, repo_path)
              if path:
                  resolved.append(path)

          return resolved
  ```

**Deliverables:**
- Python import parser complete
- JavaScript/TypeScript import parser complete
- Import resolution working
- Unified parser interface ready

**Success Criteria:**
- [ ] Parses Python imports correctly (including relative)
- [ ] Parses JS/TS imports correctly
- [ ] Resolves imports to actual file paths
- [ ] Handles parse errors gracefully
- [ ] Unit tests pass for both parsers

---

#### Day 4: Dependency Graph Builder

**Tasks:**
- [ ] Implement dependency graph builder
  ```python
  # backend/agents/repository/dependency_graph.py

  class DependencyGraphBuilder:
      """Builds and maintains dependency graph"""

      def __init__(self):
          self.graph: dict[str, list[str]] = {}
          self.reverse_graph: dict[str, list[str]] = {}
          self.last_modified: dict[str, datetime] = {}

      async def build_graph(
          self,
          repo_path: str,
          file_inventory: dict[str, FileInfo]
      ) -> DependencyGraph:
          """
          Build complete dependency graph

          Time: ~5-10 seconds for medium repo
          """
          logger.info(f"Building dependency graph for {len(file_inventory)} files")

          # Parse imports for all files
          for file_path, file_info in file_inventory.items():
              imports = await ImportParser.parse_file(file_path, repo_path)

              self.graph[file_path] = imports
              file_info.imports = imports

              # Build reverse graph
              for imported_file in imports:
                  if imported_file not in self.reverse_graph:
                      self.reverse_graph[imported_file] = []
                  self.reverse_graph[imported_file].append(file_path)

              # Track last modified
              self.last_modified[file_path] = file_info.last_modified

          logger.info(
              f"Graph built: {len(self.graph)} nodes, "
              f"{sum(len(v) for v in self.graph.values())} edges"
          )

          return DependencyGraph(
              graph=self.graph,
              reverse_graph=self.reverse_graph,
              last_modified=self.last_modified
          )
  ```

- [ ] Implement graph traversal
  ```python
  def get_related_files(
      self,
      file_path: str,
      depth: int = 2
  ) -> set[str]:
      """
      Get all files related to this file within N hops

      Uses BFS to find files within depth hops
      """
      related = set()
      to_visit = [(file_path, 0)]
      visited = set()

      while to_visit:
          current, current_depth = to_visit.pop(0)

          if current in visited or current_depth > depth:
              continue

          visited.add(current)

          # Add dependencies
          for dep in self.graph.get(current, []):
              related.add(dep)
              if current_depth < depth:
                  to_visit.append((dep, current_depth + 1))

          # Add dependents
          for dependent in self.reverse_graph.get(current, []):
              related.add(dependent)
              if current_depth < depth:
                  to_visit.append((dependent, current_depth + 1))

      return related

  def get_distance(self, file1: str, file2: str) -> int:
      """Calculate shortest path distance between two files"""
      if file1 == file2:
          return 0

      # BFS to find shortest path
      queue = [(file1, 0)]
      visited = set()

      while queue:
          current, dist = queue.pop(0)

          if current in visited:
              continue
          visited.add(current)

          if current == file2:
              return dist

          # Check neighbors
          neighbors = (
              self.graph.get(current, []) +
              self.reverse_graph.get(current, [])
          )

          for neighbor in neighbors:
              if neighbor not in visited:
                  queue.append((neighbor, dist + 1))

      return float('inf')  # Not connected
  ```

- [ ] Implement graph updates
  ```python
  async def update_file_dependencies(
      self,
      file_path: str,
      new_imports: list[str]
  ) -> None:
      """Update graph when file's imports change"""

      # Get old imports
      old_imports = self.graph.get(file_path, [])

      # Update forward graph
      self.graph[file_path] = new_imports

      # Update reverse graph
      # Remove old edges
      for old_imp in old_imports:
          if old_imp in self.reverse_graph:
              if file_path in self.reverse_graph[old_imp]:
                  self.reverse_graph[old_imp].remove(file_path)

      # Add new edges
      for new_imp in new_imports:
          if new_imp not in self.reverse_graph:
              self.reverse_graph[new_imp] = []
          if file_path not in self.reverse_graph[new_imp]:
              self.reverse_graph[new_imp].append(file_path)

      logger.info(f"Updated dependencies for {file_path}")
  ```

**Deliverables:**
- Dependency graph builder complete
- Graph traversal algorithms working
- Graph update logic implemented
- Performance optimized

**Success Criteria:**
- [ ] Builds graph for agent-squad in < 10 seconds
- [ ] Correctly identifies all imports
- [ ] Graph traversal finds related files
- [ ] Distance calculation works
- [ ] Updates apply correctly

---

### Week 1 (Continued): Days 5-7 - Context Building

#### Day 5: Smart Context Builder (Part 1)

**Tasks:**
- [ ] Implement task parsing
  ```python
  # backend/agents/repository/dependency_graph.py

  @dataclass
  class TaskInfo:
      """Parsed task information"""
      keywords: list[str]
      file_types: list[str]
      intent: str  # "add", "fix", "refactor", "test", etc.
      mentioned_files: list[str]

  async def _parse_task(self, task: str) -> TaskInfo:
      """
      Extract structured information from task

      Example:
      Task: "Add authentication to the user profile page"
      Returns:
      - keywords: ["authentication", "user", "profile", "page"]
      - file_types: [".tsx", ".ts", ".py"]
      - intent: "add"
      - mentioned_files: []
      """
      # Extract keywords
      keywords = self._extract_keywords(task)

      # Detect intent
      intent = "modify"  # default
      if any(word in task.lower() for word in ["add", "create", "new"]):
          intent = "add"
      elif any(word in task.lower() for word in ["fix", "bug", "error"]):
          intent = "fix"
      elif any(word in task.lower() for word in ["refactor", "reorganize"]):
          intent = "refactor"
      elif any(word in task.lower() for word in ["test", "testing"]):
          intent = "test"

      # Detect file types based on keywords
      file_types = []
      if any(word in task.lower() for word in ["frontend", "ui", "page", "component"]):
          file_types.extend([".tsx", ".jsx", ".ts", ".js"])
      if any(word in task.lower() for word in ["backend", "api", "database", "model"]):
          file_types.extend([".py", ".go", ".java"])

      # Extract mentioned files (e.g., "in users.py")
      import re
      file_pattern = r'\b(\w+\.(py|js|ts|tsx|jsx|go|rs))\b'
      mentioned_files = re.findall(file_pattern, task.lower())

      return TaskInfo(
          keywords=keywords,
          file_types=file_types or [".py", ".js", ".ts"],  # default
          intent=intent,
          mentioned_files=[f[0] for f in mentioned_files]
      )

  def _extract_keywords(self, text: str) -> list[str]:
      """Extract meaningful keywords from text"""
      # Remove common words
      stop_words = {
          "the", "a", "an", "and", "or", "but", "in", "to",
          "for", "of", "on", "with", "at", "by", "from"
      }

      # Simple tokenization
      words = re.findall(r'\b\w+\b', text.lower())

      # Filter stop words and short words
      keywords = [
          w for w in words
          if w not in stop_words and len(w) > 2
      ]

      return keywords
  ```

- [ ] Implement file search strategies
  ```python
  async def _find_relevant_files(self, task: str) -> set[str]:
      """
      Find files relevant to task using multiple strategies
      """
      task_info = await self._parse_task(task)
      candidate_files = set()

      # Strategy A: Keyword search in file content
      keyword_files = await self._search_by_keywords(
          task_info.keywords,
          file_types=task_info.file_types
      )
      candidate_files.update(keyword_files)
      logger.info(f"Keyword search found {len(keyword_files)} files")

      # Strategy B: Filename match
      name_matches = await self._search_by_filename(task_info.keywords)
      candidate_files.update(name_matches)
      logger.info(f"Filename search found {len(name_matches)} files")

      # Strategy C: Mentioned files + dependencies
      if task_info.mentioned_files:
          for file in task_info.mentioned_files:
              # Find actual file path
              actual_path = self._find_file_by_name(file)
              if actual_path:
                  candidate_files.add(actual_path)
                  # Add dependencies
                  related = self.dep_graph.get_related_files(
                      actual_path,
                      depth=2
                  )
                  candidate_files.update(related)

      # Strategy D: Recently modified files
      if any(word in task_info.intent for word in ["recent", "latest", "new"]):
          recent = await self._get_recent_files(hours=24)
          candidate_files.update(recent)

      # Strategy E: Test files (if fixing bugs or testing)
      if task_info.intent in ["fix", "test"]:
          test_files = await self._find_test_files(candidate_files)
          candidate_files.update(test_files)

      logger.info(f"Total candidate files: {len(candidate_files)}")
      return candidate_files

  async def _search_by_keywords(
      self,
      keywords: list[str],
      file_types: list[str]
  ) -> set[str]:
      """Search for keywords in file content"""
      matching_files = set()

      for file_path, file_info in self.repo_index.file_inventory.items():
          # Check file type
          if not any(file_path.endswith(ft) for ft in file_types):
              continue

          # Read file content
          full_path = os.path.join(self.repo_path, file_path)
          try:
              with open(full_path, 'r') as f:
                  content = f.read().lower()

              # Check if any keyword appears
              if any(kw in content for kw in keywords):
                  matching_files.add(file_path)

          except Exception as e:
              logger.warning(f"Failed to read {file_path}: {e}")

      return matching_files
  ```

**Deliverables:**
- Task parsing implemented
- Keyword extraction working
- Multiple file search strategies implemented
- Intent detection functional

**Success Criteria:**
- [ ] Correctly parses task intent
- [ ] Extracts relevant keywords
- [ ] Finds files matching keywords
- [ ] Identifies mentioned files
- [ ] Handles edge cases gracefully

---

#### Day 6: Smart Context Builder (Part 2)

**Tasks:**
- [ ] Implement file ranking algorithm
  ```python
  async def _rank_files(
      self,
      files: set[str],
      task_info: TaskInfo,
      focus_files: list[str] = None
  ) -> list[tuple[str, float]]:
      """
      Rank files by relevance to task

      Returns: List of (file_path, score) sorted by score descending
      """
      scores = {}

      for file_path in files:
          score = 0.0

          # Factor 1: Keyword matches (weight: 0.3)
          keyword_score = await self._score_keyword_matches(
              file_path,
              task_info.keywords
          )
          score += keyword_score * 0.3

          # Factor 2: Recency (weight: 0.2)
          recency_score = self._score_recency(file_path)
          score += recency_score * 0.2

          # Factor 3: Dependency distance (weight: 0.2)
          if focus_files:
              distance_score = self._score_dependency_distance(
                  file_path,
                  focus_files
              )
              score += distance_score * 0.2

          # Factor 4: File type match (weight: 0.1)
          if any(file_path.endswith(ft) for ft in task_info.file_types):
              score += 0.1

          # Factor 5: File size (weight: 0.1, prefer smaller)
          size_score = self._score_file_size(file_path)
          score += size_score * 0.1

          # Factor 6: Access history (weight: 0.1)
          if file_path in self.file_cache:
              score += 0.1

          scores[file_path] = score

      # Sort by score descending
      ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

      logger.info(
          f"Ranked {len(ranked)} files, "
          f"top score: {ranked[0][1]:.2f}, "
          f"median: {ranked[len(ranked)//2][1]:.2f}"
      )

      return ranked

  async def _score_keyword_matches(
      self,
      file_path: str,
      keywords: list[str]
  ) -> float:
      """Score based on keyword matches"""
      try:
          content = await self._load_file(file_path)
          content_lower = content.lower()

          matches = sum(
              1 for kw in keywords
              if kw in content_lower
          )

          return matches / len(keywords) if keywords else 0.0

      except Exception:
          return 0.0

  def _score_recency(self, file_path: str) -> float:
      """Score based on how recently file was modified"""
      last_mod = self.dep_graph.last_modified.get(file_path)
      if not last_mod:
          return 0.0

      hours_ago = (datetime.utcnow() - last_mod).total_seconds() / 3600

      # Decay over 1 week
      recency_score = max(0, 1 - (hours_ago / 168))
      return recency_score

  def _score_dependency_distance(
      self,
      file_path: str,
      focus_files: list[str]
  ) -> float:
      """Score based on distance from focus files"""
      if not focus_files:
          return 0.0

      min_distance = min(
          self.dep_graph.get_distance(file_path, focus)
          for focus in focus_files
      )

      # Closer = higher score
      distance_score = max(0, 1 - (min_distance / 5))
      return distance_score

  def _score_file_size(self, file_path: str) -> float:
      """Score based on file size (prefer smaller)"""
      file_info = self.repo_index.file_inventory.get(file_path)
      if not file_info:
          return 0.0

      # Prefer files < 10KB
      size_score = max(0, 1 - (file_info.size / 10000))
      return size_score
  ```

- [ ] Implement token estimation
  ```python
  # backend/agents/repository/utils/token_counter.py

  class TokenCounter:
      """Estimate token count for text"""

      # Rough estimates: 1 token ≈ 4 characters
      CHARS_PER_TOKEN = 4

      @staticmethod
      def estimate_tokens(text: str) -> int:
          """
          Estimate token count

          This is a rough estimate. For production, use tiktoken:
          https://github.com/openai/tiktoken
          """
          return len(text) // TokenCounter.CHARS_PER_TOKEN

      @staticmethod
      def estimate_tokens_precise(text: str, model: str = "gpt-4") -> int:
          """
          Precise token count using tiktoken

          Requires: pip install tiktoken
          """
          try:
              import tiktoken
              encoding = tiktoken.encoding_for_model(model)
              return len(encoding.encode(text))
          except ImportError:
              # Fallback to rough estimate
              return TokenCounter.estimate_tokens(text)
  ```

**Deliverables:**
- File ranking algorithm complete
- Multi-factor scoring implemented
- Token estimation working
- Performance optimized

**Success Criteria:**
- [ ] Rankings are reasonable (manual inspection)
- [ ] Most relevant files score highest
- [ ] Token estimation is accurate (±10%)
- [ ] Ranking completes in < 1 second

---

#### Day 7: Context Assembly

**Tasks:**
- [ ] Implement context building
  ```python
  async def build_context(
      self,
      task: str,
      max_tokens: int = 8000
  ) -> AgentContext:
      """
      Build optimal context for agent task

      Main entry point for Strategy 4
      """
      logger.info(f"Building context for task: {task}")
      start_time = time.time()

      # Step 1: Parse task
      task_info = await self._parse_task(task)

      # Step 2: Find relevant files
      candidate_files = await self._find_relevant_files(task)

      # Step 3: Rank files
      ranked_files = await self._rank_files(
          candidate_files,
          task_info
      )

      # Step 4: Assemble context
      context = AgentContext(
          task=task,
          overview="",
          files=[],
          signatures=[],
          token_count=0,
          max_tokens=max_tokens
      )

      # Add repository overview (always included)
      overview = await self._build_overview()
      context.overview = overview
      context.token_count += self._estimate_tokens(overview)

      # Load files until context full
      for file_path, relevance_score in ranked_files:
          # Check if file is cached
          if file_path in self.file_cache:
              file_content = self.file_cache[file_path]
          else:
              file_content = await self._load_file(file_path)
              self.file_cache[file_path] = file_content

          file_tokens = self._estimate_tokens(file_content)

          if context.token_count + file_tokens > max_tokens:
              # Context window full - add signature only
              signature = await self._get_file_signature(file_path)
              context.signatures.append((
                  file_path,
                  signature,
                  relevance_score
              ))
          else:
              # Add full file
              context.files.append((
                  file_path,
                  file_content,
                  relevance_score
              ))
              context.token_count += file_tokens

      elapsed = time.time() - start_time
      logger.info(
          f"Context built in {elapsed:.2f}s: "
          f"{len(context.files)} files, "
          f"{len(context.signatures)} signatures, "
          f"{context.token_count} tokens"
      )

      return context

  async def _build_overview(self) -> str:
      """
      Build repository overview

      Extension point: Strategy 7 will override this
      """
      return f"""Repository: {self.repo_index.name}
  Tech Stack: {', '.join(self.repo_index.tech_stack)}
  Entry Points: {', '.join(self.repo_index.entry_points)}

  Structure:
  {self._format_directory_tree(self.repo_index.structure)}
  """

  def _format_directory_tree(self, tree: dict, indent: int = 0) -> str:
      """Format directory tree for display"""
      lines = []
      for path, info in sorted(tree.items())[:20]:  # Limit to 20 entries
          prefix = "  " * indent
          if isinstance(info, dict) and "files" in info:
              file_count = len(info["files"])
              dir_count = len(info["dirs"])
              lines.append(
                  f"{prefix}📁 {path}/ "
                  f"({file_count} files, {dir_count} dirs)"
              )
          else:
              lines.append(f"{prefix}📄 {path}")
      return "\n".join(lines)
  ```

- [ ] Implement file signature extraction
  ```python
  async def _get_file_signature(self, file_path: str) -> str:
      """
      Get file signature (summary without implementation)

      For Python: class/function definitions + docstrings
      For JS/TS: function signatures + JSDoc
      """
      content = await self._load_file(file_path)

      if file_path.endswith('.py'):
          return await self._extract_python_signature(content)
      elif file_path.endswith(('.js', '.ts', '.tsx', '.jsx')):
          return await self._extract_js_signature(content)
      else:
          # Fallback: first 500 chars
          return content[:500] + "..."

  async def _extract_python_signature(self, content: str) -> str:
      """Extract Python class/function signatures"""
      try:
          tree = ast.parse(content)
          signatures = []

          for node in ast.walk(tree):
              if isinstance(node, ast.ClassDef):
                  # Class definition
                  sig = f"class {node.name}"
                  if node.bases:
                      bases = ", ".join(
                          getattr(b, 'id', str(b)) for b in node.bases
                      )
                      sig += f"({bases})"

                  # Add docstring if present
                  docstring = ast.get_docstring(node)
                  if docstring:
                      sig += f"\n    '''{docstring[:100]}...'''"

                  signatures.append(sig)

              elif isinstance(node, ast.FunctionDef):
                  # Function definition
                  args = [arg.arg for arg in node.args.args]
                  sig = f"def {node.name}({', '.join(args)})"

                  # Add return type if present
                  if node.returns:
                      sig += f" -> {ast.unparse(node.returns)}"

                  # Add docstring
                  docstring = ast.get_docstring(node)
                  if docstring:
                      sig += f"\n    '''{docstring[:100]}...'''"

                  signatures.append(sig)

          return "\n\n".join(signatures)

      except Exception as e:
          logger.warning(f"Failed to extract Python signature: {e}")
          return content[:500] + "..."

  async def _extract_js_signature(self, content: str) -> str:
      """Extract JavaScript function signatures"""
      # Simple regex-based extraction
      # For production, use a proper JS parser like esprima

      function_pattern = r'(export\s+)?(async\s+)?function\s+(\w+)\s*\([^)]*\)'
      class_pattern = r'(export\s+)?class\s+(\w+)(\s+extends\s+\w+)?'

      signatures = []

      # Find functions
      for match in re.finditer(function_pattern, content):
          signatures.append(match.group(0))

      # Find classes
      for match in re.finditer(class_pattern, content):
          signatures.append(match.group(0))

      return "\n\n".join(signatures) if signatures else content[:500] + "..."
  ```

**Deliverables:**
- Context assembly complete
- Overview generation working
- File signature extraction implemented
- Token management working

**Success Criteria:**
- [ ] Builds context in < 1 second
- [ ] Respects token limits
- [ ] Includes most relevant files
- [ ] Signatures are useful
- [ ] Overview is informative

---

### Week 2: File Watching & Integration (Days 8-10)

#### Day 8: File System Watcher

**Tasks:**
- [ ] Implement file watcher
  ```python
  # backend/agents/repository/utils/file_watcher.py

  from watchdog.observers import Observer
  from watchdog.events import FileSystemEventHandler
  import asyncio
  from typing import Callable

  class RepositoryFileWatcher:
      """Watch repository for file changes"""

      def __init__(
          self,
          repo_path: str,
          on_file_changed: Callable[[str], None]
      ):
          self.repo_path = repo_path
          self.on_file_changed = on_file_changed
          self.observer = None
          self.debounce_delay = 0.5  # 500ms debounce
          self.pending_changes = {}

      async def start(self):
          """Start watching repository"""
          handler = ChangeHandler(self._handle_change)

          self.observer = Observer()
          self.observer.schedule(
              handler,
              self.repo_path,
              recursive=True
          )
          self.observer.start()

          logger.info(f"File watcher started for {self.repo_path}")

      async def stop(self):
          """Stop watching"""
          if self.observer:
              self.observer.stop()
              self.observer.join()
              logger.info("File watcher stopped")

      async def _handle_change(self, file_path: str):
          """Handle file change with debouncing"""

          # Cancel previous pending change
          if file_path in self.pending_changes:
              self.pending_changes[file_path].cancel()

          # Schedule new change handler
          task = asyncio.create_task(
              self._process_change_debounced(file_path)
          )
          self.pending_changes[file_path] = task

      async def _process_change_debounced(self, file_path: str):
          """Process change after debounce delay"""
          await asyncio.sleep(self.debounce_delay)

          # Remove from pending
          if file_path in self.pending_changes:
              del self.pending_changes[file_path]

          # Process change
          await self.on_file_changed(file_path)

  class ChangeHandler(FileSystemEventHandler):
      """Handle file system events"""

      def __init__(self, callback: Callable):
          self.callback = callback

      def on_modified(self, event):
          if not event.is_directory:
              asyncio.create_task(self.callback(event.src_path))

      def on_created(self, event):
          if not event.is_directory:
              asyncio.create_task(self.callback(event.src_path))

      def on_deleted(self, event):
          if not event.is_directory:
              asyncio.create_task(self.callback(event.src_path))
  ```

- [ ] Integrate file watcher with context builder
  ```python
  # backend/agents/repository/dependency_graph.py

  async def _start_file_watcher(self):
      """Start watching repository for changes"""
      if not config.ENABLE_FILE_WATCHING:
          logger.info("File watching disabled")
          return

      self.file_watcher = RepositoryFileWatcher(
          repo_path=self.repo_path,
          on_file_changed=self._on_file_changed
      )

      await self.file_watcher.start()

  async def _on_file_changed(self, file_path: str):
      """Handle file change event"""
      rel_path = os.path.relpath(file_path, self.repo_path)

      # Ignore non-source files
      if self._is_ignored(rel_path):
          return

      logger.info(f"File changed: {rel_path}")

      # Update last modified timestamp
      self.dep_graph.last_modified[rel_path] = datetime.utcnow()

      # Re-parse imports
      new_imports = await ImportParser.parse_file(rel_path, self.repo_path)
      old_imports = self.dep_graph.graph.get(rel_path, [])

      if new_imports != old_imports:
          logger.info(
              f"Dependencies changed for {rel_path}: "
              f"{len(old_imports)} -> {len(new_imports)}"
          )
          await self.dep_graph.update_file_dependencies(rel_path, new_imports)

      # Invalidate file cache
      if rel_path in self.file_cache:
          del self.file_cache[rel_path]
          logger.debug(f"Cache invalidated for {rel_path}")
  ```

**Deliverables:**
- File system watcher implemented
- Debouncing working
- Integration with context builder complete
- Cache invalidation functional

**Success Criteria:**
- [ ] Detects file changes within 1 second
- [ ] Debounces rapid changes correctly
- [ ] Updates dependency graph on changes
- [ ] Invalidates cache appropriately
- [ ] Handles file deletions gracefully

---

#### Day 9: Factory Pattern & Configuration

**Tasks:**
- [ ] Create factory for context builders
  ```python
  # backend/agents/repository/factory.py

  from typing import Optional
  from .base import RepositoryContextBuilder
  from .dependency_graph import DependencyGraphContextBuilder
  from backend.config import RepositoryConfig

  class ContextBuilderFactory:
      """Factory for creating context builders"""

      _instances: dict[str, RepositoryContextBuilder] = {}

      @staticmethod
      def create(
          repo_path: str,
          strategy: Optional[str] = None
      ) -> RepositoryContextBuilder:
          """
          Create context builder for repository

          Args:
              repo_path: Path to repository
              strategy: Strategy name ("dependency_graph" or "enhanced")
                       If None, uses config.REPOSITORY_STRATEGY

          Returns:
              Context builder instance
          """
          # Use cached instance if available
          cache_key = f"{repo_path}:{strategy}"
          if cache_key in ContextBuilderFactory._instances:
              return ContextBuilderFactory._instances[cache_key]

          # Determine strategy
          strategy = strategy or RepositoryConfig.REPOSITORY_STRATEGY

          # Create builder
          if strategy == "dependency_graph":
              builder = DependencyGraphContextBuilder(repo_path)
          elif strategy == "enhanced":
              # Week 3: Import EnhancedContextBuilder
              from .enhanced import EnhancedContextBuilder
              builder = EnhancedContextBuilder(repo_path)
          else:
              raise ValueError(f"Unknown strategy: {strategy}")

          # Cache instance
          ContextBuilderFactory._instances[cache_key] = builder

          logger.info(f"Created {strategy} builder for {repo_path}")
          return builder

      @staticmethod
      async def initialize_all():
          """Initialize all cached builders"""
          for builder in ContextBuilderFactory._instances.values():
              await builder.initialize()

      @staticmethod
      def clear_cache():
          """Clear all cached builders"""
          ContextBuilderFactory._instances.clear()
  ```

- [ ] Add metrics tracking
  ```python
  # backend/agents/repository/models.py

  @dataclass
  class ContextMetrics:
      """Metrics for context building"""

      # Performance
      build_time_ms: float
      parse_time_ms: float
      rank_time_ms: float
      load_time_ms: float

      # Quality
      files_included: int
      files_excluded: int
      signatures_included: int
      token_count: int
      token_limit: int

      # Efficiency
      cache_hits: int
      cache_misses: int
      wasted_tokens: int  # Tokens in irrelevant files

      @property
      def token_utilization(self) -> float:
          """Percentage of token budget used"""
          return (self.token_count / self.token_limit) * 100

      @property
      def cache_hit_rate(self) -> float:
          """Percentage of cache hits"""
          total = self.cache_hits + self.cache_misses
          return (self.cache_hits / total * 100) if total > 0 else 0.0

  # Add to AgentContext
  @dataclass
  class AgentContext:
      """Context provided to agent"""
      task: str
      overview: str
      files: list[tuple[str, str, float]]
      signatures: list[tuple[str, str, float]]
      token_count: int
      max_tokens: int
      metrics: Optional[ContextMetrics] = None  # Add this
  ```

- [ ] Update context builder to track metrics
  ```python
  async def build_context(
      self,
      task: str,
      max_tokens: int = 8000
  ) -> AgentContext:
      """Build context with metrics tracking"""

      start_time = time.time()
      metrics = ContextMetrics(
          build_time_ms=0,
          parse_time_ms=0,
          rank_time_ms=0,
          load_time_ms=0,
          files_included=0,
          files_excluded=0,
          signatures_included=0,
          token_count=0,
          token_limit=max_tokens,
          cache_hits=0,
          cache_misses=0,
          wasted_tokens=0
      )

      # Parse task
      parse_start = time.time()
      task_info = await self._parse_task(task)
      metrics.parse_time_ms = (time.time() - parse_start) * 1000

      # Find and rank files
      candidate_files = await self._find_relevant_files(task)

      rank_start = time.time()
      ranked_files = await self._rank_files(candidate_files, task_info)
      metrics.rank_time_ms = (time.time() - rank_start) * 1000

      # Build context
      context = AgentContext(
          task=task,
          overview="",
          files=[],
          signatures=[],
          token_count=0,
          max_tokens=max_tokens,
          metrics=metrics
      )

      # ... rest of context building with metrics tracking

      # Track cache hits/misses
      for file_path, _ in ranked_files:
          if file_path in self.file_cache:
              metrics.cache_hits += 1
          else:
              metrics.cache_misses += 1

      metrics.build_time_ms = (time.time() - start_time) * 1000
      metrics.files_included = len(context.files)
      metrics.signatures_included = len(context.signatures)
      metrics.token_count = context.token_count

      return context
  ```

**Deliverables:**
- Factory pattern implemented
- Configuration system complete
- Metrics tracking integrated
- Caching working

**Success Criteria:**
- [ ] Factory creates correct builder based on config
- [ ] Builders are cached and reused
- [ ] Metrics are tracked accurately
- [ ] Configuration can be changed at runtime

---

#### Day 10: Testing & Documentation

**Tasks:**
- [ ] Write unit tests
  ```python
  # backend/tests/test_repository/test_dependency_graph.py

  import pytest
  from backend.agents.repository import DependencyGraphContextBuilder

  @pytest.fixture
  async def context_builder():
      """Create test context builder"""
      builder = DependencyGraphContextBuilder("/path/to/test/repo")
      await builder.initialize()
      return builder

  @pytest.mark.asyncio
  async def test_initial_scan(context_builder):
      """Test repository scanning"""
      assert context_builder.repo_index is not None
      assert len(context_builder.repo_index.tech_stack) > 0
      assert len(context_builder.repo_index.entry_points) > 0

  @pytest.mark.asyncio
  async def test_dependency_graph_build(context_builder):
      """Test dependency graph building"""
      assert context_builder.dep_graph is not None
      assert len(context_builder.dep_graph.graph) > 0

  @pytest.mark.asyncio
  async def test_context_building(context_builder):
      """Test context building"""
      context = await context_builder.build_context(
          task="Add user authentication",
          max_tokens=8000
      )

      assert len(context.files) > 0
      assert context.token_count < 8000
      assert context.overview != ""

  @pytest.mark.asyncio
  async def test_file_ranking(context_builder):
      """Test file ranking"""
      task_info = await context_builder._parse_task(
          "Fix bug in user authentication"
      )

      files = {"backend/api/auth.py", "backend/models/user.py", "tests/test_auth.py"}
      ranked = await context_builder._rank_files(files, task_info)

      assert len(ranked) == 3
      # Auth file should rank highest
      assert "auth.py" in ranked[0][0]

  @pytest.mark.asyncio
  async def test_file_watching(context_builder):
      """Test file change detection"""
      # Modify a file
      test_file = "backend/test.py"
      with open(test_file, 'w') as f:
          f.write("# test")

      # Wait for file watcher
      await asyncio.sleep(1)

      # Check that cache was invalidated
      assert test_file not in context_builder.file_cache
  ```

- [ ] Write integration tests
  ```python
  # backend/tests/test_repository/test_integration.py

  @pytest.mark.asyncio
  async def test_full_workflow():
      """Test complete workflow"""

      # 1. Create builder
      builder = DependencyGraphContextBuilder("/path/to/repo")

      # 2. Initialize
      await builder.initialize()

      # 3. Build context for task
      context = await builder.build_context(
          task="Add authentication to user profile"
      )

      # 4. Verify context
      assert len(context.files) > 0
      assert "user" in context.overview.lower() or \
             any("user" in f[0].lower() for f in context.files)

      # 5. Verify metrics
      assert context.metrics.build_time_ms < 2000  # < 2 seconds
      assert context.metrics.token_utilization > 50  # Using > 50% of tokens

  @pytest.mark.asyncio
  async def test_factory_pattern():
      """Test factory pattern"""

      builder1 = ContextBuilderFactory.create("/path/to/repo")
      builder2 = ContextBuilderFactory.create("/path/to/repo")

      # Should return same instance
      assert builder1 is builder2
  ```

- [ ] Write API documentation
  ```python
  # docs/api/repository_context_builder.md

  """
  # Repository Context Builder API

  ## Quick Start

  ```python
  from backend.agents.repository import ContextBuilderFactory

  # Create builder
  builder = ContextBuilderFactory.create("/path/to/repo")
  await builder.initialize()

  # Build context
  context = await builder.build_context(
      task="Add user authentication",
      max_tokens=8000
  )

  # Use context
  for file_path, content, score in context.files:
      print(f"{file_path} (score: {score:.2f})")
  ```

  ## Configuration

  Set via environment variables:

  - `REPOSITORY_STRATEGY`: "dependency_graph" or "enhanced"
  - `MAX_CONTEXT_TOKENS`: Maximum tokens (default: 8000)
  - `ENABLE_FILE_WATCHING`: Enable file watching (default: true)

  ## API Reference

  ### RepositoryContextBuilder

  Base class for all context builders.

  #### Methods

  - `initialize()`: Initialize the builder
  - `build_context(task, max_tokens)`: Build context for task
  - `refresh()`: Refresh repository state

  ### DependencyGraphContextBuilder

  Strategy 4 implementation using dependency graphs.

  ...
  """
  ```

**Deliverables:**
- Unit tests written (80%+ coverage)
- Integration tests written
- API documentation complete
- Performance benchmarks documented

**Success Criteria:**
- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Documentation is clear and complete
- [ ] Performance meets targets (< 2s context building)

---

### Week 2 Summary & Deployment

**End of Week 2 Deliverable: Strategy 4 Complete and Production-Ready**

**Checklist:**
- [x] Repository scanning implemented
- [x] Dependency graph building working
- [x] Import parsers for Python and JS/TS complete
- [x] File ranking algorithm implemented
- [x] Context building functional
- [x] File watching enabled
- [x] Factory pattern implemented
- [x] Configuration system complete
- [x] Metrics tracking integrated
- [x] Tests written and passing
- [x] Documentation complete

**Deployment Steps:**
1. Merge to main branch
2. Deploy to staging environment
3. Run integration tests
4. Monitor metrics for 24 hours
5. Deploy to production
6. Monitor performance and accuracy

**Success Metrics:**
- Context accuracy: Target 85%
- Context build time: < 2 seconds
- Token utilization: > 70%
- Cache hit rate: > 80% (after warmup)
- No errors or crashes

---

### 📅 Phase 2: Strategy 7 Implementation (Week 3)

**Overview:**
- **Objective:** Extend Strategy 4 with AI-powered folder summaries
- **Timeline:** 5 days (1 week)
- **Deliverable:** Strategy 7 with 90% context accuracy, -7% wasted tokens, lazy folder summarization
- **Success Criteria:**
  - Context accuracy ≥ 90% on test repository
  - Wasted tokens ≤ 8% (down from 15% in Strategy 4)
  - Warm cache build time ≤ 2 seconds (same as Strategy 4)
  - Cold cache build time ≤ 3 seconds (includes summary generation)
  - Zero breaking changes (Strategy 4 continues to work)
  - Backward compatible factory pattern

---

#### Week 3: Folder Summaries Implementation

#### Day 1: Folder Summarization

**Tasks:**
- [ ] Create EnhancedContextBuilder class
  ```python
  # backend/agents/repository/enhanced.py

  from .dependency_graph import DependencyGraphContextBuilder
  from cachetools import LRUCache
  from pathlib import Path

  class EnhancedContextBuilder(DependencyGraphContextBuilder):
      """
      Strategy 7: Dependency Graph + Folder Summaries

      Extends Strategy 4 with AI-powered folder summaries
      """

      def __init__(self, repo_path: str):
          super().__init__(repo_path)

          # Folder summary cache
          self.folder_summaries: dict[str, str] = {}
          self.summary_cache = LRUCache(maxsize=50)

          # Configuration
          self.enable_summaries = config.ENABLE_FOLDER_SUMMARIES
          self.max_folders_to_summarize = 5

      async def initialize(self):
          """Initialize enhanced context builder"""
          await super().initialize()

          logger.info(
              f"Enhanced context builder initialized "
              f"(summaries: {self.enable_summaries})"
          )
  ```

- [ ] Implement folder identification
  ```python
  async def _identify_relevant_folders(self, task: str) -> list[str]:
      """
      Identify folders relevant to task

      Returns: List of folder paths to summarize
      """
      # Parse task
      task_info = await self._parse_task(task)

      # Find files matching keywords
      matching_files = await self._find_files_by_keywords(
          task_info.keywords
      )

      # Extract parent folders
      folders = {}
      for file_path in matching_files:
          folder = os.path.dirname(file_path)
          if folder not in folders:
              folders[folder] = 0
          folders[folder] += 1

      # Sort by file count (most files = most relevant)
      sorted_folders = sorted(
          folders.items(),
          key=lambda x: x[1],
          reverse=True
      )

      # Return top N folders
      top_folders = [
          f[0] for f in sorted_folders[:self.max_folders_to_summarize]
      ]

      logger.info(f"Identified {len(top_folders)} relevant folders: {top_folders}")
      return top_folders
  ```

- [ ] Implement folder summarization
  ```python
  async def _summarize_folder(self, folder_path: str) -> str:
      """
      Generate AI summary for folder

      Returns: 200-500 token summary
      """
      # Check cache
      if folder_path in self.summary_cache:
          logger.debug(f"Cache hit for folder summary: {folder_path}")
          return self.summary_cache[folder_path]

      logger.info(f"Generating summary for folder: {folder_path}")

      # Get files in folder
      full_path = os.path.join(self.repo_path, folder_path)
      files = list(Path(full_path).glob("*.py"))[:10]

      if not files:
          return f"Empty or non-Python folder: {folder_path}"

      # Get file signatures (not full content)
      file_info = []
      for file in files:
          rel_path = os.path.relpath(file, self.repo_path)
          signature = await self._get_file_signature(rel_path)
          file_info.append(f"{file.name}:\n{signature}")

      # Build prompt
      prompt = f"""Summarize this code folder in 200-500 tokens.

  Folder: {folder_path}
  Files:
  {chr(10).join(file_info)}

  Include:
  1. What is the purpose of this folder?
  2. What are the key files and their roles?
  3. What functionality does it provide?
  4. How does it fit in the overall system?

  Be concise and technical."""

      # Call AI for summary
      summary = await self._call_ai_for_summary(prompt)

      # Cache it
      self.summary_cache[folder_path] = summary

      logger.info(f"Summary generated for {folder_path} ({len(summary)} chars)")
      return summary

  async def _call_ai_for_summary(self, prompt: str) -> str:
      """
      Call AI service to generate summary

      Uses configured LLM (Claude, GPT-4, etc.)
      """
      from anthropic import AsyncAnthropic

      client = AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)

      try:
          response = await client.messages.create(
              model="claude-3-5-sonnet-20241022",
              max_tokens=500,
              messages=[{
                  "role": "user",
                  "content": prompt
              }]
          )

          summary = response.content[0].text
          return summary

      except Exception as e:
          logger.error(f"AI summary generation failed: {e}")
          return f"Summary generation failed: {str(e)}"
  ```

**Deliverables:**
- EnhancedContextBuilder class created
- Folder identification implemented
- AI summarization working
- Caching functional

**Success Criteria:**
- [ ] Identifies correct folders for task
- [ ] Generates useful summaries (manual inspection)
- [ ] Summaries are 200-500 tokens
- [ ] Caching works (no duplicate AI calls)
- [ ] Handles errors gracefully

---

#### Day 2: Integration with Context Building

**Tasks:**
- [ ] Override _build_overview method
  ```python
  async def _build_overview(self) -> str:
      """
      Build overview with folder summaries

      Extension of Strategy 4's overview
      """
      # Start with base overview
      base_overview = await super()._build_overview()

      # Add folder summaries if available
      if self.folder_summaries:
          folder_section = "\n\n## Folder Details\n\n"

          for folder, summary in self.folder_summaries.items():
              folder_section += f"### 📁 {folder}\n{summary}\n\n"

          return base_overview + folder_section

      return base_overview
  ```

- [ ] Override build_context method
  ```python
  async def build_context(
      self,
      task: str,
      max_tokens: int = 8000
  ) -> AgentContext:
      """
      Build context with folder summaries

      Steps:
      1. Identify relevant folders
      2. Generate summaries (lazy)
      3. Call parent's build_context
      """
      if not self.enable_summaries:
          # Fallback to Strategy 4
          return await super().build_context(task, max_tokens)

      try:
          # Identify relevant folders
          relevant_folders = await self._identify_relevant_folders(task)

          # Generate summaries (only if not cached)
          for folder in relevant_folders:
              if folder not in self.folder_summaries:
                  summary = await self._summarize_folder(folder)
                  self.folder_summaries[folder] = summary

          # Use parent's build_context
          # (folder summaries will be included in overview)
          return await super().build_context(task, max_tokens)

      except Exception as e:
          logger.error(f"Enhanced context building failed: {e}")
          logger.info("Falling back to Strategy 4")

          # Graceful degradation
          return await super().build_context(task, max_tokens)
  ```

- [ ] Add metrics for summaries
  ```python
  @dataclass
  class ContextMetrics:
      # ... existing fields ...

      # Strategy 7 specific
      folders_summarized: int = 0
      summary_generation_time_ms: float = 0
      summary_cache_hits: int = 0
      summary_cache_misses: int = 0
      summary_tokens: int = 0
  ```

- [ ] Update metrics tracking
  ```python
  async def build_context(
      self,
      task: str,
      max_tokens: int = 8000
  ) -> AgentContext:
      """Build context with metrics"""

      start_time = time.time()

      # ... existing code ...

      # Track summary metrics
      if self.enable_summaries:
          summary_start = time.time()

          for folder in relevant_folders:
              if folder in self.summary_cache:
                  context.metrics.summary_cache_hits += 1
              else:
                  context.metrics.summary_cache_misses += 1

              summary = await self._summarize_folder(folder)
              context.metrics.summary_tokens += self._estimate_tokens(summary)

          context.metrics.summary_generation_time_ms = (
              (time.time() - summary_start) * 1000
          )
          context.metrics.folders_summarized = len(self.folder_summaries)

      return context
  ```

**Deliverables:**
- Override methods implemented
- Two-tier context working
- Metrics tracking added
- Graceful degradation functional

**Success Criteria:**
- [ ] Folder summaries appear in overview
- [ ] Parent's context building still works
- [ ] Metrics are tracked correctly
- [ ] Falls back gracefully on errors
- [ ] No breaking changes to Strategy 4

---

#### Day 3: Invalidation & Freshness

**Tasks:**
- [ ] Implement summary invalidation on file changes
  ```python
  async def _on_file_changed(self, file_path: str):
      """
      Handle file change (override parent)

      Invalidates folder summary when files change
      """
      # Call parent's handler
      await super()._on_file_changed(file_path)

      # Invalidate folder summary
      folder = os.path.dirname(file_path)

      if folder in self.folder_summaries:
          logger.info(f"Invalidating folder summary: {folder}")
          del self.folder_summaries[folder]

      if folder in self.summary_cache:
          del self.summary_cache[folder]
  ```

- [ ] Implement selective invalidation
  ```python
  def _should_invalidate_summary(
      self,
      folder: str,
      changed_file: str
  ) -> bool:
      """
      Determine if folder summary should be invalidated

      Only invalidate if significant change:
      - New file added
      - File deleted
      - Major refactoring (many lines changed)
      """
      # Check file significance
      file_info = self.repo_index.file_inventory.get(changed_file)
      if not file_info:
          return True  # New or deleted file

      # Check if it's a test file (don't invalidate for test changes)
      if "test" in changed_file.lower():
          return False

      # Check file size (invalidate if significant)
      if file_info.size > 1000:  # > 1KB
          return True

      return False
  ```

- [ ] Add summary refresh command
  ```python
  async def refresh_folder_summary(self, folder: str):
      """Manually refresh a folder summary"""
      logger.info(f"Manually refreshing folder summary: {folder}")

      # Remove from caches
      if folder in self.folder_summaries:
          del self.folder_summaries[folder]
      if folder in self.summary_cache:
          del self.summary_cache[folder]

      # Regenerate
      summary = await self._summarize_folder(folder)
      return summary

  async def refresh_all_summaries(self):
      """Refresh all cached summaries"""
      logger.info("Refreshing all folder summaries")

      folders = list(self.folder_summaries.keys())
      self.folder_summaries.clear()
      self.summary_cache.clear()

      for folder in folders:
          await self._summarize_folder(folder)
  ```

**Deliverables:**
- Summary invalidation implemented
- Selective invalidation working
- Manual refresh commands added
- Freshness maintained

**Success Criteria:**
- [ ] Summaries invalidated on file changes
- [ ] Selective invalidation reduces unnecessary AI calls
- [ ] Manual refresh works correctly
- [ ] No stale summaries in production

---

#### Day 4: Testing & Benchmarking

**Tasks:**
- [ ] Write tests for Strategy 7
  ```python
  # backend/tests/test_repository/test_enhanced.py

  @pytest.mark.asyncio
  async def test_enhanced_context_builder():
      """Test Strategy 7"""
      builder = EnhancedContextBuilder("/path/to/repo")
      await builder.initialize()

      context = await builder.build_context("Add user authentication")

      # Should have folder summaries
      assert "📁" in context.overview
      assert len(builder.folder_summaries) > 0

      # Should still have files (from Strategy 4)
      assert len(context.files) > 0

  @pytest.mark.asyncio
  async def test_folder_identification():
      """Test folder identification"""
      builder = EnhancedContextBuilder("/path/to/repo")
      await builder.initialize()

      folders = await builder._identify_relevant_folders(
          "Fix authentication bug"
      )

      # Should identify auth-related folders
      assert any("auth" in f.lower() for f in folders)

  @pytest.mark.asyncio
  async def test_summary_caching():
      """Test summary caching"""
      builder = EnhancedContextBuilder("/path/to/repo")
      await builder.initialize()

      folder = "backend/api"

      # First call - cache miss
      summary1 = await builder._summarize_folder(folder)
      assert builder.metrics.summary_cache_misses == 1

      # Second call - cache hit
      summary2 = await builder._summarize_folder(folder)
      assert summary1 == summary2
      assert builder.metrics.summary_cache_hits == 1

  @pytest.mark.asyncio
  async def test_graceful_degradation():
      """Test fallback to Strategy 4"""
      builder = EnhancedContextBuilder("/path/to/repo")
      builder.enable_summaries = False
      await builder.initialize()

      context = await builder.build_context("Add feature")

      # Should work like Strategy 4
      assert len(context.files) > 0
      assert "📁" not in context.overview
  ```

- [ ] Run performance benchmarks
  ```python
  # backend/tests/benchmarks/test_performance.py

  import pytest
  import time

  @pytest.mark.benchmark
  async def test_strategy_4_performance():
      """Benchmark Strategy 4"""
      builder = DependencyGraphContextBuilder("/path/to/large/repo")
      await builder.initialize()

      start = time.time()
      context = await builder.build_context("Add authentication")
      elapsed = time.time() - start

      print(f"Strategy 4: {elapsed:.2f}s")
      assert elapsed < 2.0  # Should be < 2 seconds

  @pytest.mark.benchmark
  async def test_strategy_7_performance():
      """Benchmark Strategy 7"""
      builder = EnhancedContextBuilder("/path/to/large/repo")
      await builder.initialize()

      # First call (cold cache)
      start = time.time()
      context1 = await builder.build_context("Add authentication")
      elapsed_cold = time.time() - start

      print(f"Strategy 7 (cold): {elapsed_cold:.2f}s")
      assert elapsed_cold < 5.0  # Allow extra time for summaries

      # Second call (warm cache)
      start = time.time()
      context2 = await builder.build_context("Add authentication")
      elapsed_warm = time.time() - start

      print(f"Strategy 7 (warm): {elapsed_warm:.2f}s")
      assert elapsed_warm < 2.0  # Should be as fast as Strategy 4
  ```

- [ ] Compare token usage
  ```python
  @pytest.mark.benchmark
  async def test_token_efficiency_comparison():
      """Compare token efficiency between strategies"""

      # Strategy 4
      builder4 = DependencyGraphContextBuilder("/path/to/repo")
      await builder4.initialize()
      context4 = await builder4.build_context("Add auth")

      # Strategy 7
      builder7 = EnhancedContextBuilder("/path/to/repo")
      await builder7.initialize()
      context7 = await builder7.build_context("Add auth")

      print(f"Strategy 4 tokens: {context4.token_count}")
      print(f"Strategy 7 tokens: {context7.token_count}")
      print(f"Strategy 4 wasted: {context4.metrics.wasted_tokens}")
      print(f"Strategy 7 wasted: {context7.metrics.wasted_tokens}")

      # Strategy 7 should waste fewer tokens
      assert context7.metrics.wasted_tokens < context4.metrics.wasted_tokens
  ```

**Deliverables:**
- Tests written for Strategy 7
- Performance benchmarks run
- Token efficiency compared
- Results documented

**Success Criteria:**
- [ ] All tests pass
- [ ] Strategy 7 (warm cache) performance ≈ Strategy 4
- [ ] Strategy 7 (cold cache) performance < 5 seconds
- [ ] Token efficiency improved by 7%
- [ ] Context accuracy improved to 90%

---

#### Day 5: Rollout & Monitoring

**Tasks:**
- [ ] Set up feature flag
  ```python
  # backend/config.py

  class RepositoryConfig:
      # ... existing config ...

      # Feature flags
      ENABLE_FOLDER_SUMMARIES: bool = os.getenv(
          "ENABLE_FOLDER_SUMMARIES",
          "false"
      ).lower() == "true"

      # Gradual rollout
      STRATEGY_7_ROLLOUT_PERCENTAGE: int = int(os.getenv(
          "STRATEGY_7_ROLLOUT_PERCENTAGE",
          "0"
      ))
  ```

- [ ] Implement gradual rollout
  ```python
  # backend/agents/repository/factory.py

  def create(
      repo_path: str,
      user_id: Optional[str] = None
  ) -> RepositoryContextBuilder:
      """Create builder with gradual rollout"""

      # Determine strategy based on rollout percentage
      strategy = RepositoryConfig.REPOSITORY_STRATEGY

      if strategy == "auto" and user_id:
          # Gradual rollout based on user ID
          rollout_pct = RepositoryConfig.STRATEGY_7_ROLLOUT_PERCENTAGE

          if rollout_pct > 0:
              # Hash user ID to get consistent assignment
              user_hash = hash(user_id) % 100

              if user_hash < rollout_pct:
                  strategy = "enhanced"
              else:
                  strategy = "dependency_graph"

      # Create builder
      if strategy == "enhanced":
          return EnhancedContextBuilder(repo_path)
      else:
          return DependencyGraphContextBuilder(repo_path)
  ```

- [ ] Add monitoring/logging
  ```python
  # backend/agents/repository/enhanced.py

  async def build_context(self, task: str, max_tokens: int = 8000) -> AgentContext:
      """Build context with monitoring"""

      logger.info(
          f"[Strategy 7] Building context for: {task[:50]}...",
          extra={
              "strategy": "enhanced",
              "repo_path": self.repo_path,
              "max_tokens": max_tokens
          }
      )

      try:
          context = await super().build_context(task, max_tokens)

          # Log metrics
          logger.info(
              f"[Strategy 7] Context built successfully",
              extra={
                  "files_included": len(context.files),
                  "folders_summarized": context.metrics.folders_summarized,
                  "token_count": context.token_count,
                  "build_time_ms": context.metrics.build_time_ms,
                  "summary_cache_hits": context.metrics.summary_cache_hits,
                  "summary_cache_misses": context.metrics.summary_cache_misses
              }
          )

          return context

      except Exception as e:
          logger.error(
              f"[Strategy 7] Context building failed: {e}",
              extra={
                  "strategy": "enhanced",
                  "error": str(e)
              }
          )
          raise
  ```

- [ ] Create monitoring dashboard queries
  ```python
  # docs/monitoring/strategy_7_metrics.md

  """
  # Strategy 7 Monitoring Queries

  ## Performance Comparison

  ```sql
  -- Average build time by strategy
  SELECT
      strategy,
      AVG(build_time_ms) as avg_build_time,
      PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY build_time_ms) as p95_build_time
  FROM context_metrics
  WHERE timestamp > NOW() - INTERVAL '1 day'
  GROUP BY strategy
  ```

  ## Token Efficiency

  ```sql
  -- Wasted tokens by strategy
  SELECT
      strategy,
      AVG(wasted_tokens) as avg_wasted,
      AVG(token_utilization) as avg_utilization
  FROM context_metrics
  WHERE timestamp > NOW() - INTERVAL '1 day'
  GROUP BY strategy
  ```

  ## Cache Performance

  ```sql
  -- Cache hit rates
  SELECT
      strategy,
      AVG(cache_hit_rate) as avg_cache_hits,
      AVG(summary_cache_hits::float / NULLIF(summary_cache_hits + summary_cache_misses, 0)) as summary_cache_rate
  FROM context_metrics
  WHERE timestamp > NOW() - INTERVAL '1 day'
  GROUP BY strategy
  ```
  """
  ```

- [ ] Deploy with gradual rollout
  ```bash
  # Day 5, Hour 1: 10% rollout
  export STRATEGY_7_ROLLOUT_PERCENTAGE=10
  # Deploy and monitor

  # Day 5, Hour 4: 25% rollout
  export STRATEGY_7_ROLLOUT_PERCENTAGE=25
  # Monitor for issues

  # Day 5, Hour 6: 50% rollout
  export STRATEGY_7_ROLLOUT_PERCENTAGE=50
  # Continue monitoring

  # Day 5, Hour 8: 100% rollout (if all looks good)
  export STRATEGY_7_ROLLOUT_PERCENTAGE=100
  # Full deployment
  ```

**Deliverables:**
- Feature flag implemented
- Gradual rollout working
- Monitoring dashboard set up
- Deployment plan executed

**Success Criteria:**
- [ ] Feature flag toggles strategies correctly
- [ ] Gradual rollout assigns users consistently
- [ ] Metrics are being logged
- [ ] Dashboard shows real-time data
- [ ] No errors in production

---

## 📊 Success Metrics & KPIs

### Strategy 4 (Week 2) Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Context Accuracy** | 85% | Manual review of 20 contexts |
| **Context Build Time** | < 2 seconds | P95 latency |
| **Token Utilization** | > 70% | Average across all contexts |
| **Cache Hit Rate** | > 80% | After warmup period |
| **Error Rate** | < 1% | Percentage of failed builds |
| **File Ranking Quality** | Top 3 files relevant | Manual inspection |

### Strategy 7 (Week 3) Success Criteria

| Metric | Target | Improvement |
|--------|--------|-------------|
| **Context Accuracy** | 90% | +5% vs Strategy 4 |
| **Wasted Tokens** | 8% | -7% vs Strategy 4 |
| **Build Time (Cold)** | < 5 seconds | First-time builds |
| **Build Time (Warm)** | < 2 seconds | Cached summaries |
| **Summary Quality** | "Useful" rating > 80% | User feedback |
| **Summary Cache Hit Rate** | > 90% | After initial generation |

### Comparison Metrics

```python
# Expected improvements from Strategy 4 → Strategy 7

EXPECTED_IMPROVEMENTS = {
    "context_accuracy": 0.05,      # +5%
    "wasted_tokens": -0.07,        # -7%
    "navigation_speed": -0.2,      # -0.2s faster
    "user_satisfaction": 0.15      # +15% based on surveys
}

ACCEPTABLE_TRADEOFFS = {
    "build_time_cold": 3.0,        # +3s on cold cache (one-time)
    "ai_cost_per_folder": 0.001,   # $0.001 per folder
    "complexity": 150              # +150 LOC
}
```

---

## 🚨 Risk Mitigation

### Technical Risks

#### Risk 1: Dependency Graph Parsing Errors

**Probability:** Medium
**Impact:** High (blocks context building)

**Mitigation:**
- Graceful error handling in parsers
- Skip unparseable files instead of failing
- Log parsing errors for investigation
- Fallback to file content search if graph unavailable

#### Risk 2: File Watcher Missing Changes

**Probability:** Low
**Impact:** Medium (stale cache)

**Mitigation:**
- Periodic full refresh (every 1 hour)
- TTL on cached items (1 hour)
- Manual refresh command
- Monitor last refresh timestamp

#### Risk 3: AI Summary Generation Fails

**Probability:** Medium
**Impact:** Low (graceful degradation)

**Mitigation:**
- Automatic fallback to Strategy 4
- Retry logic with exponential backoff
- Monitor AI service health
- Alert on high failure rate

#### Risk 4: Performance Regression

**Probability:** Low
**Impact:** High (poor UX)

**Mitigation:**
- Performance tests in CI/CD
- Alerts on P95 latency > 3 seconds
- Automatic rollback on performance degradation
- Load testing before full rollout

### Operational Risks

#### Risk 5: Increased AI Costs

**Probability:** Medium
**Impact:** Medium

**Mitigation:**
- Aggressive caching (90%+ hit rate target)
- Cost monitoring and alerts
- Rate limiting on summary generation
- Budget cap on AI spending

#### Risk 6: Strategy 7 Not Worth It

**Probability:** Low
**Impact:** Medium (wasted dev time)

**Mitigation:**
- Can keep Strategy 4 as default
- Only 1 week investment for Strategy 7
- Easy rollback via config
- A/B testing validates value

---

## 🔄 Rollback Plan

### Quick Rollback (< 5 minutes)

```bash
# Option 1: Environment variable
export REPOSITORY_STRATEGY="dependency_graph"

# Option 2: Feature flag
export ENABLE_FOLDER_SUMMARIES="false"

# Option 3: Rollout percentage
export STRATEGY_7_ROLLOUT_PERCENTAGE="0"

# Restart services
kubectl rollout restart deployment/agent-service
```

### Full Rollback (< 30 minutes)

```bash
# Revert to last known good version
git revert <commit-hash>
git push origin main

# Deploy previous version
kubectl apply -f k8s/agent-service-v1.yaml

# Monitor recovery
kubectl logs -f deployment/agent-service
```

### Gradual Rollback

If issues found during rollout:

```bash
# Reduce rollout percentage
export STRATEGY_7_ROLLOUT_PERCENTAGE="25"  # from 50%
# Monitor for 1 hour

export STRATEGY_7_ROLLOUT_PERCENTAGE="10"  # from 25%
# Monitor for 1 hour

export STRATEGY_7_ROLLOUT_PERCENTAGE="0"   # Complete rollback
```

---

## 📚 Documentation Checklist

### Week 2 (Strategy 4)
- [ ] API documentation
- [ ] Configuration guide
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] Performance tuning guide
- [ ] Architecture diagrams

### Week 3 (Strategy 7)
- [ ] Migration guide (Strategy 4 → 7)
- [ ] Feature flag documentation
- [ ] Monitoring dashboard guide
- [ ] Cost optimization guide
- [ ] Rollback procedures
- [ ] Comparison benchmarks

---

## 🎯 Post-Implementation

### After Strategy 4 Deployment

**Week 2, Day 11-14: Monitoring Period**
- Monitor performance metrics daily
- Collect user feedback
- Identify optimization opportunities
- Document lessons learned
- Prepare for Strategy 7 implementation

**Success Criteria for Starting Week 3:**
- [ ] Strategy 4 stable in production (no critical bugs)
- [ ] Performance meets targets
- [ ] Users report positive experience
- [ ] Team comfortable with codebase

### After Strategy 7 Deployment

**Week 3, Day 6-7: Validation Period**
- Compare Strategy 4 vs 7 metrics
- Analyze cost vs benefit
- Decide on default strategy
- Document final results
- Plan future optimizations

**Decision Matrix:**

| Scenario | Action |
|----------|--------|
| Strategy 7 better & cost acceptable | Make Strategy 7 default |
| Strategy 7 better but cost high | Keep Strategy 4 default, offer Strategy 7 as premium |
| Strategy 7 not significantly better | Keep Strategy 4 default, deprecate Strategy 7 |
| Strategy 7 worse | Rollback to Strategy 4 only |

---

### 📅 Phase 3: Strategy 8 Implementation (Weeks 4-5) [Optional]

**Overview:**
- **Objective:** Extend Strategy 7 with vector similarity search for semantic understanding
- **Timeline:** 5-7 days (1-1.5 weeks)
- **Deliverable:** Strategy 8 with 93% context accuracy, +7% file recall, +15% NL query performance
- **Success Criteria:**
  - Context accuracy ≥ 93% on test repository
  - File discovery recall ≥ 92% (up from 85% in Strategy 7)
  - Natural language query success rate ≥ 95%
  - Build time ≤ 1 second (including vector search)
  - Zero breaking changes (Strategies 4 & 7 continue to work)
  - Cost remains ~$0.41/month per repo

**Prerequisites:**
- [ ] Strategy 7 deployed and stable
- [ ] Pinecone account set up
- [ ] OpenAI API access (for embeddings)
- [ ] Decision made to proceed with vector search

---

#### Week 4: Vector Search Foundation

#### Day 1: Pinecone Integration & Vector Store Setup

**Tasks:**
- [ ] Create VectorStore abstraction layer
  ```python
  # backend/agents/repository/utils/vector_store.py

  from abc import ABC, abstractmethod
  from typing import List, Dict, Any
  import pinecone
  from openai import AsyncOpenAI

  class VectorStore(ABC):
      """Abstract base for vector storage backends"""

      @abstractmethod
      async def index_repository(
          self,
          repo_path: str,
          files: Dict[str, str]
      ) -> None:
          """Index all files in repository"""
          pass

      @abstractmethod
      async def search_similar(
          self,
          query: str,
          top_k: int = 15
      ) -> List[str]:
          """Find files similar to query"""
          pass

      @abstractmethod
      async def update_file(
          self,
          file_path: str,
          content: str
      ) -> None:
          """Update single file embedding"""
          pass

      @abstractmethod
      async def delete_file(self, file_path: str) -> None:
          """Remove file from index"""
          pass


  class PineconeVectorStore(VectorStore):
      """Pinecone implementation"""

      def __init__(
          self,
          api_key: str,
          environment: str,
          index_name: str = "agent-squad-repos"
      ):
          # Initialize Pinecone
          pinecone.init(api_key=api_key, environment=environment)

          # Create or connect to index
          if index_name not in pinecone.list_indexes():
              pinecone.create_index(
                  name=index_name,
                  dimension=1536,  # OpenAI ada-002 embedding size
                  metric="cosine"
              )

          self.index = pinecone.Index(index_name)
          self.openai = AsyncOpenAI()

      async def _get_embedding(self, text: str) -> List[float]:
          """Generate embedding using OpenAI"""
          response = await self.openai.embeddings.create(
              model="text-embedding-ada-002",
              input=text[:8000]  # Token limit
          )
          return response.data[0].embedding

      async def index_repository(
          self,
          repo_path: str,
          files: Dict[str, str]
      ) -> None:
          """Index all files with metadata"""
          vectors = []

          for file_path, content in files.items():
              # Generate embedding
              embedding = await self._get_embedding(content)

              # Create vector with metadata
              vectors.append({
                  "id": f"{repo_path}::{file_path}",
                  "values": embedding,
                  "metadata": {
                      "repo_path": repo_path,
                      "file_path": file_path,
                      "file_type": file_path.split('.')[-1],
                      "size": len(content)
                  }
              })

              # Batch upsert every 100 vectors
              if len(vectors) >= 100:
                  self.index.upsert(vectors=vectors)
                  vectors = []

          # Upsert remaining
          if vectors:
              self.index.upsert(vectors=vectors)

      async def search_similar(
          self,
          query: str,
          top_k: int = 15,
          namespace: str = None
      ) -> List[str]:
          """Find semantically similar files"""
          # Get query embedding
          query_embedding = await self._get_embedding(query)

          # Search Pinecone
          results = self.index.query(
              vector=query_embedding,
              top_k=top_k,
              include_metadata=True,
              namespace=namespace
          )

          # Extract file paths
          return [
              match["metadata"]["file_path"]
              for match in results["matches"]
          ]

      async def update_file(
          self,
          file_path: str,
          content: str,
          repo_path: str
      ) -> None:
          """Update single file's embedding"""
          embedding = await self._get_embedding(content)

          self.index.upsert(vectors=[{
              "id": f"{repo_path}::{file_path}",
              "values": embedding,
              "metadata": {
                  "repo_path": repo_path,
                  "file_path": file_path,
                  "file_type": file_path.split('.')[-1],
                  "size": len(content)
              }
          }])

      async def delete_file(
          self,
          file_path: str,
          repo_path: str
      ) -> None:
          """Remove file from index"""
          self.index.delete(ids=[f"{repo_path}::{file_path}"])
  ```

- [ ] Add Pinecone configuration to settings
  ```python
  # backend/config.py

  class Settings:
      # ... existing settings ...

      # Vector search settings
      PINECONE_API_KEY: str = ""
      PINECONE_ENVIRONMENT: str = "us-east-1-aws"
      PINECONE_INDEX_NAME: str = "agent-squad-repos"
      ENABLE_VECTOR_SEARCH: bool = False  # Feature flag
  ```

- [ ] Add dependencies to requirements.txt
  ```
  pinecone-client>=2.2.0
  openai>=1.0.0
  ```

**Validation:**
- [ ] Pinecone connection successful
- [ ] Can create test embeddings
- [ ] Can upsert and query test vectors

**Time:** 4-5 hours

---

#### Day 2: Repository Indexing System

**Tasks:**
- [ ] Create repository indexer
  ```python
  # backend/agents/repository/utils/indexer.py

  from pathlib import Path
  import asyncio
  from .vector_store import VectorStore

  class RepositoryIndexer:
      """Handles initial indexing and updates"""

      def __init__(self, vector_store: VectorStore):
          self.vector_store = vector_store

      async def index_repository(
          self,
          repo_path: str,
          file_list: List[str],
          batch_size: int = 20
      ) -> Dict[str, Any]:
          """
          Index entire repository

          Returns metrics about indexing process
          """
          files_to_index = {}
          skipped = []

          # Read files
          for file_path in file_list:
              full_path = Path(repo_path) / file_path

              # Skip large files (> 100KB)
              if full_path.stat().st_size > 100_000:
                  skipped.append(file_path)
                  continue

              try:
                  content = full_path.read_text()
                  files_to_index[file_path] = content
              except Exception as e:
                  skipped.append(file_path)

          # Index in batches
          start_time = time.time()
          await self.vector_store.index_repository(
              repo_path,
              files_to_index
          )
          duration = time.time() - start_time

          return {
              "indexed": len(files_to_index),
              "skipped": len(skipped),
              "duration_seconds": duration,
              "files_per_second": len(files_to_index) / duration
          }

      async def update_file(
          self,
          repo_path: str,
          file_path: str
      ) -> None:
          """Update single file after change"""
          full_path = Path(repo_path) / file_path
          content = full_path.read_text()

          await self.vector_store.update_file(
              file_path,
              content,
              repo_path
          )

      async def delete_file(
          self,
          repo_path: str,
          file_path: str
      ) -> None:
          """Remove file after deletion"""
          await self.vector_store.delete_file(file_path, repo_path)
  ```

- [ ] Add CLI command for indexing
  ```python
  # backend/cli/index_repository.py

  import asyncio
  import click
  from backend.agents.repository.utils.indexer import RepositoryIndexer
  from backend.agents.repository.utils.vector_store import PineconeVectorStore
  from backend.config import settings

  @click.command()
  @click.argument('repo_path')
  @click.option('--force', is_flag=True, help='Reindex all files')
  async def index_repo(repo_path: str, force: bool):
      """Index repository for vector search"""

      # Initialize vector store
      vector_store = PineconeVectorStore(
          api_key=settings.PINECONE_API_KEY,
          environment=settings.PINECONE_ENVIRONMENT
      )

      indexer = RepositoryIndexer(vector_store)

      # Get file list (reuse from Strategy 4)
      from backend.agents.repository.dependency_graph import (
          DependencyGraphContextBuilder
      )
      builder = DependencyGraphContextBuilder(repo_path)
      await builder.scan_repository()

      file_list = list(builder.index.file_inventory.keys())

      click.echo(f"Indexing {len(file_list)} files from {repo_path}...")

      # Index
      metrics = await indexer.index_repository(repo_path, file_list)

      click.echo(f"✅ Indexed {metrics['indexed']} files")
      click.echo(f"⏭️  Skipped {metrics['skipped']} files")
      click.echo(f"⏱️  Duration: {metrics['duration_seconds']:.1f}s")
      click.echo(f"📊 Speed: {metrics['files_per_second']:.1f} files/sec")
  ```

**Validation:**
- [ ] Can index test repository
- [ ] Embeddings stored in Pinecone
- [ ] Metadata accessible
- [ ] Indexing completes in < 5 minutes for 500 files

**Time:** 4-5 hours

---

#### Day 3: VectorEnhancedContextBuilder Implementation

**Tasks:**
- [ ] Create Strategy 8 implementation
  ```python
  # backend/agents/repository/vector_enhanced.py

  from .enhanced import EnhancedContextBuilder
  from .utils.vector_store import PineconeVectorStore
  from typing import Set, List

  class VectorEnhancedContextBuilder(EnhancedContextBuilder):
      """
      Strategy 8: Strategy 7 + Vector Similarity Search

      Extends Strategy 7 with semantic file discovery
      """

      def __init__(self, repo_path: str, vector_store: VectorStore):
          super().__init__(repo_path)
          self.vector_store = vector_store

      async def _find_relevant_files(
          self,
          task: str,
          max_files: int = 50
      ) -> Set[str]:
          """
          Find files using Strategy 7 + vector similarity

          Combines:
          1. Keyword matching (from Strategy 4)
          2. Dependency graph traversal (from Strategy 4)
          3. Folder summaries (from Strategy 7)
          4. Vector similarity (NEW)
          """
          # Get Strategy 7 results
          strategy_7_files = await super()._find_relevant_files(
              task,
              max_files
          )

          # Add vector search results
          semantic_files = await self._search_by_similarity(task, top_k=15)

          # Combine both approaches
          combined = strategy_7_files | set(semantic_files)

          # Re-rank combined results
          ranked_files = await self._rank_files(task, list(combined))

          return set(ranked_files[:max_files])

      async def _search_by_similarity(
          self,
          query: str,
          top_k: int = 15
      ) -> List[str]:
          """Search for semantically similar files"""
          try:
              similar_files = await self.vector_store.search_similar(
                  query=query,
                  top_k=top_k,
                  namespace=self.index.name  # Repo namespace
              )

              # Filter out files not in current inventory
              return [
                  f for f in similar_files
                  if f in self.index.file_inventory
              ]
          except Exception as e:
              # Graceful degradation - fall back to Strategy 7
              logger.warning(f"Vector search failed: {e}")
              return []

      async def _rank_files(
          self,
          task: str,
          files: List[str]
      ) -> List[str]:
          """
          Enhanced ranking with vector similarity scores

          Combines:
          - Strategy 4 ranking (keyword, dependency, recency, size)
          - Strategy 7 ranking (folder relevance)
          - Vector similarity score (NEW)
          """
          scores = {}

          # Get base scores from Strategy 7
          base_scores = await super()._rank_files(task, files)
          for i, file_path in enumerate(base_scores):
              scores[file_path] = 100 - i  # Higher is better

          # Add vector similarity boost
          semantic_results = await self.vector_store.search_similar(
              query=task,
              top_k=50
          )

          for i, file_path in enumerate(semantic_results):
              if file_path in scores:
                  # Boost score based on vector rank
                  boost = (50 - i) * 0.5  # Up to +25 points
                  scores[file_path] += boost

          # Sort by combined score
          ranked = sorted(
              scores.items(),
              key=lambda x: x[1],
              reverse=True
          )

          return [file_path for file_path, _ in ranked]

      async def on_file_changed(self, file_path: str) -> None:
          """Handle file change - update both graph and vector index"""
          # Update Strategy 7
          await super().on_file_changed(file_path)

          # Update vector index
          try:
              await self.vector_store.update_file(
                  file_path,
                  Path(self.repo_path) / file_path).read_text(),
                  self.index.name
              )
          except Exception as e:
              logger.warning(f"Failed to update vector index: {e}")

      async def on_file_deleted(self, file_path: str) -> None:
          """Handle file deletion - remove from graph and vector index"""
          # Update Strategy 7
          await super().on_file_deleted(file_path)

          # Remove from vector index
          try:
              await self.vector_store.delete_file(
                  file_path,
                  self.index.name
              )
          except Exception as e:
              logger.warning(f"Failed to delete from vector index: {e}")
  ```

**Validation:**
- [ ] VectorEnhancedContextBuilder extends EnhancedContextBuilder correctly
- [ ] Combines results from multiple sources
- [ ] Graceful degradation if vector search fails
- [ ] File watching updates vector index

**Time:** 5-6 hours

---

#### Day 4: Factory Pattern & Feature Flag

**Tasks:**
- [ ] Update factory to support Strategy 8
  ```python
  # backend/agents/repository/factory.py

  def create_context_builder(
      repo_path: str,
      strategy: str = "auto"
  ) -> BaseContextBuilder:
      """
      Factory for creating context builders

      Args:
          repo_path: Path to repository
          strategy: "dependency_graph", "enhanced", "vector", or "auto"

      Returns:
          Appropriate context builder instance
      """
      if strategy == "auto":
          # Auto-detect best strategy
          if settings.ENABLE_VECTOR_SEARCH and settings.PINECONE_API_KEY:
              strategy = "vector"
          elif settings.ENABLE_FOLDER_SUMMARIES:
              strategy = "enhanced"
          else:
              strategy = "dependency_graph"

      if strategy == "vector":
          # Strategy 8
          from .vector_enhanced import VectorEnhancedContextBuilder
          from .utils.vector_store import PineconeVectorStore

          vector_store = PineconeVectorStore(
              api_key=settings.PINECONE_API_KEY,
              environment=settings.PINECONE_ENVIRONMENT
          )

          return VectorEnhancedContextBuilder(repo_path, vector_store)

      elif strategy == "enhanced":
          # Strategy 7
          from .enhanced import EnhancedContextBuilder
          return EnhancedContextBuilder(repo_path)

      elif strategy == "dependency_graph":
          # Strategy 4
          from .dependency_graph import DependencyGraphContextBuilder
          return DependencyGraphContextBuilder(repo_path)

      else:
          raise ValueError(f"Unknown strategy: {strategy}")
  ```

- [ ] Add feature flag configuration
  ```python
  # backend/config.py

  class Settings:
      # Strategy selection
      DEFAULT_CONTEXT_STRATEGY: str = "auto"  # auto, dependency_graph, enhanced, vector

      # Feature flags
      ENABLE_FOLDER_SUMMARIES: bool = True
      ENABLE_VECTOR_SEARCH: bool = False  # Gradual rollout

      # Vector search A/B testing
      VECTOR_SEARCH_ROLLOUT_PERCENTAGE: int = 0  # 0-100
  ```

- [ ] Implement A/B testing
  ```python
  # backend/agents/repository/factory.py

  import hashlib

  def should_use_vector_search(user_id: str) -> bool:
      """
      Determine if user should get vector search (A/B test)

      Uses consistent hashing for stable assignment
      """
      if not settings.ENABLE_VECTOR_SEARCH:
          return False

      if settings.VECTOR_SEARCH_ROLLOUT_PERCENTAGE >= 100:
          return True

      # Hash user_id to get deterministic bucket (0-99)
      hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
      bucket = hash_val % 100

      return bucket < settings.VECTOR_SEARCH_ROLLOUT_PERCENTAGE
  ```

**Validation:**
- [ ] Factory creates correct builder based on config
- [ ] Feature flags work correctly
- [ ] A/B testing assigns users consistently
- [ ] Can toggle strategies without code changes

**Time:** 3-4 hours

---

#### Day 5: Testing & Benchmarking

**Tasks:**
- [ ] Create comprehensive test suite
  ```python
  # backend/tests/test_vector_enhanced.py

  import pytest
  from backend.agents.repository.vector_enhanced import (
      VectorEnhancedContextBuilder
  )

  @pytest.mark.asyncio
  async def test_vector_search_integration():
      """Test vector search returns relevant files"""
      builder = VectorEnhancedContextBuilder(
          repo_path="./test_repo",
          vector_store=mock_vector_store
      )

      await builder.scan_repository()
      context = await builder.build_context(
          "Add user authentication with JWT tokens"
      )

      # Should find auth-related files via semantic search
      file_paths = [f.path for f in context.files]
      assert any("auth" in f.lower() for f in file_paths)
      assert any("token" in f.lower() or "jwt" in f.lower() for f in file_paths)

  @pytest.mark.asyncio
  async def test_graceful_degradation():
      """Test fallback when vector search fails"""
      # Mock vector store that raises exception
      failing_store = Mock(side_effect=Exception("Connection failed"))

      builder = VectorEnhancedContextBuilder(
          repo_path="./test_repo",
          vector_store=failing_store
      )

      # Should still work (falls back to Strategy 7)
      context = await builder.build_context("Fix login bug")
      assert len(context.files) > 0

  @pytest.mark.asyncio
  async def test_file_update_updates_vector_index():
      """Test that file changes update vector index"""
      builder = VectorEnhancedContextBuilder(
          repo_path="./test_repo",
          vector_store=mock_vector_store
      )

      # Modify file
      await builder.on_file_changed("src/auth.py")

      # Verify vector store was updated
      mock_vector_store.update_file.assert_called_once()
  ```

- [ ] Run benchmark comparison (Strategy 7 vs 8)
  ```python
  # backend/tests/benchmark_strategies.py

  async def benchmark_strategies():
      """Compare Strategy 7 vs Strategy 8 performance"""

      test_queries = [
          "Add user authentication",
          "Fix payment processing bug",
          "Implement email notifications",
          "Add analytics dashboard",
          "Optimize database queries"
      ]

      results = {
          "strategy_7": {"accuracy": [], "time": [], "recall": []},
          "strategy_8": {"accuracy": [], "time": [], "recall": []}
      }

      for query in test_queries:
          # Strategy 7
          start = time.time()
          s7_context = await strategy_7_builder.build_context(query)
          s7_time = time.time() - start

          # Strategy 8
          start = time.time()
          s8_context = await strategy_8_builder.build_context(query)
          s8_time = time.time() - start

          # Measure accuracy (requires ground truth)
          s7_accuracy = calculate_accuracy(s7_context, ground_truth[query])
          s8_accuracy = calculate_accuracy(s8_context, ground_truth[query])

          # Measure recall
          s7_recall = calculate_recall(s7_context, ground_truth[query])
          s8_recall = calculate_recall(s8_context, ground_truth[query])

          results["strategy_7"]["accuracy"].append(s7_accuracy)
          results["strategy_7"]["time"].append(s7_time)
          results["strategy_7"]["recall"].append(s7_recall)

          results["strategy_8"]["accuracy"].append(s8_accuracy)
          results["strategy_8"]["time"].append(s8_time)
          results["strategy_8"]["recall"].append(s8_recall)

      print_comparison(results)
  ```

- [ ] Document performance results
  ```markdown
  # Strategy 8 Benchmark Results

  ## Test Repository
  - Name: agent-squad
  - Files: 487
  - Languages: Python, TypeScript
  - Size: 12.3 MB

  ## Results (Average of 20 queries)

  | Metric | Strategy 7 | Strategy 8 | Change |
  |--------|-----------|-----------|--------|
  | Context Accuracy | 89.2% | 92.8% | +3.6% ⭐ |
  | File Recall | 84.5% | 91.3% | +6.8% ⭐⭐ |
  | Natural Language Queries | 78% | 94% | +16% ⭐⭐⭐ |
  | Build Time (cold) | 0.52s | 0.73s | +0.21s |
  | Build Time (warm) | 0.48s | 0.69s | +0.21s |
  | Wasted Tokens | 8.2% | 6.1% | -2.1% ⭐ |

  ## Conclusion
  Strategy 8 shows significant improvements in accuracy and recall, especially for natural language queries. The +0.2s latency is acceptable for the quality gains.
  ```

**Validation:**
- [ ] All tests pass
- [ ] Strategy 8 outperforms Strategy 7 on benchmarks
- [ ] Latency increase acceptable (< 300ms)
- [ ] No regressions vs Strategy 7

**Time:** 6-7 hours

---

#### Week 5: Production Deployment (Days 1-2)

#### Day 1: Monitoring & Metrics

**Tasks:**
- [ ] Add vector search metrics
  ```python
  # backend/agents/repository/vector_enhanced.py

  async def build_context(self, task: str) -> AgentContext:
      """Build context with vector search metrics"""
      start_time = time.time()

      # Track metrics
      metrics = {
          "strategy_7_files": 0,
          "vector_search_files": 0,
          "combined_files": 0,
          "vector_search_time": 0,
          "total_time": 0
      }

      # Get Strategy 7 results
      s7_start = time.time()
      strategy_7_files = await super()._find_relevant_files(task)
      metrics["strategy_7_files"] = len(strategy_7_files)

      # Get vector search results
      vs_start = time.time()
      vector_files = await self._search_by_similarity(task, top_k=15)
      metrics["vector_search_files"] = len(vector_files)
      metrics["vector_search_time"] = time.time() - vs_start

      # Combine
      combined = strategy_7_files | set(vector_files)
      metrics["combined_files"] = len(combined)
      metrics["total_time"] = time.time() - start_time

      # Log metrics
      logger.info("vector_search_metrics", extra=metrics)

      # Continue with context building...
      return context
  ```

- [ ] Create Grafana dashboard for Strategy 8
  - Vector search hit rate
  - Avg vector search latency
  - Files from vector vs dependency graph
  - Context accuracy by strategy

**Time:** 3-4 hours

---

#### Day 2: Gradual Rollout & Validation

**Tasks:**
- [ ] Deploy with vector search disabled
  ```python
  ENABLE_VECTOR_SEARCH = False
  ```

- [ ] Index production repositories
  ```bash
  for repo in prod_repos:
      python -m backend.cli.index_repository $repo
  ```

- [ ] Enable for 5% of users
  ```python
  ENABLE_VECTOR_SEARCH = True
  VECTOR_SEARCH_ROLLOUT_PERCENTAGE = 5
  ```

- [ ] Monitor metrics for 24 hours
  - Check error rates
  - Compare accuracy metrics
  - Verify costs align with projections

- [ ] Gradual increase
  - Day 3: 10%
  - Day 4: 25%
  - Day 5: 50%
  - Day 6-7: 100% if metrics good

**Validation:**
- [ ] No increase in error rates
- [ ] Context accuracy improved
- [ ] Latency increase acceptable
- [ ] Costs within budget
- [ ] User feedback positive

**Time:** 2-3 hours setup + ongoing monitoring

---

### After Strategy 8 Deployment

**Weeks 5-6: Optimization Period**
- Monitor vector search performance
- Collect user feedback on accuracy improvements
- Analyze cost vs benefit
- Tune vector search parameters (top_k, thresholds)
- Document final results

**Success Criteria for Strategy 8:**
- [ ] Strategy 8 stable in production (no critical bugs)
- [ ] Context accuracy ≥ 93%
- [ ] File recall ≥ 92%
- [ ] Natural language query success ≥ 95%
- [ ] Latency < 1 second
- [ ] Costs within budget (~$0.41/month per repo)
- [ ] Users report improved experience

**Decision Matrix:**

| Scenario | Action |
|----------|--------|
| Strategy 8 significantly better & costs acceptable | Make Strategy 8 default |
| Strategy 8 better for some use cases | Offer Strategy 8 as option (feature flag) |
| Strategy 8 not significantly better | Keep Strategy 7 default, deprecate Strategy 8 |
| Strategy 8 worse or too expensive | Rollback to Strategy 7 only |

---

## 🏁 Conclusion

This incremental implementation plan provides:

✅ **Fast Time to Value** - Working system in 2 weeks (Phase 1)
✅ **Low Risk** - Each phase tested independently with clear rollback options
✅ **Zero Breaking Changes** - Each strategy extends the previous one via inheritance
✅ **Easy Rollback** - Can stop at any phase (Strategy 4, 7, or 8)
✅ **Data-Driven** - Comprehensive metrics inform decisions at each phase
✅ **Production-Ready** - Full testing, monitoring, and feature flags
✅ **Cost-Effective** - Start at $0 (Strategy 4), scale as needed
✅ **Flexible** - A/B testing and gradual rollout capabilities

**Implementation Timeline:**

| Phase | Duration | Deliverable | Context Accuracy | Cost |
|-------|----------|-------------|------------------|------|
| **Phase 1** | 2 weeks | Strategy 4 (Dependency Graph) | 85% | $0 |
| **Phase 2** | 1 week | Strategy 7 (+ Folder Summaries) | 90% | ~$0.41/month per repo |
| **Phase 3** | 1-1.5 weeks | Strategy 8 (+ Vector Search) | 93% | ~$0.41/month per repo |
| **Total** | 4-5 weeks | Production-ready context builder | 85-93% | $0-$0.41/month per repo |

**Next Steps:**
1. Review and approve this plan
2. Set up project tracking (Jira, Linear, etc.)
3. Provision infrastructure:
   - Set up monitoring (Grafana, DataDog)
   - For Phase 3: Set up Pinecone account and OpenAI API access
4. Kick off Phase 1 implementation
5. Daily standups to track progress
6. Weekly demos to stakeholders
7. Decision points:
   - End of Phase 1: Deploy Strategy 4 or continue to Phase 2?
   - End of Phase 2: Deploy Strategy 7 or continue to Phase 3?
   - End of Phase 3: Make Strategy 8 default or keep as optional?

**Estimated Team:**
- 1 Senior Engineer (lead) - Full time
- 1 Mid-level Engineer (support) - Full time
- Part-time: DevOps (infrastructure setup), QA (testing), Product Manager (metrics review)

**Total Investment:**

**Phase 1 (Required):**
- 2 weeks engineering time (2 engineers)
- Minimal infrastructure costs
- AI costs: $0

**Phase 2 (Recommended):**
- 1 week engineering time (2 engineers)
- AI costs: ~$0.41/month per repo (~$20/month for 50 repos)

**Phase 3 (Optional):**
- 1-1.5 weeks engineering time (2 engineers)
- Pinecone: Free tier for < 10 repos, ~$70/month for production scale
- OpenAI embeddings: Included in Phase 2 costs
- Total additional cost: ~$70/month (primarily Pinecone)

**Expected ROI by Phase:**

**Phase 1 (Strategy 4):**
- ✅ 85% context accuracy
- ✅ < 2s context build time
- ✅ Real-time freshness via file watching
- ✅ Zero AI costs
- ✅ Solid foundation for all developer agents

**Phase 2 (Strategy 7):**
- ✅ 90% context accuracy (+5%)
- ✅ 7% token savings (reduced wasted context)
- ✅ Better agent navigation (knows where to look)
- ✅ ROI: ~$20/month cost saves ~$30/month in wasted LLM tokens

**Phase 3 (Strategy 8):**
- ✅ 93% context accuracy (+3%)
- ✅ 92% file recall (+7%)
- ✅ 95% natural language query success (+15%)
- ✅ Better cross-domain understanding
- ✅ Best for teams with heavy NL queries and new feature development

**Recommended Approach:**
1. **Implement Phase 1** (2 weeks) - Required foundation
2. **Monitor metrics** (Days 11-14) - Validate Strategy 4 performance
3. **Implement Phase 2** (1 week) - High-value, low-cost enhancement
4. **Decision point:** Evaluate Phase 3 based on:
   - Team's use of natural language queries
   - Budget for Pinecone infrastructure
   - Value of +3% accuracy improvement
   - Cross-domain feature development needs

**Success Metrics:**
- Developer satisfaction score improved
- Agent task completion rate increased
- Time to complete agent tasks reduced
- Wasted context tokens reduced by 7-10%
- Foundation ready for future AI capabilities
