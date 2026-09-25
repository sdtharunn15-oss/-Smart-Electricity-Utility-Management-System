"""merge migration heads

Revision ID: 9fbd7d3be3f9
Revises: 9580c80f29f6, f13311d28119
Create Date: 2026-09-24 11:13:08.324109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fbd7d3be3f9'
down_revision: Union[str, Sequence[str], None] = ('9580c80f29f6', 'f13311d28119')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
