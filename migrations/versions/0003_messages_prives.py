"""messages privés

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-14 10:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_seen_at', sa.DateTime(), nullable=True))

    op.create_table('conversations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('is_group', sa.Boolean(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=True),
    sa.Column('direct_key', sa.String(length=40), nullable=True),
    sa.Column('creator_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('(is_group = 1 AND name IS NOT NULL AND direct_key IS NULL) OR (is_group = 0 AND name IS NULL AND direct_key IS NOT NULL)', name='ck_conversations_kind'),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('direct_key')
    )
    op.create_table('conversation_members',
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(), nullable=False),
    sa.Column('last_read_message_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('conversation_id', 'user_id')
    )
    with op.batch_alter_table('conversation_members', schema=None) as batch_op:
        batch_op.create_index('ix_conversation_members_user', ['user_id'], unique=False)

    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('image_path', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.CheckConstraint('length(content) <= 1000 AND (length(trim(content)) > 0 OR image_path IS NOT NULL)', name='ck_messages_content'),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.create_index('ix_messages_conversation', ['conversation_id', 'id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('messages', schema=None) as batch_op:
        batch_op.drop_index('ix_messages_conversation')

    op.drop_table('messages')
    with op.batch_alter_table('conversation_members', schema=None) as batch_op:
        batch_op.drop_index('ix_conversation_members_user')

    op.drop_table('conversation_members')
    op.drop_table('conversations')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_seen_at')
