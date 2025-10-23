"""add universal conversations system

Revision ID: 004
Revises: 003
Create Date: 2025-10-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_type', sa.String(50), nullable=False),
        sa.Column('initiator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('initiator_type', sa.String(50), nullable=False),
        sa.Column('primary_responder_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('total_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['primary_responder_id'], ['squad_members.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )

    # Create indexes for conversations
    op.create_index('ix_conversations_conversation_type', 'conversations', ['conversation_type'])
    op.create_index('ix_conversations_initiator_id', 'conversations', ['initiator_id'])
    op.create_index('ix_conversations_initiator_type', 'conversations', ['initiator_type'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_primary_responder_id', 'conversations', ['primary_responder_id'])
    op.create_index('ix_conversations_status', 'conversations', ['status'])
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])
    op.create_index('ix_conversations_updated_at', 'conversations', ['updated_at'])
    op.create_index('ix_conversations_last_message_at', 'conversations', ['last_message_at'])

    # Create conversation_messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.String(50), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('llm_provider', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('agent_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_message_id'], ['agent_messages.id'], ondelete='SET NULL'),
    )

    # Create indexes for conversation_messages
    op.create_index('ix_conversation_messages_conversation_id', 'conversation_messages', ['conversation_id'])
    op.create_index('ix_conversation_messages_sender_id', 'conversation_messages', ['sender_id'])
    op.create_index('ix_conversation_messages_sender_type', 'conversation_messages', ['sender_type'])
    op.create_index('ix_conversation_messages_role', 'conversation_messages', ['role'])
    op.create_index('ix_conversation_messages_created_at', 'conversation_messages', ['created_at'])

    # Create conversation_participants table
    op.create_table(
        'conversation_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_type', sa.String(50), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    )

    # Create indexes for conversation_participants
    op.create_index('ix_conversation_participants_conversation_id', 'conversation_participants', ['conversation_id'])
    op.create_index('ix_conversation_participants_participant_id', 'conversation_participants', ['participant_id'])
    op.create_index('ix_conversation_participants_participant_type', 'conversation_participants', ['participant_type'])
    op.create_index('ix_conversation_participants_is_active', 'conversation_participants', ['is_active'])

    # Create unique constraint for active participants
    op.create_index(
        'ix_conversation_participants_unique_active',
        'conversation_participants',
        ['conversation_id', 'participant_id', 'participant_type'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )


def downgrade():
    # Drop conversation_participants table
    op.drop_index('ix_conversation_participants_unique_active', table_name='conversation_participants')
    op.drop_index('ix_conversation_participants_is_active', table_name='conversation_participants')
    op.drop_index('ix_conversation_participants_participant_type', table_name='conversation_participants')
    op.drop_index('ix_conversation_participants_participant_id', table_name='conversation_participants')
    op.drop_index('ix_conversation_participants_conversation_id', table_name='conversation_participants')
    op.drop_table('conversation_participants')

    # Drop conversation_messages table
    op.drop_index('ix_conversation_messages_created_at', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_role', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_sender_type', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_sender_id', table_name='conversation_messages')
    op.drop_index('ix_conversation_messages_conversation_id', table_name='conversation_messages')
    op.drop_table('conversation_messages')

    # Drop conversations table
    op.drop_index('ix_conversations_last_message_at', table_name='conversations')
    op.drop_index('ix_conversations_updated_at', table_name='conversations')
    op.drop_index('ix_conversations_created_at', table_name='conversations')
    op.drop_index('ix_conversations_status', table_name='conversations')
    op.drop_index('ix_conversations_primary_responder_id', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    op.drop_index('ix_conversations_initiator_type', table_name='conversations')
    op.drop_index('ix_conversations_initiator_id', table_name='conversations')
    op.drop_index('ix_conversations_conversation_type', table_name='conversations')
    op.drop_table('conversations')
