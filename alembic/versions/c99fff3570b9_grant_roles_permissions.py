"""grant roles permissions

Revision ID: c99fff3570b9
Revises: d01aec28d1ac
Create Date: 2026-06-17 08:45:45.216352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c99fff3570b9'
down_revision: Union[str, None] = 'd01aec28d1ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with open(f"alembic/sql/{revision}/up.sql") as file:
        op.execute(file.read())


def downgrade() -> None:
    with open(f"alembic/sql/{revision}/down.sql") as file:
        op.execute(file.read())