"""notifications de mention

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-10 16:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('comment_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'comment_id', name='uq_notifications_user_comment')
    )
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_index('ix_notifications_user', ['user_id', 'read_at'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index('ix_notifications_user')

    op.drop_table('notifications')
