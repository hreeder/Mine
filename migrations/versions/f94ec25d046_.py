"""empty message

Revision ID: f94ec25d046
Revises: 2e8bc3267636
Create Date: 2015-07-26 15:20:39.743494

"""

# revision identifiers, used by Alembic.
revision = 'f94ec25d046'
down_revision = '2e8bc3267636'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entry', sa.Column('url', sa.String(length=256), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('entry', 'url')
    ### end Alembic commands ###
