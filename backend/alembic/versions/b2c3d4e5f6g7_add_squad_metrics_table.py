"""add_squad_metrics_table

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-21 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6g7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create squad_metrics table
    op.create_table(
        'squad_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(), nullable=True, default='hourly'),
        
        sa.Column('total_questions', sa.Integer(), default=0),
        sa.Column('total_resolved', sa.Integer(), default=0),
        sa.Column('total_escalated', sa.Integer(), default=0),
        sa.Column('total_timeouts', sa.Integer(), default=0),
        
        sa.Column('avg_resolution_time_seconds', sa.Float(), default=0.0),
        sa.Column('avg_escalation_depth', sa.Float(), default=0.0),
        
        sa.Column('total_cost', sa.Float(), default=0.0),
        
        sa.Column('questions_by_type', sa.JSON(), default=dict),
        sa.Column('agent_performance', sa.JSON(), default=dict),
        
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        
        sa.ForeignKeyConstraint(['squad_id'], ['squads.id'], ),
    )
    
    op.create_index(op.f('ix_squad_metrics_squad_id'), 'squad_metrics', ['squad_id'], unique=False)
    op.create_index(op.f('ix_squad_metrics_start_time'), 'squad_metrics', ['start_time'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_squad_metrics_start_time'), table_name='squad_metrics')
    op.drop_index(op.f('ix_squad_metrics_squad_id'), table_name='squad_metrics')
    op.drop_table('squad_metrics')
