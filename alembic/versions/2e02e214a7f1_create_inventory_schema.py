"""create_inventory_schema

Revision ID: 2e02e214a7f1
Revises: c50160eb550d
Create Date: 2026-06-17 11:38:18.317309

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e02e214a7f1'
down_revision: Union[str, None] = 'c50160eb550d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with open(f"alembic/sql/{revision}/up.sql", encoding="utf-8") as file:
        op.execute(file.read())


def downgrade() -> None:
    with open(f"alembic/sql/{revision}/down.sql", encoding="utf-8") as file:
        op.execute(file.read())