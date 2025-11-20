"""change_llm_cost_provider_to_varchar

Revision ID: e56078e08225
Revises: c9d8114e9541
Create Date: 2025-11-03 18:33:40.377785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e56078e08225'
down_revision = 'c9d8114e9541'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change provider column from ENUM to VARCHAR in llm_cost_entries
    op.execute("""
        ALTER TABLE llm_cost_entries
        ALTER COLUMN provider TYPE VARCHAR
        USING provider::text
    """)

    # Change provider column from ENUM to VARCHAR in llm_cost_summaries
    op.execute("""
        ALTER TABLE llm_cost_summaries
        ALTER COLUMN provider TYPE VARCHAR
        USING provider::text
    """)

    # Drop the llmprovider ENUM type if it exists
    op.execute("DROP TYPE IF EXISTS llmprovider CASCADE")


def downgrade() -> None:
    # Recreate the ENUM type
    op.execute("""
        CREATE TYPE llmprovider AS ENUM ('openai', 'anthropic', 'groq', 'ollama')
    """)

    # Change provider column back to ENUM in llm_cost_entries
    op.execute("""
        ALTER TABLE llm_cost_entries
        ALTER COLUMN provider TYPE llmprovider
        USING provider::llmprovider
    """)

    # Change provider column back to ENUM in llm_cost_summaries
    op.execute("""
        ALTER TABLE llm_cost_summaries
        ALTER COLUMN provider TYPE llmprovider
        USING provider::llmprovider
    """)

