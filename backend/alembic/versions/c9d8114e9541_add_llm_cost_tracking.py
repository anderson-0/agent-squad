"""add_llm_cost_tracking

Revision ID: c9d8114e9541
Revises: 008
Create Date: 2025-11-03 17:19:48.826630

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c9d8114e9541'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create llm_cost_entries table
    op.create_table(
        'llm_cost_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(), nullable=False, index=True),
        sa.Column('model', sa.String(), nullable=False, index=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prompt_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('completion_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('prompt_price_per_1m', sa.Float(), nullable=True),
        sa.Column('completion_price_per_1m', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('finish_reason', sa.String(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('extra_metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Create indexes for llm_cost_entries
    op.create_index('idx_llm_cost_provider_model', 'llm_cost_entries', ['provider', 'model'])
    op.create_index('idx_llm_cost_squad_created', 'llm_cost_entries', ['squad_id', 'created_at'])
    op.create_index('idx_llm_cost_org_created', 'llm_cost_entries', ['organization_id', 'created_at'])
    op.create_index('idx_llm_cost_execution', 'llm_cost_entries', ['task_execution_id'])
    op.create_index('idx_llm_cost_created_at', 'llm_cost_entries', ['created_at'])

    # Create llm_cost_summaries table
    op.create_table(
        'llm_cost_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('summary_type', sa.String(), nullable=False, index=True),
        sa.Column('summary_date', sa.DateTime(), nullable=False, index=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('provider', sa.String(), nullable=True, index=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('avg_tokens_per_request', sa.Float(), nullable=True),
        sa.Column('avg_cost_per_request', sa.Float(), nullable=True),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

    # Create indexes for llm_cost_summaries
    op.create_index('idx_summary_type_date', 'llm_cost_summaries', ['summary_type', 'summary_date'])
    op.create_index('idx_summary_org_date', 'llm_cost_summaries', ['organization_id', 'summary_date'])
    op.create_index('idx_summary_squad_date', 'llm_cost_summaries', ['squad_id', 'summary_date'])
    op.create_index('idx_summary_provider', 'llm_cost_summaries', ['provider', 'summary_date'])


def downgrade() -> None:
    # Drop tables
    op.drop_table('llm_cost_summaries')
    op.drop_table('llm_cost_entries')
