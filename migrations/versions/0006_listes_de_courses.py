"""listes de courses

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-18 14:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('shopping_lists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('length(trim(name)) > 0', name='ck_shopping_lists_name'),
    sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('shopping_items',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('list_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('quantity', sa.String(length=30), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=True),
    sa.Column('checked_at', sa.DateTime(), nullable=True),
    sa.Column('checked_by_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint('length(trim(name)) > 0', name='ck_shopping_items_name'),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['checked_by_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['list_id'], ['shopping_lists.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('shopping_items', schema=None) as batch_op:
        batch_op.create_index('ix_shopping_items_list', ['list_id', 'id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('shopping_items', schema=None) as batch_op:
        batch_op.drop_index('ix_shopping_items_list')
    op.drop_table('shopping_items')
    op.drop_table('shopping_lists')
