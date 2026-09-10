"""add version columns for optimistic concurrency checks

Revision ID: a1b2c3d4e5f6
Revises: 81ad433473f7
Create Date: 2026-09-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "81ad433473f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "payments",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "subscriptions",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.alter_column("payments", "version", server_default=None)
    op.alter_column("subscriptions", "version", server_default=None)


def downgrade() -> None:
    op.drop_column("payments", "version")
    op.drop_column("subscriptions", "version")
