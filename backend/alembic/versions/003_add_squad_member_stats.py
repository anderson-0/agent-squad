"""add squad_member_stats table

Revision ID: 003
Revises: 8ac963704cb9
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '8ac963704cb9'
branch_labels = None
depends_on = None


def upgrade():
    # Create squad_member_stats table
    op.create_table(
        'squad_member_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('squad_member_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('total_input_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_output_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_messages_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_messages_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_message_sent_at', sa.DateTime(), nullable=True),
        sa.Column('last_message_received_at', sa.DateTime(), nullable=True),
        sa.Column('last_llm_call_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['squad_member_id'], ['squad_members.id'], ondelete='CASCADE'),
    )

    # Create indexes
    op.create_index('ix_squad_member_stats_squad_member_id', 'squad_member_stats', ['squad_member_id'])
    op.create_index('ix_squad_member_stats_total_tokens', 'squad_member_stats', ['total_tokens'])
    op.create_index('ix_squad_member_stats_updated_at', 'squad_member_stats', ['updated_at'])


def downgrade():
    # Drop indexes
    op.drop_index('ix_squad_member_stats_updated_at', table_name='squad_member_stats')
    op.drop_index('ix_squad_member_stats_total_tokens', table_name='squad_member_stats')
    op.drop_index('ix_squad_member_stats_squad_member_id', table_name='squad_member_stats')

    # Drop table
    op.drop_table('squad_member_stats')
