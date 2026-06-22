"""grant_worker_permissions

Revision ID: 663d0e061c71
Revises: 3cef37c581fb
Create Date: 2026-06-17 11:52:51.599339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '663d0e061c71'
down_revision: Union[str, None] = '3cef37c581fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with open(f"alembic/sql/{revision}/up.sql", encoding="utf-8") as file:
        op.execute(file.read())


def downgrade() -> None:
    with open(f"alembic/sql/{revision}/down.sql", encoding="utf-8") as file:
        op.execute(file.read())