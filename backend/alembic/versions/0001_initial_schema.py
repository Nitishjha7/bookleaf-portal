"""initial schema

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('admins',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admins_email'), 'admins', ['email'], unique=True)
    op.create_table('authors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author_code', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('joined_date', sa.String(), nullable=True),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_authors_author_code'), 'authors', ['author_code'], unique=True)
    op.create_index(op.f('ix_authors_email'), 'authors', ['email'], unique=True)
    op.create_table('books',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('book_code', sa.String(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('isbn', sa.String(), nullable=True),
    sa.Column('genre', sa.String(), nullable=True),
    sa.Column('publication_date', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('mrp', sa.Float(), nullable=True),
    sa.Column('author_royalty_per_copy', sa.Float(), nullable=True),
    sa.Column('total_copies_sold', sa.Integer(), nullable=True),
    sa.Column('total_royalty_earned', sa.Float(), nullable=True),
    sa.Column('royalty_paid', sa.Float(), nullable=True),
    sa.Column('royalty_pending', sa.Float(), nullable=True),
    sa.Column('last_royalty_payout_date', sa.String(), nullable=True),
    sa.Column('print_partner', sa.String(), nullable=True),
    sa.Column('available_on', sa.JSON(), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_book_code'), 'books', ['book_code'], unique=True)
    op.create_table('tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('book_id', sa.Integer(), nullable=True),
    sa.Column('subject', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.Enum('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', name='ticketstatus'), nullable=False),
    sa.Column('ai_category', sa.Enum('ROYALTY', 'ISBN', 'PRINTING', 'DISTRIBUTION', 'STATUS', 'GENERAL', name='ticketcategory'), nullable=True),
    sa.Column('ai_priority', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='ticketpriority'), nullable=True),
    sa.Column('category', sa.Enum('ROYALTY', 'ISBN', 'PRINTING', 'DISTRIBUTION', 'STATUS', 'GENERAL', name='ticketcategory'), nullable=True),
    sa.Column('priority', sa.Enum('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', name='ticketpriority'), nullable=True),
    sa.Column('category_overridden', sa.Integer(), nullable=True),
    sa.Column('priority_overridden', sa.Integer(), nullable=True),
    sa.Column('ai_classification_note', sa.Text(), nullable=True),
    sa.Column('assigned_admin_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['assigned_admin_id'], ['admins.id'], ),
    sa.ForeignKeyConstraint(['author_id'], ['authors.id'], ),
    sa.ForeignKeyConstraint(['book_id'], ['books.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('internal_notes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
    sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('ticket_responses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=True),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('was_ai_drafted', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
    sa.ForeignKeyConstraint(['ticket_id'], ['tickets.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ticket_responses')
    op.drop_table('internal_notes')
    op.drop_table('tickets')
    op.drop_index(op.f('ix_books_book_code'), table_name='books')
    op.drop_table('books')
    op.drop_index(op.f('ix_authors_email'), table_name='authors')
    op.drop_index(op.f('ix_authors_author_code'), table_name='authors')
    op.drop_table('authors')
    op.drop_index(op.f('ix_admins_email'), table_name='admins')
    op.drop_table('admins')
