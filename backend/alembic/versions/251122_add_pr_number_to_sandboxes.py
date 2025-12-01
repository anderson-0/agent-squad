"""add pr_number to sandboxes

Revision ID: 251122_pr_number
Revises: e56078e08225
Create Date: 2025-11-22 23:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '251122_pr_number'
down_revision = 'e56078e08225'
branch_labels = None
depends_on = None


def upgrade():
    # Add pr_number column to sandboxes table
    op.add_column('sandboxes', sa.Column('pr_number', sa.Integer(), nullable=True))

    # Create index on pr_number for fast webhook lookups
    op.create_index(
        'ix_sandboxes_pr_number',
        'sandboxes',
        ['pr_number'],
        unique=False
    )


def downgrade():
    # Remove index first
    op.drop_index('ix_sandboxes_pr_number', table_name='sandboxes')

    # Remove column
    op.drop_column('sandboxes', 'pr_number')
