"""notifications de nouveau cadeau

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-18 10:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gift_id', sa.Integer(), nullable=True))
        batch_op.alter_column('comment_id', existing_type=sa.Integer(), nullable=True)
        batch_op.create_foreign_key(
            'fk_notifications_gift_id', 'gifts', ['gift_id'], ['id'], ondelete='CASCADE'
        )
        batch_op.create_unique_constraint('uq_notifications_user_gift', ['user_id', 'gift_id'])
        batch_op.create_check_constraint(
            'ck_notifications_target', '(comment_id IS NULL) <> (gift_id IS NULL)'
        )


def downgrade() -> None:
    op.execute('DELETE FROM notifications WHERE gift_id IS NOT NULL')
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_constraint('ck_notifications_target', type_='check')
        batch_op.drop_constraint('uq_notifications_user_gift', type_='unique')
        batch_op.drop_constraint('fk_notifications_gift_id', type_='foreignkey')
        batch_op.alter_column('comment_id', existing_type=sa.Integer(), nullable=False)
        batch_op.drop_column('gift_id')
