"""add conversation tracking and routing rules

Revision ID: 001
Revises:
Create Date: 2025-10-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_conversations table
    op.create_table(
        'agent_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('initial_message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_state', sa.String(50), nullable=False),
        sa.Column('asker_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_responder_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('escalation_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('question_type', sa.String(100), nullable=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.ForeignKeyConstraint(['initial_message_id'], ['agent_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asker_id'], ['squad_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['current_responder_id'], ['squad_members.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_execution_id'], ['task_executions.id'], ondelete='SET NULL')
    )

    # Create indexes for agent_conversations
    op.create_index('ix_conversations_state', 'agent_conversations', ['current_state'])
    op.create_index('ix_conversations_asker', 'agent_conversations', ['asker_id'])
    op.create_index('ix_conversations_responder', 'agent_conversations', ['current_responder_id'])
    op.create_index('ix_conversations_task', 'agent_conversations', ['task_execution_id'])
    op.create_index(
        'ix_conversations_timeout',
        'agent_conversations',
        ['timeout_at', 'current_state'],
        postgresql_where=sa.text("current_state IN ('waiting', 'follow_up')")
    )

    # Create conversation_events table
    op.create_table(
        'conversation_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('from_state', sa.String(50), nullable=True),
        sa.Column('to_state', sa.String(50), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('triggered_by_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_data', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['agent_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['message_id'], ['agent_messages.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['triggered_by_agent_id'], ['squad_members.id'], ondelete='SET NULL')
    )

    # Create indexes for conversation_events
    op.create_index('ix_conversation_events_conversation', 'conversation_events', ['conversation_id'])
    op.create_index('ix_conversation_events_type', 'conversation_events', ['event_type'])
    op.create_index('ix_conversation_events_created', 'conversation_events', ['created_at'])

    # Add new columns to agent_messages table
    op.add_column('agent_messages', sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('agent_messages', sa.Column('is_acknowledgment', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agent_messages', sa.Column('is_follow_up', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agent_messages', sa.Column('is_escalation', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agent_messages', sa.Column('requires_acknowledgment', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('agent_messages', sa.Column('parent_message_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create foreign keys for new agent_messages columns
    op.create_foreign_key(
        'fk_agent_messages_conversation',
        'agent_messages', 'agent_conversations',
        ['conversation_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_agent_messages_parent',
        'agent_messages', 'agent_messages',
        ['parent_message_id'], ['id'],
        ondelete='SET NULL'
    )

    # Create indexes for new agent_messages columns
    op.create_index('ix_agent_messages_conversation', 'agent_messages', ['conversation_id'])
    op.create_index('ix_agent_messages_parent', 'agent_messages', ['parent_message_id'])

    # Create routing_rules table
    op.create_table(
        'routing_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('asker_role', sa.String(100), nullable=False),
        sa.Column('question_type', sa.String(100), nullable=False),
        sa.Column('escalation_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('responder_role', sa.String(100), nullable=False),
        sa.Column('specific_responder_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rule_metadata', postgresql.JSONB(), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['squad_id'], ['squads.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['specific_responder_id'], ['squad_members.id'], ondelete='CASCADE')
    )

    # Create indexes for routing_rules
    op.create_index('ix_routing_rules_squad_asker_question', 'routing_rules', ['squad_id', 'asker_role', 'question_type'])
    op.create_index('ix_routing_rules_org_asker_question', 'routing_rules', ['organization_id', 'asker_role', 'question_type'])
    op.create_index('ix_routing_rules_escalation', 'routing_rules', ['escalation_level'])
    op.create_index('ix_routing_rules_active', 'routing_rules', ['is_active'])

    # Create default_routing_templates table
    op.create_table(
        'default_routing_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('template_type', sa.String(100), nullable=False),
        sa.Column('routing_rules_template', postgresql.JSONB(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_org_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_org_id'], ['organizations.id'], ondelete='CASCADE')
    )

    # Create indexes for default_routing_templates
    op.create_index('ix_routing_templates_type', 'default_routing_templates', ['template_type'])
    op.create_index('ix_routing_templates_public', 'default_routing_templates', ['is_public'])
    op.create_index('ix_routing_templates_default', 'default_routing_templates', ['is_default'])


def downgrade():
    # Drop indexes for default_routing_templates
    op.drop_index('ix_routing_templates_default', 'default_routing_templates')
    op.drop_index('ix_routing_templates_public', 'default_routing_templates')
    op.drop_index('ix_routing_templates_type', 'default_routing_templates')

    # Drop default_routing_templates table
    op.drop_table('default_routing_templates')

    # Drop indexes for routing_rules
    op.drop_index('ix_routing_rules_active', 'routing_rules')
    op.drop_index('ix_routing_rules_escalation', 'routing_rules')
    op.drop_index('ix_routing_rules_org_asker_question', 'routing_rules')
    op.drop_index('ix_routing_rules_squad_asker_question', 'routing_rules')

    # Drop routing_rules table
    op.drop_table('routing_rules')

    # Drop indexes for new agent_messages columns
    op.drop_index('ix_agent_messages_parent', 'agent_messages')
    op.drop_index('ix_agent_messages_conversation', 'agent_messages')

    # Drop foreign keys from agent_messages
    op.drop_constraint('fk_agent_messages_parent', 'agent_messages', type_='foreignkey')
    op.drop_constraint('fk_agent_messages_conversation', 'agent_messages', type_='foreignkey')

    # Drop new columns from agent_messages
    op.drop_column('agent_messages', 'parent_message_id')
    op.drop_column('agent_messages', 'requires_acknowledgment')
    op.drop_column('agent_messages', 'is_escalation')
    op.drop_column('agent_messages', 'is_follow_up')
    op.drop_column('agent_messages', 'is_acknowledgment')
    op.drop_column('agent_messages', 'conversation_id')

    # Drop indexes for conversation_events
    op.drop_index('ix_conversation_events_created', 'conversation_events')
    op.drop_index('ix_conversation_events_type', 'conversation_events')
    op.drop_index('ix_conversation_events_conversation', 'conversation_events')

    # Drop conversation_events table
    op.drop_table('conversation_events')

    # Drop indexes for agent_conversations
    op.drop_index('ix_conversations_timeout', 'agent_conversations')
    op.drop_index('ix_conversations_task', 'agent_conversations')
    op.drop_index('ix_conversations_responder', 'agent_conversations')
    op.drop_index('ix_conversations_asker', 'agent_conversations')
    op.drop_index('ix_conversations_state', 'agent_conversations')

    # Drop agent_conversations table
    op.drop_table('agent_conversations')
