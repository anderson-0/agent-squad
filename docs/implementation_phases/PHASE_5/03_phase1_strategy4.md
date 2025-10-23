# Repository Digestion System - Implementation Plan
## Part 3: Phase 1 - Strategy 4 Implementation (Weeks 1-2)

> **Navigation:** [Part 2: Rationale](./02_rationale_and_approach.md) ← | → [Part 4: Phase 2](./04_phase2_strategy7.md)

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


---

> **Next:** [Part 4: Phase 2 Implementation (Strategy 7)](./04_phase2_strategy7.md)
