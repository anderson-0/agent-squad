"""make_agent_message_task_execution_id_nullable

Revision ID: 8ac963704cb9
Revises: 002
Create Date: 2025-10-22 21:56:30.518211

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ac963704cb9'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make task_execution_id nullable in agent_messages table
    # This allows messages to exist independently of task executions (e.g., for conversations)
    op.alter_column('agent_messages', 'task_execution_id',
               existing_type=sa.UUID(),
               nullable=True)


def downgrade() -> None:
    # Make task_execution_id NOT NULL again
    # Note: This will fail if there are any NULL values in the column
    op.alter_column('agent_messages', 'task_execution_id',
               existing_type=sa.UUID(),
               nullable=False)
