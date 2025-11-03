"""Add performance indexes

Revision ID: 008_add_performance_indexes
Revises: 007_add_workflow_branching
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '008_add_performance_indexes'
down_revision = '007_add_workflow_branching'  # Update to your latest revision
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for frequently queried fields"""

    # Squad members - queries by squad_id and role
    op.create_index(
        'ix_squad_members_squad_role',
        'squad_members',
        ['squad_id', 'role'],
        unique=False
    )

    # Task executions - queries by squad_id and status
    op.create_index(
        'ix_task_executions_squad_status',
        'task_executions',
        ['squad_id', 'status'],
        unique=False
    )

    # Task executions - queries by created_at for recent tasks
    op.create_index(
        'ix_task_executions_created_at',
        'task_executions',
        ['created_at'],
        unique=False
    )

    # Agent messages - queries by sender and timestamp
    op.create_index(
        'ix_agent_messages_sender_created',
        'agent_messages',
        ['sender_id', 'created_at'],
        unique=False
    )

    # Agent messages - queries by execution_id for thread
    op.create_index(
        'ix_agent_messages_execution_created',
        'agent_messages',
        ['execution_id', 'created_at'],
        unique=False
    )

    # Conversations - queries by squad_id and status
    op.create_index(
        'ix_conversations_squad_status',
        'conversations',
        ['squad_id', 'status'],
        unique=False
    )

    # Dynamic tasks - additional composite index for Guardian queries
    op.create_index(
        'ix_dynamic_tasks_phase_created',
        'dynamic_tasks',
        ['phase', 'created_at'],
        unique=False
    )


def downgrade():
    """Remove performance indexes"""
    op.drop_index('ix_dynamic_tasks_phase_created', table_name='dynamic_tasks')
    op.drop_index('ix_conversations_squad_status', table_name='conversations')
    op.drop_index('ix_agent_messages_execution_created', table_name='agent_messages')
    op.drop_index('ix_agent_messages_sender_created', table_name='agent_messages')
    op.drop_index('ix_task_executions_created_at', table_name='task_executions')
    op.drop_index('ix_task_executions_squad_status', table_name='task_executions')
    op.drop_index('ix_squad_members_squad_role', table_name='squad_members')
