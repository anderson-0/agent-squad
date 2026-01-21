"""Initial schema - all tables

Revision ID: 001_initial
Revises: None
Create Date: 2026-01-21

Creates all database tables in correct dependency order.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables"""

    # ==== TIER 1: No foreign key dependencies ====

    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(), nullable=True),
        sa.Column('plan_tier', sa.String(), nullable=False, server_default='starter'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'])

    # ==== TIER 2: Depends on users ====

    # Organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_organizations_owner_id', 'organizations', ['owner_id'])

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(), nullable=True),
        sa.Column('stripe_price_id', sa.String(), nullable=True),
        sa.Column('plan', sa.String(), nullable=False, server_default='starter'),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('current_period_start', sa.DateTime(), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_subscriptions_user_id', 'subscriptions', ['user_id'])

    # Usage metrics table
    op.create_table(
        'usage_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric_type', sa.String(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_usage_metrics_user_id', 'usage_metrics', ['user_id'])

    # ==== TIER 3: Depends on users and organizations ====

    # Squads table
    op.create_table(
        'squads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('is_paused', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_squads_user_id', 'squads', ['user_id'])
    op.create_index('ix_squads_org_id', 'squads', ['org_id'])
    op.create_index('ix_squads_user_id_status', 'squads', ['user_id', 'status'])

    # ==== TIER 4: Depends on squads ====

    # Squad members table
    op.create_table(
        'squad_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('specialization', sa.String(), nullable=True),
        sa.Column('llm_provider', sa.String(), nullable=False, server_default='openai'),
        sa.Column('llm_model', sa.String(), nullable=False, server_default='gpt-4'),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_squad_members_squad_id', 'squad_members', ['squad_id'])
    op.create_index('ix_squad_members_squad_id_role', 'squad_members', ['squad_id', 'role'])

    # Squad member stats table
    op.create_table(
        'squad_member_stats',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_member_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('total_messages_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_messages_received', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tasks_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_response_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_squad_member_stats_member_id', 'squad_member_stats', ['squad_member_id'])

    # Squad templates table
    op.create_table(
        'squad_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Projects table
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('git_repo_url', sa.String(), nullable=True),
        sa.Column('git_provider', sa.String(), nullable=True),
        sa.Column('ticket_system_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_projects_squad_id', 'projects', ['squad_id'])
    op.create_index('ix_projects_squad_id_is_active', 'projects', ['squad_id', 'is_active'])

    # Learning insights table
    op.create_table(
        'learning_insights',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('insight_text', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_learning_insights_squad_id', 'learning_insights', ['squad_id'])

    # ==== TIER 5: Depends on projects ====

    # Tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('priority', sa.String(), nullable=False, server_default='medium'),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.Column('task_metadata', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('ix_tasks_project_id_status', 'tasks', ['project_id', 'status'])
    op.create_index('ix_tasks_external_id', 'tasks', ['external_id'])

    # Integrations table
    op.create_table(
        'integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('integration_type', sa.String(), nullable=False),
        sa.Column('config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_integrations_project_id', 'integrations', ['project_id'])

    # Webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('secret', sa.String(), nullable=True),
        sa.Column('events', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_webhooks_project_id', 'webhooks', ['project_id'])

    # ==== TIER 6: Depends on tasks and squads ====

    # Task executions table
    op.create_table(
        'task_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('logs', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('execution_metadata', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_task_executions_task_id', 'task_executions', ['task_id'])
    op.create_index('ix_task_executions_squad_id', 'task_executions', ['squad_id'])
    op.create_index('ix_task_executions_squad_id_status', 'task_executions', ['squad_id', 'status'])
    op.create_index('ix_task_executions_status_created_at', 'task_executions', ['status', 'created_at'])

    # Workflow branches table
    op.create_table(
        'workflow_branches',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_workflow_branches_execution_id', 'workflow_branches', ['parent_execution_id'])

    # ==== TIER 7: Depends on task_executions and squad_members ====

    # Agent messages table (needs to exist before conversations)
    op.create_table(
        'agent_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='CASCADE'), nullable=True),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='SET NULL'), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(), nullable=False),
        sa.Column('message_metadata', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        # Conversation tracking columns (added later via FK)
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_acknowledgment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_follow_up', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_escalation', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('requires_acknowledgment', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_messages.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_agent_messages_task_execution_id', 'agent_messages', ['task_execution_id'])
    op.create_index('ix_agent_messages_task_execution_id_created_at', 'agent_messages', ['task_execution_id', 'created_at'])
    op.create_index('ix_agent_messages_sender_id', 'agent_messages', ['sender_id'])
    op.create_index('ix_agent_messages_recipient_id', 'agent_messages', ['recipient_id'])
    op.create_index('ix_agent_messages_conversation', 'agent_messages', ['conversation_id'])
    op.create_index('ix_agent_messages_parent', 'agent_messages', ['parent_message_id'])

    # Feedback table
    op.create_table(
        'feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_feedback_task_execution_id', 'feedback', ['task_execution_id'])
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])

    # Coherence metrics table (Guardian system)
    op.create_table(
        'coherence_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('coherence_score', sa.Float(), nullable=False),
        sa.Column('details', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_coherence_metrics_execution_id', 'coherence_metrics', ['task_execution_id'])

    # Dynamic tasks table
    op.create_table(
        'dynamic_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('parent_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workflow_branches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('phase', sa.String(20), nullable=False),
        sa.Column('spawned_by_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='SET NULL'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("phase IN ('investigation', 'building', 'validation')", name='ck_dynamic_tasks_valid_phase'),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed', 'blocked')", name='ck_dynamic_tasks_valid_status'),
    )
    op.create_index('ix_dynamic_tasks_execution_phase', 'dynamic_tasks', ['parent_execution_id', 'phase'])
    op.create_index('ix_dynamic_tasks_execution_status', 'dynamic_tasks', ['parent_execution_id', 'status'])
    op.create_index('ix_dynamic_tasks_phase_status', 'dynamic_tasks', ['phase', 'status'])

    # Task dependencies (blocking relationships)
    op.create_table(
        'task_dependencies',
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dynamic_tasks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('blocks_task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('dynamic_tasks.id', ondelete='CASCADE'), primary_key=True),
        sa.CheckConstraint('task_id != blocks_task_id', name='ck_no_self_dependency'),
    )
    op.create_index('ix_task_dependencies_task_id', 'task_dependencies', ['task_id'])
    op.create_index('ix_task_dependencies_blocks_task_id', 'task_dependencies', ['blocks_task_id'])

    # ==== TIER 8: Agent conversations (depends on agent_messages) ====

    # Agent conversations table
    op.create_table(
        'agent_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('initial_message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_state', sa.String(50), nullable=False, server_default='initiated'),
        sa.Column('asker_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('current_responder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('escalation_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('question_type', sa.String(100), nullable=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timeout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
    )
    op.create_index('ix_conversations_state', 'agent_conversations', ['current_state'])
    op.create_index('ix_conversations_asker', 'agent_conversations', ['asker_id'])
    op.create_index('ix_conversations_responder', 'agent_conversations', ['current_responder_id'])
    op.create_index('ix_conversations_task', 'agent_conversations', ['task_execution_id'])

    # Add FK from agent_messages to agent_conversations
    op.create_foreign_key(
        'fk_agent_messages_conversation',
        'agent_messages', 'agent_conversations',
        ['conversation_id'], ['id'],
        ondelete='SET NULL'
    )

    # Conversation events table
    op.create_table(
        'conversation_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('from_state', sa.String(50), nullable=True),
        sa.Column('to_state', sa.String(50), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('triggered_by_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='SET NULL'), nullable=True),
        sa.Column('event_data', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_conversation_events_conversation', 'conversation_events', ['conversation_id'])
    op.create_index('ix_conversation_events_type', 'conversation_events', ['event_type'])

    # Routing rules table
    op.create_table(
        'routing_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('rule_config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_routing_rules_squad_id', 'routing_rules', ['squad_id'])

    # Default routing templates table
    op.create_table(
        'default_routing_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('template_config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # ==== TIER 9: Multi-turn conversations ====

    # Multi-turn conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_type', sa.String(50), nullable=False),
        sa.Column('initiator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('initiator_type', sa.String(50), nullable=False),
        sa.Column('primary_responder_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='SET NULL'), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('agent_conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_conversations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('total_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
    )
    op.create_index('ix_conversations_type', 'conversations', ['conversation_type'])
    op.create_index('ix_conversations_initiator', 'conversations', ['initiator_id'])
    op.create_index('ix_conversations_status', 'conversations', ['status'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])

    # Conversation messages table
    op.create_table(
        'conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
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
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('agent_message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('agent_messages.id', ondelete='SET NULL'), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
    )
    op.create_index('ix_conversation_messages_conversation', 'conversation_messages', ['conversation_id'])
    op.create_index('ix_conversation_messages_sender', 'conversation_messages', ['sender_id'])

    # Conversation participants table
    op.create_table(
        'conversation_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_type', sa.String(50), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('joined_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('conv_metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
    )
    op.create_index('ix_conversation_participants_conversation', 'conversation_participants', ['conversation_id'])
    op.create_index('ix_conversation_participants_participant', 'conversation_participants', ['participant_id'])

    # ==== TIER 10: LLM Cost tracking ====

    # LLM cost entries table
    op.create_table(
        'llm_cost_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=False),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='SET NULL'), nullable=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
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
        sa.Column('extra_metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_llm_cost_entries_provider', 'llm_cost_entries', ['provider'])
    op.create_index('ix_llm_cost_entries_model', 'llm_cost_entries', ['model'])
    op.create_index('ix_llm_cost_entries_squad_id', 'llm_cost_entries', ['squad_id'])
    op.create_index('idx_llm_cost_provider_model', 'llm_cost_entries', ['provider', 'model'])
    op.create_index('idx_llm_cost_squad_created', 'llm_cost_entries', ['squad_id', 'created_at'])
    op.create_index('idx_llm_cost_created_at', 'llm_cost_entries', ['created_at'])

    # LLM cost summaries table
    op.create_table(
        'llm_cost_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('summary_type', sa.String(), nullable=False),
        sa.Column('summary_date', sa.DateTime(), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('squad_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squads.id', ondelete='CASCADE'), nullable=True),
        sa.Column('provider', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_cost_usd', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('avg_tokens_per_request', sa.Float(), nullable=True),
        sa.Column('avg_cost_per_request', sa.Float(), nullable=True),
        sa.Column('avg_response_time_ms', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_summary_type_date', 'llm_cost_summaries', ['summary_type', 'summary_date'])
    op.create_index('idx_summary_org_date', 'llm_cost_summaries', ['organization_id', 'summary_date'])

    # ==== TIER 11: Sandbox and approval tables ====

    # Sandboxes table
    op.create_table(
        'sandboxes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('e2b_id', sa.String(), nullable=False),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('repo_url', sa.String(), nullable=True),
        sa.Column('pr_number', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('created', 'running', 'terminated', 'error', name='sandboxstatus'), nullable=False, server_default='created'),
        sa.Column('last_used_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_sandboxes_e2b_id', 'sandboxes', ['e2b_id'])
    op.create_index('ix_sandboxes_pr_number', 'sandboxes', ['pr_number'])

    # Approval requests table
    op.create_table(
        'approval_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('task_execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('requested_by_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('squad_members.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approval_type', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('reviewed_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_approval_requests_execution_id', 'approval_requests', ['task_execution_id'])
    op.create_index('ix_approval_requests_status', 'approval_requests', ['status'])


def downgrade() -> None:
    """Drop all tables in reverse order"""
    op.drop_table('approval_requests')
    op.drop_table('sandboxes')
    op.execute('DROP TYPE IF EXISTS sandboxstatus')
    op.drop_table('llm_cost_summaries')
    op.drop_table('llm_cost_entries')
    op.drop_table('conversation_participants')
    op.drop_table('conversation_messages')
    op.drop_table('conversations')
    op.drop_table('default_routing_templates')
    op.drop_table('routing_rules')
    op.drop_table('conversation_events')
    op.drop_constraint('fk_agent_messages_conversation', 'agent_messages', type_='foreignkey')
    op.drop_table('agent_conversations')
    op.drop_table('task_dependencies')
    op.drop_table('dynamic_tasks')
    op.drop_table('coherence_metrics')
    op.drop_table('feedback')
    op.drop_table('agent_messages')
    op.drop_table('workflow_branches')
    op.drop_table('task_executions')
    op.drop_table('webhooks')
    op.drop_table('integrations')
    op.drop_table('tasks')
    op.drop_table('learning_insights')
    op.drop_table('projects')
    op.drop_table('squad_templates')
    op.drop_table('squad_member_stats')
    op.drop_table('squad_members')
    op.drop_table('squads')
    op.drop_table('usage_metrics')
    op.drop_table('subscriptions')
    op.drop_table('organizations')
    op.drop_table('users')
