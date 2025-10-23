# Repository Digestion System - Implementation Plan
## Part 5: Phase 3 - Strategy 8 Implementation (Weeks 4-5) [Optional]

> **Navigation:** [Part 4: Phase 2](./04_phase2_strategy7.md) ← | → [Part 6: Conclusion](./06_conclusion.md)

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


---

> **Next:** [Part 6: Conclusion and Next Steps](./06_conclusion.md)
