"""add PM Guardian system (coherence metrics)

Revision ID: 006
Revises: 005
Create Date: 2025-01-XX

Adds support for PM-as-Guardian monitoring system:
- CoherenceMetrics model for tracking agent coherence
- Workflow health monitoring capabilities
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Create coherence_metrics table
    op.create_table(
        'coherence_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('monitored_by_pm_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('phase', sa.String(20), nullable=False),
        sa.Column('coherence_score', sa.Float(), nullable=False),
        sa.Column('metrics', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('anomaly_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('pm_action_taken', sa.String(255), nullable=True),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['execution_id'], ['task_executions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['squad_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['monitored_by_pm_id'], ['squad_members.id'], ondelete='SET NULL'),
        sa.CheckConstraint(
            "phase IN ('investigation', 'building', 'validation')",
            name='ck_coherence_metrics_valid_phase'
        ),
        sa.CheckConstraint(
            "coherence_score >= 0.0 AND coherence_score <= 1.0",
            name='ck_coherence_metrics_valid_score'
        ),
    )

    # Create indexes for coherence_metrics
    op.create_index('ix_coherence_metrics_execution_id', 'coherence_metrics', ['execution_id'])
    op.create_index('ix_coherence_metrics_agent_id', 'coherence_metrics', ['agent_id'])
    op.create_index('ix_coherence_metrics_monitored_by_pm_id', 'coherence_metrics', ['monitored_by_pm_id'])
    op.create_index('ix_coherence_metrics_phase', 'coherence_metrics', ['phase'])
    op.create_index('ix_coherence_metrics_anomaly_detected', 'coherence_metrics', ['anomaly_detected'])
    op.create_index('ix_coherence_metrics_calculated_at', 'coherence_metrics', ['calculated_at'])
    op.create_index(
        'ix_coherence_metrics_execution_agent',
        'coherence_metrics',
        ['execution_id', 'agent_id']
    )
    op.create_index(
        'ix_coherence_metrics_execution_phase',
        'coherence_metrics',
        ['execution_id', 'phase']
    )
    op.create_index(
        'ix_coherence_metrics_agent_phase',
        'coherence_metrics',
        ['agent_id', 'phase']
    )
    op.create_index(
        'ix_coherence_metrics_anomaly',
        'coherence_metrics',
        ['anomaly_detected', 'calculated_at']
    )
    op.create_index(
        'ix_coherence_metrics_pm_action',
        'coherence_metrics',
        ['pm_action_taken']
    )
    op.create_index(
        'ix_coherence_metrics_execution_agent_phase',
        'coherence_metrics',
        ['execution_id', 'agent_id', 'phase']
    )


def downgrade():
    # Drop coherence_metrics table
    op.drop_index('ix_coherence_metrics_execution_agent_phase', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_pm_action', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_anomaly', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_agent_phase', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_execution_phase', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_execution_agent', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_calculated_at', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_anomaly_detected', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_phase', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_monitored_by_pm_id', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_agent_id', table_name='coherence_metrics')
    op.drop_index('ix_coherence_metrics_execution_id', table_name='coherence_metrics')
    op.drop_table('coherence_metrics')

