#!/usr/bin/env python3
"""Reset database - drop and recreate all tables"""
import sys
sys.path.insert(0, '/Users/anderson/Documents/anderson-0/agent-squad')

from backend.core.database import sync_engine
from backend.models.base import Base

# Import all models so they're registered with Base
from backend.models.user import User
from backend.models.squad import Squad, SquadMember
from backend.models.project import Project, Task
from backend.models.task_execution import TaskExecution
from backend.models.agent_message import AgentMessage

print("Dropping all tables...")
Base.metadata.drop_all(bind=sync_engine)
print('✅ Dropped all tables')

print("Creating all tables fresh...")
Base.metadata.create_all(bind=sync_engine)
print('✅ Created all tables')
