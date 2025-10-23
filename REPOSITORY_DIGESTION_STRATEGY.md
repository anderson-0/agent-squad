# Repository Digestion Strategy for Developer Agents

## Executive Summary

**Problem:** Developer agents need to understand constantly-changing codebases without:
- Exceeding context window limits
- Using stale information
- Missing important context
- Wasting tokens on irrelevant files

**Solution:** Hybrid multi-layer approach combining dependency graphs, smart caching, and JIT context assembly.

---

## 📚 Repository Digestion Strategies Explained

There are several approaches to helping developer agents understand and work with repositories. Each has different trade-offs in terms of performance, accuracy, and complexity.

### Strategy 1: Full Context Loading (Naive Approach)

**How it works:**
Load the entire repository into the agent's context window at once.

**Implementation:**
```python
def load_repository(repo_path: str) -> str:
    all_files = []
    for file in get_all_source_files(repo_path):
        content = read_file(file)
        all_files.append(f"=== {file} ===\n{content}")
    return "\n\n".join(all_files)
```

**Pros:**
- ✅ Simple to implement (< 50 lines of code)
- ✅ Agent has complete information
- ✅ No risk of missing relevant context
- ✅ No complex indexing or caching needed

**Cons:**
- ❌ Exceeds context window for any non-trivial repo
- ❌ Wastes tokens on irrelevant files
- ❌ Slow - reads all files every time
- ❌ No freshness tracking (stale data)
- ❌ Expensive - uses maximum tokens always
- ❌ Not scalable beyond tiny repos (< 20 files)

**Use case:** Prototypes, tiny single-file projects, educational examples

---

### Strategy 2: On-Demand File Loading (Reactive Approach)

**How it works:**
Start with minimal context. Agent explicitly requests files as needed using tool calls.

**Implementation:**
```python
class FileLoader:
    @tool
    async def read_file(self, file_path: str) -> str:
        """Agent can call this to load any file"""
        return await load_file(file_path)

    @tool
    async def search_files(self, query: str) -> list:
        """Agent can search for files by keyword"""
        return await grep_files(self.repo_path, query)
```

**Pros:**
- ✅ Efficient - only loads what's needed
- ✅ Scales to any repository size
- ✅ Always fresh (reads from disk on demand)
- ✅ Simple implementation (< 100 lines)
- ✅ Minimal token usage

**Cons:**
- ❌ Agent must know what to ask for (chicken-and-egg problem)
- ❌ Multiple round-trips slow down tasks
- ❌ Agent might miss important context
- ❌ No guidance on what files exist or are relevant
- ❌ Poor UX - agent fumbles around blindly
- ❌ No understanding of file relationships

**Use case:** Simple file-based operations, when agent knows exact file paths

---

### Strategy 3: Semantic Search / Vector Embeddings

**How it works:**
Embed all source files into a vector database. Search by semantic similarity to the task.

**Implementation:**
```python
class SemanticRepositoryIndex:
    async def index_repository(self, repo_path: str):
        """Embed all files"""
        for file in get_source_files(repo_path):
            content = read_file(file)
            embedding = await embed_text(content)  # OpenAI, Cohere, etc.
            await self.vector_db.insert(file, embedding, content)

    async def search(self, query: str, top_k: int = 10) -> list:
        """Find most relevant files"""
        query_embedding = await embed_text(query)
        return await self.vector_db.similarity_search(query_embedding, top_k)
```

**Pros:**
- ✅ Finds semantically related files (not just keyword match)
- ✅ Good for natural language queries
- ✅ Scales well (vector search is fast)
- ✅ Learns from code semantics

**Cons:**
- ❌ Expensive - requires embedding all files (API costs)
- ❌ Slow initial indexing (1-5 seconds per file)
- ❌ Requires external service (vector DB, embedding API)
- ❌ Embeddings go stale (need re-indexing on changes)
- ❌ Complex infrastructure (Pinecone, Weaviate, ChromaDB)
- ❌ Ignores code structure (imports, dependencies)
- ❌ Can miss exact keyword matches
- ❌ Hard to debug (black box similarity)

**Use case:** Large codebases with good documentation, Q&A systems, code search tools

---

### Strategy 4: Dependency Graph + Smart Context Building (Hybrid)

**How it works:**
Build a dependency graph of the codebase. Use graph traversal + keyword search + heuristics to find relevant files. Load the most relevant files ranked by multiple factors.

**Implementation:** (See detailed code in sections below)

**Pros:**
- ✅ Understands code structure (imports, dependencies)
- ✅ Fast - graph queries are instant
- ✅ Efficient - loads only relevant files
- ✅ Accurate - uses multiple relevance signals
- ✅ Fresh - file watcher tracks changes
- ✅ Scalable - handles large repos well
- ✅ No external dependencies (works offline)
- ✅ Explainable - can show why files were included
- ✅ Adaptive - learns from agent access patterns

**Cons:**
- ❌ More complex implementation (~1000 lines)
- ❌ Requires initial graph build time (5-30 seconds)
- ❌ Graph can become stale (needs watching)
- ❌ Language-specific parsing logic needed
- ❌ May miss files with weak/no dependencies

**Use case:** Production systems, complex codebases, real-time development agents

---

### Strategy 5: AI-Powered Summarization

**How it works:**
Use AI to create summaries of files/directories. Load summaries instead of full files.

**Implementation:**
```python
class AISummarizer:
    async def summarize_repository(self, repo_path: str):
        """Create hierarchical summaries"""
        for directory in get_directories(repo_path):
            files = get_files(directory)
            file_contents = [read_file(f) for f in files]

            # Use GPT-4 to summarize directory
            summary = await ai_summarize(
                f"Summarize this directory:\n" + "\n".join(file_contents)
            )

            self.summaries[directory] = summary
```

**Pros:**
- ✅ Compact - summaries use fewer tokens
- ✅ Good for understanding large files
- ✅ Can capture high-level architecture

**Cons:**
- ❌ Very expensive - requires AI calls for all files
- ❌ Extremely slow - seconds per file
- ❌ Lossy - details are lost in summarization
- ❌ Summaries go stale quickly
- ❌ Can hallucinate or miss important details
- ❌ Not suitable for precise code modifications
- ❌ High latency for initial indexing

**Use case:** Code documentation, high-level exploration, architectural understanding

---

### Strategy 6: Git-Based Context

**How it works:**
Use git history to understand what files change together. Load files that are frequently modified together.

**Implementation:**
```python
class GitContextBuilder:
    async def get_related_files(self, file_path: str) -> list:
        """Find files that change together with this file"""
        # Get commits that touched this file
        commits = await git_log(file_path, max_count=50)

        # Find other files in those commits
        co_changed_files = {}
        for commit in commits:
            changed_files = await git_show(commit, name_only=True)
            for other_file in changed_files:
                if other_file != file_path:
                    co_changed_files[other_file] = co_changed_files.get(other_file, 0) + 1

        # Return files sorted by co-change frequency
        return sorted(co_changed_files.items(), key=lambda x: x[1], reverse=True)
```

**Pros:**
- ✅ Reveals implicit relationships
- ✅ Based on real development patterns
- ✅ Fast - git operations are efficient
- ✅ No parsing required

**Cons:**
- ❌ Requires git repository
- ❌ New repositories have little history
- ❌ Biased toward frequently changed files
- ❌ Doesn't understand code structure
- ❌ Can include unrelated files (coincidental changes)
- ❌ Ignores actual dependencies

**Use case:** Supplementary signal for mature projects, refactoring analysis

---

## 📊 Comparison Table

| Strategy | Context Accuracy | Speed | Token Efficiency | Freshness | Complexity | Cost | Scalability | Best For |
|----------|-----------------|-------|------------------|-----------|------------|------|-------------|----------|
| **Full Context Loading** | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐ Slow | ⭐ Wasteful | ⭐⭐⭐⭐⭐ Always fresh | ⭐⭐⭐⭐⭐ Trivial | 💰💰💰💰💰 Very high | ⭐ Tiny repos only | Tiny projects |
| **On-Demand Loading** | ⭐⭐ Poor | ⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐⭐ Minimal | ⭐⭐⭐⭐⭐ Always fresh | ⭐⭐⭐⭐⭐ Very simple | 💰 Low | ⭐⭐⭐⭐⭐ Unlimited | Known file paths |
| **Semantic Search** | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Medium | ⭐⭐⭐⭐ Good | ⭐⭐ Stale | ⭐⭐ Complex | 💰💰💰💰 High | ⭐⭐⭐⭐ Good | Large documented codebases |
| **Dependency Graph** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Very fast | ⭐⭐⭐⭐⭐ Optimal | ⭐⭐⭐⭐⭐ Real-time | ⭐⭐⭐ Moderate | 💰 Low | ⭐⭐⭐⭐⭐ Excellent | **Production systems** |
| **AI Summarization** | ⭐⭐⭐ Lossy | ⭐ Very slow | ⭐⭐⭐ Good | ⭐ Very stale | ⭐⭐ Complex | 💰💰💰💰💰 Very high | ⭐⭐⭐ Limited | Exploration only |
| **Git-Based** | ⭐⭐⭐ Decent | ⭐⭐⭐⭐ Fast | ⭐⭐⭐⭐ Good | ⭐⭐⭐⭐ Fresh | ⭐⭐⭐⭐ Simple | 💰 Low | ⭐⭐⭐⭐ Good | Supplementary signal |

### Detailed Metrics Comparison

| Strategy | Initial Setup Time | Per-Task Time | Token Cost (per task) | RAM Usage | Storage | External Deps |
|----------|-------------------|---------------|----------------------|-----------|---------|---------------|
| Full Context | 1s | 1s | 50,000+ | Low | None | None |
| On-Demand | 0s | 2-5s | 2,000-10,000 | Low | None | None |
| Semantic Search | 60-300s | 0.5s | 5,000-15,000 | High | High | Vector DB, Embedding API |
| Dependency Graph | 5-30s | 0.5s | 3,000-8,000 | Medium | Low | None |
| AI Summarization | 300-3600s | 1s | 8,000-20,000 | Low | Medium | LLM API |
| Git-Based | 1s | 0.2s | 3,000-10,000 | Low | None | Git |

---

## 🏆 Recommended Strategy

**Winner: Dependency Graph + Smart Context Building (Strategy 4)**

### Why This Wins:

1. **Best Balance**: Accurate, fast, efficient, and fresh
2. **No External Dependencies**: Works offline, no API costs
3. **Explainable**: Can show why files were included
4. **Real-time**: File watcher keeps context fresh
5. **Scales Well**: Handles repos with 10,000+ files
6. **Adaptive**: Learns from agent behavior over time

### Hybrid Enhancement:

Combine multiple strategies for best results:

```
Primary: Dependency Graph (Structure understanding)
    ↓
+ Keyword Search (Explicit matches)
    ↓
+ Recency Tracking (Recent changes)
    ↓
+ Git Co-change (Implicit relationships) [Optional]
    ↓
+ Semantic Search (Fuzzy matching) [Optional, if needed]
```

---

## 🎯 Recommended Architecture

### Phase 1: Initial Repository Scan (One-time)

```python
class RepositoryDigestor:
    """Handles repository understanding for developer agents"""

    async def initial_scan(self, repo_path: str) -> RepositoryIndex:
        """
        Lightweight scan to build repository index
        Time: ~1-2 seconds for medium repo
        """
        return {
            "structure": await self.get_directory_tree(repo_path, max_depth=3),
            "entry_points": await self.find_entry_points(repo_path),
            "tech_stack": await self.detect_technologies(repo_path),
            "file_inventory": await self.catalog_files(repo_path),
            "documentation": await self.find_docs(repo_path)
        }

    async def get_directory_tree(self, path: str, max_depth: int = 3) -> dict:
        """
        Get directory structure (for agent orientation)

        Returns:
        {
            "src/": {
                "api/": ["auth.py", "users.py"],
                "models/": ["user.py", "session.py"],
                "services/": ["auth_service.py"]
            },
            "tests/": {...},
            "docs/": {...}
        }
        """
        pass

    async def find_entry_points(self, path: str) -> list:
        """
        Find main entry points:
        - main.py, app.py, index.js
        - API route definitions
        - CLI commands
        """
        pass
```

**Output (Layer 0 Context):**
```
Repository: agent-squad
Tech Stack: Python 3.11, FastAPI, PostgreSQL, React
Structure:
  backend/
    ├── api/ (15 files)
    ├── models/ (12 files)
    ├── services/ (8 files)
    └── agents/ (6 files)
  frontend/
    ├── src/ (43 files)
    └── components/ (28 files)
  tests/ (34 files)
Entry Points: backend/main.py, frontend/src/index.tsx
```

---

### Phase 2: Dependency Graph Builder

```python
class DependencyGraphBuilder:
    """Builds and maintains file dependency graph"""

    def __init__(self):
        self.graph = {}  # file -> [dependencies]
        self.reverse_graph = {}  # file -> [dependents]
        self.last_modified = {}  # file -> timestamp

    async def build_graph(self, repo_path: str, language: str) -> DependencyGraph:
        """
        Parse all source files to build dependency graph
        Time: ~5-10 seconds for medium repo
        """
        for file_path in self.get_source_files(repo_path):
            imports = await self.parse_imports(file_path, language)
            self.graph[file_path] = imports

            for imported_file in imports:
                if imported_file not in self.reverse_graph:
                    self.reverse_graph[imported_file] = []
                self.reverse_graph[imported_file].append(file_path)

        return DependencyGraph(self.graph, self.reverse_graph)

    async def parse_imports(self, file_path: str, language: str) -> list:
        """
        Extract imports from file based on language

        Python: import X, from Y import Z
        JavaScript: import X from 'Y', require('Y')
        TypeScript: import X from 'Y'
        """
        if language == "python":
            return await self._parse_python_imports(file_path)
        elif language == "javascript":
            return await self._parse_js_imports(file_path)
        # ... more languages

    def get_related_files(self, file_path: str, depth: int = 2) -> set:
        """
        Get all files related to this file within N hops

        depth=1: Direct dependencies + direct dependents
        depth=2: + second-level connections
        depth=3: + third-level connections

        Example:
        get_related_files("backend/api/users.py", depth=2)

        Returns:
        {
            "backend/models/user.py",        # imported by users.py
            "backend/services/auth.py",      # imported by users.py
            "backend/api/auth.py",           # imports users.py
            "backend/models/session.py",     # imported by auth.py (depth 2)
            "tests/test_users.py"            # imports users.py
        }
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
```

---

### Phase 3: File Change Watcher

```python
class FileChangeWatcher:
    """Watches for file changes and updates context"""

    def __init__(self, repo_path: str, dependency_graph: DependencyGraph):
        self.repo_path = repo_path
        self.graph = dependency_graph
        self.watcher = None

    async def start_watching(self):
        """
        Watch file system for changes
        Use: watchdog library or inotify
        """
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, callback):
                self.callback = callback

            def on_modified(self, event):
                if not event.is_directory:
                    asyncio.create_task(self.callback(event.src_path))

        handler = ChangeHandler(self.on_file_changed)
        self.watcher = Observer()
        self.watcher.schedule(handler, self.repo_path, recursive=True)
        self.watcher.start()

    async def on_file_changed(self, file_path: str):
        """
        File changed - update graph and notify agents
        """
        # Update last modified timestamp
        self.graph.last_modified[file_path] = datetime.utcnow()

        # Re-parse imports (in case they changed)
        new_imports = await self.graph.parse_imports(file_path)
        old_imports = self.graph.graph.get(file_path, [])

        if new_imports != old_imports:
            # Dependencies changed - rebuild graph edges
            self.graph.update_file_dependencies(file_path, new_imports)

        # Invalidate caches
        await self.invalidate_related_caches(file_path)

        # Notify agents working on this file or related files
        await self.notify_agents(file_path)
```

---

### Phase 4: Smart Context Builder (Core Algorithm)

```python
class SmartContextBuilder:
    """Builds optimal context for agent based on task"""

    def __init__(self, repo_index: RepositoryIndex, dep_graph: DependencyGraph):
        self.index = repo_index
        self.graph = dep_graph
        self.file_cache = LRUCache(max_size=100)  # Cache recently-accessed files

    async def build_context_for_task(
        self,
        task: str,
        max_tokens: int = 8000,
        focus_files: list = None
    ) -> AgentContext:
        """
        Build optimal context for agent task

        Strategy:
        1. Parse task to extract keywords and intent
        2. Find relevant files using multiple strategies
        3. Rank files by relevance
        4. Load files until context window is full
        5. Return structured context
        """
        # Step 1: Parse task
        task_info = await self.parse_task(task)

        # Step 2: Find relevant files (multiple strategies)
        candidate_files = set()

        # Strategy A: Keyword search
        keyword_files = await self.search_by_keywords(
            task_info.keywords,
            file_types=task_info.file_types
        )
        candidate_files.update(keyword_files)

        # Strategy B: Focus files + dependencies
        if focus_files:
            for file in focus_files:
                candidate_files.add(file)
                # Add dependencies (2 hops)
                related = self.graph.get_related_files(file, depth=2)
                candidate_files.update(related)

        # Strategy C: Recently modified files (if task mentions "recent changes")
        if "recent" in task.lower() or "latest" in task.lower():
            recent_files = await self.get_recent_files(hours=24)
            candidate_files.update(recent_files)

        # Strategy D: Test files (if task mentions "test" or "bug")
        if any(word in task.lower() for word in ["test", "bug", "fix", "error"]):
            test_files = await self.find_test_files(keyword_files)
            candidate_files.update(test_files)

        # Step 3: Rank files by relevance
        ranked_files = await self.rank_files(
            candidate_files,
            task_info=task_info,
            focus_files=focus_files
        )

        # Step 4: Load files until context window full
        context = AgentContext(task=task)
        token_count = 0

        # Always include repository overview (small)
        context.add_layer("overview", self.index.structure)
        token_count += self.estimate_tokens(self.index.structure)

        # Load files by rank until context full
        for file_path, relevance_score in ranked_files:
            # Check if file is cached
            if file_path in self.file_cache:
                file_content = self.file_cache[file_path]
            else:
                file_content = await self.load_file(file_path)
                self.file_cache[file_path] = file_content

            file_tokens = self.estimate_tokens(file_content)

            if token_count + file_tokens > max_tokens:
                # Context window full - stop here
                break

            context.add_file(file_path, file_content, relevance_score)
            token_count += file_tokens

        # Step 5: Add file signatures for remaining candidates
        # (Give agent awareness of other relevant files)
        remaining = ranked_files[len(context.files):]
        for file_path, score in remaining[:20]:  # Top 20 remaining
            signature = await self.get_file_signature(file_path)
            context.add_signature(file_path, signature, score)

        context.token_count = token_count
        return context

    async def rank_files(
        self,
        files: set,
        task_info: TaskInfo,
        focus_files: list = None
    ) -> list:
        """
        Rank files by relevance to task

        Scoring factors:
        - Keyword matches (weight: 0.3)
        - Recently modified (weight: 0.2)
        - Dependency distance from focus files (weight: 0.2)
        - File type match (weight: 0.1)
        - File size (weight: 0.1, prefer smaller)
        - Previous agent access (weight: 0.1)
        """
        scores = {}

        for file_path in files:
            score = 0.0

            # Factor 1: Keyword matches
            file_content = await self.load_file(file_path)
            keyword_matches = sum(
                kw.lower() in file_content.lower()
                for kw in task_info.keywords
            )
            score += (keyword_matches / len(task_info.keywords)) * 0.3

            # Factor 2: Recency
            last_mod = self.graph.last_modified.get(file_path)
            if last_mod:
                hours_ago = (datetime.utcnow() - last_mod).total_seconds() / 3600
                recency_score = max(0, 1 - (hours_ago / 168))  # Decay over 1 week
                score += recency_score * 0.2

            # Factor 3: Dependency distance
            if focus_files:
                min_distance = min(
                    self.graph.get_distance(file_path, focus)
                    for focus in focus_files
                )
                distance_score = max(0, 1 - (min_distance / 5))  # Max distance 5
                score += distance_score * 0.2

            # Factor 4: File type match
            if self.file_type_matches(file_path, task_info.file_types):
                score += 0.1

            # Factor 5: File size (prefer smaller)
            file_size = os.path.getsize(file_path)
            size_score = max(0, 1 - (file_size / 10000))  # Prefer < 10KB
            score += size_score * 0.1

            # Factor 6: Agent access history
            if file_path in self.file_cache:
                score += 0.1

            scores[file_path] = score

        # Sort by score descending
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    async def get_file_signature(self, file_path: str) -> str:
        """
        Get file signature (summary without implementation)

        For Python:
        - Class/function definitions
        - Docstrings
        - Type hints

        For JavaScript:
        - Function signatures
        - JSDoc comments
        - Exported functions
        """
        content = await self.load_file(file_path)

        if file_path.endswith('.py'):
            return await self._extract_python_signature(content)
        elif file_path.endswith(('.js', '.ts', '.tsx')):
            return await self._extract_js_signature(content)

        # Fallback: first 500 chars
        return content[:500] + "..."
```

---

### Phase 5: Incremental Context Updates

```python
class IncrementalContextManager:
    """Manages agent context across multiple operations"""

    def __init__(self, context_builder: SmartContextBuilder):
        self.builder = context_builder
        self.active_contexts = {}  # agent_id -> AgentContext

    async def get_context_for_agent(
        self,
        agent_id: str,
        task: str,
        force_refresh: bool = False
    ) -> AgentContext:
        """
        Get context for agent (reuse if possible)
        """
        if agent_id in self.active_contexts and not force_refresh:
            # Agent has existing context
            context = self.active_contexts[agent_id]

            # Check if any files in context have changed
            stale_files = await self.check_staleness(context)

            if stale_files:
                # Some files changed - refresh them
                await self.refresh_files(context, stale_files)

            return context
        else:
            # Build new context
            context = await self.builder.build_context_for_task(task)
            self.active_contexts[agent_id] = context
            return context

    async def add_file_to_context(
        self,
        agent_id: str,
        file_path: str
    ) -> AgentContext:
        """
        Agent requests additional file
        """
        context = self.active_contexts[agent_id]

        # Load file
        content = await self.builder.load_file(file_path)
        tokens = self.builder.estimate_tokens(content)

        # Check if fits in context window
        if context.token_count + tokens > context.max_tokens:
            # Remove least relevant files to make room
            await self.evict_files(context, tokens_needed=tokens)

        context.add_file(file_path, content)
        context.token_count += tokens

        return context

    async def on_file_changed(self, file_path: str):
        """
        File changed - update all agent contexts using this file
        """
        for agent_id, context in self.active_contexts.items():
            if file_path in context.files:
                # Reload file
                new_content = await self.builder.load_file(file_path)
                context.update_file(file_path, new_content)

                # Notify agent
                await self.notify_agent(agent_id, f"File {file_path} was modified")
```

---

## 🎯 Implementation Example

### Complete Workflow

```python
# 1. Initialize repository digestion system
repo_digestor = RepositoryDigestor()
repo_index = await repo_digestor.initial_scan("/path/to/repo")

# 2. Build dependency graph
graph_builder = DependencyGraphBuilder()
dep_graph = await graph_builder.build_graph("/path/to/repo", language="python")

# 3. Start file watcher
watcher = FileChangeWatcher("/path/to/repo", dep_graph)
await watcher.start_watching()

# 4. Create context builder
context_builder = SmartContextBuilder(repo_index, dep_graph)

# 5. Agent receives task
agent_id = "frontend_developer_1"
task = "Add authentication to the user profile page"

# 6. Build context for task
context = await context_builder.build_context_for_task(
    task=task,
    max_tokens=8000,
    focus_files=["frontend/src/pages/UserProfile.tsx"]
)

# 7. Context contains:
print(f"Repository: {context.overview}")
print(f"Loaded {len(context.files)} files ({context.token_count} tokens)")
print(f"Files:")
for file_path, relevance in context.files:
    print(f"  - {file_path} (relevance: {relevance:.2f})")
print(f"\nAdditional available files: {len(context.signatures)}")

# 8. Agent works with context
# ... agent modifies files ...

# 9. File watcher detects changes
# Automatically updates dependency graph and notifies agent

# 10. Agent requests more context
await context_builder.add_file_to_context(
    agent_id=agent_id,
    file_path="frontend/src/services/AuthService.ts"
)
```

---

## 📊 Performance Characteristics

### Initial Scan
- **Small repo** (< 100 files): ~0.5 seconds
- **Medium repo** (100-1000 files): ~2 seconds
- **Large repo** (1000-10000 files): ~10 seconds
- **Very large repo** (> 10000 files): ~30 seconds

### Dependency Graph Build
- **Small repo**: ~1 second
- **Medium repo**: ~5 seconds
- **Large repo**: ~20 seconds
- **Very large repo**: ~60 seconds

### Context Building (per task)
- **File search**: ~0.1 seconds
- **File ranking**: ~0.2 seconds
- **File loading**: ~0.5 seconds
- **Total**: < 1 second

### Incremental Updates
- **File change detection**: Instant (file watcher)
- **Graph update**: ~0.01 seconds per file
- **Cache invalidation**: ~0.001 seconds

---

## 🔧 Technology Stack

### Core Components

```python
# File watching
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Code parsing (dependency extraction)
import ast  # Python
import esprima  # JavaScript
from tree_sitter import Parser  # Multi-language

# Caching
from cachetools import LRUCache

# Graph operations
import networkx as nx

# File operations
import pathlib
from pathspec import PathSpec  # .gitignore parsing
```

---

## 🎯 Optimization Strategies

### 1. Lazy Loading
```python
# Don't load all files at startup
# Load on-demand when agent needs them

class LazyFileLoader:
    def __init__(self):
        self.loaded_files = {}

    async def get_file(self, path: str) -> str:
        if path not in self.loaded_files:
            self.loaded_files[path] = await self.read_file(path)
        return self.loaded_files[path]
```

### 2. Diff-based Updates
```python
# When file changes, only send the diff to agent

class DiffManager:
    async def on_file_changed(self, file_path: str):
        old_content = self.cache.get(file_path)
        new_content = await self.read_file(file_path)

        if old_content:
            diff = self.compute_diff(old_content, new_content)
            await self.notify_agent(f"File changed:\n{diff}")

        self.cache[file_path] = new_content
```

### 3. Hierarchical Summarization
```python
# Summarize large files before including in context

class FileSummarizer:
    async def get_file_or_summary(self, file_path: str, max_size: int = 1000):
        content = await self.read_file(file_path)

        if len(content) < max_size:
            return content
        else:
            # File too large - return summary
            return await self.summarize_file(content)

    async def summarize_file(self, content: str) -> str:
        """
        Extract key information:
        - Imports
        - Class/function signatures
        - Docstrings
        """
        pass
```

### 4. Prefetching
```python
# Predict what files agent will need next

class PrefetchManager:
    async def prefetch_likely_files(self, current_file: str):
        # Get files agent will likely need
        dependencies = self.graph.get_related_files(current_file, depth=1)

        # Load in background
        for dep in dependencies:
            asyncio.create_task(self.cache.warm(dep))
```

---

## 🏆 Best Practices

### 1. Progressive Disclosure
Start with overview, drill down only when needed

### 2. Respect .gitignore
Don't index ignored files (node_modules, etc.)

### 3. Track Agent Working Set
Remember what files agent accessed recently

### 4. Invalidate Aggressively
When file changes, mark related files as potentially stale

### 5. Use File Signatures
Include function/class signatures for files not fully loaded

### 6. Monitor Context Window
Always track token usage to avoid overflow

### 7. Provide Escape Hatch
Let agent explicitly request any file

---

## 🚀 Summary

**Recommended Strategy: Hybrid Approach**

1. ✅ **Initial Scan** - Lightweight, fast orientation
2. ✅ **Dependency Graph** - Understand code structure
3. ✅ **File Watcher** - Stay fresh with changes
4. ✅ **Smart Context Builder** - Task-specific, ranked context
5. ✅ **Incremental Updates** - Efficient, real-time
6. ✅ **Agent Memory** - Learn what's important over time

**Result:** Agents always have fresh, relevant context without overloading the context window or wasting tokens.

**Next Steps:**
1. Implement Phase 1 (Initial Scan) - 1 day
2. Implement Phase 2 (Dependency Graph) - 2 days
3. Implement Phase 3 (File Watcher) - 1 day
4. Implement Phase 4 (Smart Context Builder) - 3 days
5. Test and optimize - 2 days

**Total: ~2 weeks for full implementation**
