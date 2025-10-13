"""
Task Execution Model - Re-export from project.py

This file exists for backward compatibility with imports.
The actual TaskExecution model is defined in project.py
"""
from backend.models.project import TaskExecution

__all__ = ["TaskExecution"]
