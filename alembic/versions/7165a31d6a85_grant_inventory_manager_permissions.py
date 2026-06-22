"""grant_inventory_manager_permissions

Revision ID: 7165a31d6a85
Revises: 2e02e214a7f1
Create Date: 2026-06-17 11:40:48.836906

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7165a31d6a85'
down_revision: Union[str, None] = '2e02e214a7f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with open(f"alembic/sql/{revision}/up.sql", encoding="utf-8") as file:
        op.execute(file.read())


def downgrade() -> None:
    with open(f"alembic/sql/{revision}/down.sql", encoding="utf-8") as file:
        op.execute(file.read())