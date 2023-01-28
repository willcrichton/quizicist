"""Add content type to generation

Revision ID: 3cdfbfffba69
Revises: 
Create Date: 2023-01-17 17:04:19.179944

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3cdfbfffba69'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('generation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content_type', sa.String(length=10), nullable=False, server_default="Markdown"))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('generation', schema=None) as batch_op:
        batch_op.drop_column('content_type')

    # ### end Alembic commands ###