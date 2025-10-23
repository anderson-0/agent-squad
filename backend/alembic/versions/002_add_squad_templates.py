"""add squad templates

Revision ID: 002
Revises: 001
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create squad_templates table
    op.create_table(
        'squad_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('template_definition', postgresql.JSONB(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_rating', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Create indexes for squad_templates
    op.create_index('ix_squad_templates_slug', 'squad_templates', ['slug'], unique=True)
    op.create_index('ix_squad_templates_category', 'squad_templates', ['category'], unique=False)
    op.create_index('ix_squad_templates_is_active', 'squad_templates', ['is_active'], unique=False)
    op.create_index('ix_squad_templates_is_featured', 'squad_templates', ['is_featured'], unique=False)


def downgrade():
    # Drop indexes for squad_templates
    op.drop_index('ix_squad_templates_is_featured', 'squad_templates')
    op.drop_index('ix_squad_templates_is_active', 'squad_templates')
    op.drop_index('ix_squad_templates_category', 'squad_templates')
    op.drop_index('ix_squad_templates_slug', 'squad_templates')

    # Drop squad_templates table
    op.drop_table('squad_templates')
