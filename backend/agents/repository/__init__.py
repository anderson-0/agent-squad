"""
Repository Analysis and Context Building Agents

This module provides components for analyzing codebases and building
optimal context for AI agents working on development tasks.

Components:
- RepositoryDigestor: Initial repository scanning and indexing
- DependencyGraphBuilder: File dependency analysis and graph construction
- FileChangeWatcher: Real-time file change monitoring
- SmartContextBuilder: Intelligent context assembly for agent tasks
- IncrementalContextManager: Context lifecycle management across operations
"""

from backend.agents.repository.repository_digestor import RepositoryDigestor
from backend.agents.repository.dependency_graph_builder import DependencyGraphBuilder
from backend.agents.repository.file_change_watcher import FileChangeWatcher
from backend.agents.repository.smart_context_builder import SmartContextBuilder
from backend.agents.repository.incremental_context_manager import IncrementalContextManager

__all__ = [
    "RepositoryDigestor",
    "DependencyGraphBuilder",
    "FileChangeWatcher",
    "SmartContextBuilder",
    "IncrementalContextManager",
]
