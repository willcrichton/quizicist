"""Add timestamps and export model.

Revision ID: 1d7661406625
Revises: 3cdfbfffba69
Create Date: 2023-01-28 10:41:57.557274

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d7661406625'
down_revision = '3cdfbfffba69'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('export',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('generation_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('export_type', sa.Enum('google_forms', 'mdbook', 'plain_text', name='exporttypes'), nullable=True),
    sa.Column('google_form_id', sa.String(length=200), nullable=True),
    sa.ForeignKeyConstraint(['generation_id'], ['generation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('generation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    with op.batch_alter_table('generation', schema=None) as batch_op:
        batch_op.drop_column('created_at')

    op.drop_table('export')
    # ### end Alembic commands ###
