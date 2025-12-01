"""add_sandbox_indexes

Revision ID: c1d2e3f4g5h6
Revises: b2c3d4e5f6g7
Create Date: 2025-11-21 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4g5h6'
down_revision = 'b2c3d4e5f6g7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add indexes for task_id and status columns
    op.create_index(op.f('ix_sandboxes_task_id'), 'sandboxes', ['task_id'], unique=False)
    op.create_index(op.f('ix_sandboxes_status'), 'sandboxes', ['status'], unique=False)

    # Add foreign key constraints
    op.create_foreign_key(
        'fk_sandboxes_task_id',
        'sandboxes', 'tasks',
        ['task_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_sandboxes_agent_id',
        'sandboxes', 'agents',
        ['agent_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_sandboxes_agent_id', 'sandboxes', type_='foreignkey')
    op.drop_constraint('fk_sandboxes_task_id', 'sandboxes', type_='foreignkey')

    # Drop indexes
    op.drop_index(op.f('ix_sandboxes_status'), table_name='sandboxes')
    op.drop_index(op.f('ix_sandboxes_task_id'), table_name='sandboxes')
