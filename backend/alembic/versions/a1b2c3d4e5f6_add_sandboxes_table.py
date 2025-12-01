"""add_sandboxes_table

Revision ID: a1b2c3d4e5f6
Revises: e56078e08225
Create Date: 2025-11-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'e56078e08225'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sandboxes table
    op.create_table(
        'sandboxes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('e2b_id', sa.String(), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('repo_url', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('CREATED', 'RUNNING', 'TERMINATED', 'ERROR', name='sandboxstatus'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    
    op.create_index(op.f('ix_sandboxes_e2b_id'), 'sandboxes', ['e2b_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sandboxes_e2b_id'), table_name='sandboxes')
    op.drop_table('sandboxes')
    op.execute("DROP TYPE sandboxstatus")
