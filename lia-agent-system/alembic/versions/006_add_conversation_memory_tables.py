"""Add conversation memory tables.

Revision ID: 006_add_conversation_memory
Revises: 005_add_affirmative_action
Create Date: 2026-01-30

This migration creates tables for persistent conversation memory:
- conversations: Main conversation threads
- messages: Individual messages in conversations
- conversation_summaries: Periodic summaries for context management
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON


revision = '006_add_conversation_memory'
down_revision = '005_add_affirmative_action'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'conversations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('user_role', sa.String(50), server_default='recruiter'),
        sa.Column('session_id', sa.String(255), nullable=True, index=True),
        sa.Column('context_type', sa.String(50), server_default='general', index=True),
        sa.Column('context_id', sa.String(255), nullable=True, index=True),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('intent', sa.String(100), nullable=True),
        sa.Column('workflow_type', sa.String(100), nullable=True),
        sa.Column('workflow_step', sa.Integer(), server_default='0'),
        sa.Column('workflow_data', JSON(), server_default='{}'),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), index=True),
        sa.Column('is_archived', sa.Boolean(), server_default=sa.false()),
        sa.Column('message_count', sa.Integer(), server_default='0'),
        sa.Column('last_summary_at_count', sa.Integer(), server_default='0'),
        sa.Column('conversation_metadata', JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('intent', sa.String(100), nullable=True),
        sa.Column('tool_calls', JSON(), nullable=True),
        sa.Column('message_metadata', JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), index=True),
    )

    op.create_table(
        'conversation_summaries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('message_count', sa.Integer(), server_default='0'),
        sa.Column('messages_start_id', UUID(as_uuid=True), nullable=True),
        sa.Column('messages_end_id', UUID(as_uuid=True), nullable=True),
        sa.Column('key_entities', JSON(), server_default='{}'),
        sa.Column('user_preferences', JSON(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    op.create_index('ix_conversations_user_context', 'conversations', ['user_id', 'context_type', 'context_id'])
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'])


def downgrade():
    op.drop_index('ix_messages_conversation_created', 'messages')
    op.drop_index('ix_conversations_user_context', 'conversations')
    op.drop_table('conversation_summaries')
    op.drop_table('messages')
    op.drop_table('conversations')
