"""add workflow branching

Revision ID: 007
Revises: 006
Create Date: 2025-01-XX

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Create workflow_branches table
    op.create_table(
        'workflow_branches',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_name', sa.String(length=255), nullable=False),
        sa.Column('branch_phase', sa.String(length=20), nullable=False),
        sa.Column('discovery_origin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('discovery_origin_type', sa.String(length=50), nullable=True),
        sa.Column('discovery_description', sa.Text(), nullable=True),
        sa.Column('branch_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_execution_id'], ['task_executions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("branch_phase IN ('investigation', 'building', 'validation')", name='ck_workflow_branches_valid_phase'),
        sa.CheckConstraint("status IN ('active', 'merged', 'abandoned', 'completed')", name='ck_workflow_branches_valid_status'),
    )
    
    # Create indexes
    op.create_index('ix_workflow_branches_execution', 'workflow_branches', ['parent_execution_id'])
    op.create_index('ix_workflow_branches_execution_status', 'workflow_branches', ['parent_execution_id', 'status'])
    op.create_index('ix_workflow_branches_phase', 'workflow_branches', ['branch_phase'])
    
    # Add branch_id to dynamic_tasks
    op.add_column('dynamic_tasks', sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index('ix_dynamic_tasks_branch_id', 'dynamic_tasks', ['branch_id'])
    op.create_foreign_key(
        'fk_dynamic_tasks_branch_id',
        'dynamic_tasks',
        'workflow_branches',
        ['branch_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Remove branch_id from dynamic_tasks
    op.drop_constraint('fk_dynamic_tasks_branch_id', 'dynamic_tasks', type_='foreignkey')
    op.drop_index('ix_dynamic_tasks_branch_id', 'dynamic_tasks')
    op.drop_column('dynamic_tasks', 'branch_id')
    
    # Drop workflow_branches table
    op.drop_index('ix_workflow_branches_phase', 'workflow_branches')
    op.drop_index('ix_workflow_branches_execution_status', 'workflow_branches')
    op.drop_index('ix_workflow_branches_execution', 'workflow_branches')
    op.drop_table('workflow_branches')

