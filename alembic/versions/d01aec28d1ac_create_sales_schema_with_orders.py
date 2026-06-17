"""create sales schema with orders

Revision ID: d01aec28d1ac
Revises: adcaa5ab66c1
Create Date: 2026-06-17 07:42:39.158307

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd01aec28d1ac'
down_revision: Union[str, None] = 'adcaa5ab66c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with open(f"alembic/sql/{revision}/up.sql") as file:
        op.execute(file.read())


def downgrade() -> None:
    with open(f"alembic/sql/{revision}/down.sql") as file:
        op.execute(file.read())