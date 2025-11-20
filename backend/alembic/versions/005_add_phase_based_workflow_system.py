"""add phase-based workflow system

Revision ID: 005
Revises: 004
Create Date: 2025-01-XX

Adds support for Hephaestus-style phase-based workflows:
- WorkflowPhase enum concept (stored as string)
- DynamicTask model for tasks spawned by agents
- Task dependencies (blocking relationships)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create dynamic_tasks table
    op.create_table(
        'dynamic_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('parent_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase', sa.String(20), nullable=False),
        sa.Column('spawned_by_agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['parent_execution_id'], ['task_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['spawned_by_agent_id'], ['squad_members.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "phase IN ('investigation', 'building', 'validation')",
            name='ck_dynamic_tasks_valid_phase'
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed', 'blocked')",
            name='ck_dynamic_tasks_valid_status'
        ),
    )

    # Create indexes for dynamic_tasks
    op.create_index('ix_dynamic_tasks_parent_execution_id', 'dynamic_tasks', ['parent_execution_id'])
    op.create_index('ix_dynamic_tasks_phase', 'dynamic_tasks', ['phase'])
    op.create_index('ix_dynamic_tasks_status', 'dynamic_tasks', ['status'])
    op.create_index('ix_dynamic_tasks_spawned_by_agent_id', 'dynamic_tasks', ['spawned_by_agent_id'])
    op.create_index(
        'ix_dynamic_tasks_execution_phase',
        'dynamic_tasks',
        ['parent_execution_id', 'phase']
    )
    op.create_index(
        'ix_dynamic_tasks_execution_status',
        'dynamic_tasks',
        ['parent_execution_id', 'status']
    )
    op.create_index(
        'ix_dynamic_tasks_phase_status',
        'dynamic_tasks',
        ['phase', 'status']
    )
    # Composite index for common query pattern: execution + phase + status
    op.create_index(
        'ix_dynamic_tasks_execution_phase_status',
        'dynamic_tasks',
        ['parent_execution_id', 'phase', 'status']
    )

    # Create task_dependencies table (association table for blocking relationships)
    op.create_table(
        'task_dependencies',
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('blocks_task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['dynamic_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['blocks_task_id'], ['dynamic_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('task_id', 'blocks_task_id'),
        sa.CheckConstraint('task_id != blocks_task_id', name='ck_no_self_dependency'),
    )

    # Create indexes for task_dependencies
    op.create_index('ix_task_dependencies_task_id', 'task_dependencies', ['task_id'])
    op.create_index('ix_task_dependencies_blocks_task_id', 'task_dependencies', ['blocks_task_id'])


def downgrade():
    # Drop task_dependencies table
    op.drop_index('ix_task_dependencies_blocks_task_id', table_name='task_dependencies')
    op.drop_index('ix_task_dependencies_task_id', table_name='task_dependencies')
    op.drop_table('task_dependencies')

    # Drop dynamic_tasks table
    op.drop_index('ix_dynamic_tasks_execution_phase_status', table_name='dynamic_tasks')
    op.drop_index('ix_dynamic_tasks_phase_status', table_name='dynamic_tasks')
    op.drop_index('ix_dynamic_tasks_execution_status', table_name='dynamic_tasks')
    op.drop_index('ix_dynamic_tasks_execution_phase', table_name='dynamic_tasks')
    op.drop_index('ix_dynamic_tasks_spawned_by_agent_id', table_name='dynamic_tasks')
    op.drop_index('ix_dynamic_tasks_status', table_name='dynamic_tasks')
    op.drop_index('ix_dynamic_tasks_phase', table_name='dynamic_tasks')
    op.drop_index('ix_dynamic_tasks_parent_execution_id', table_name='dynamic_tasks')
    op.drop_table('dynamic_tasks')

