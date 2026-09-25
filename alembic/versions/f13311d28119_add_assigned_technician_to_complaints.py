"""add assigned technician to complaints

Revision ID: f13311d28119
Revises: dda85b8e7a22
Create Date: 2026-09-24 11:04:36.685428

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f13311d28119"
down_revision: Union[str, Sequence[str], None] = "dda85b8e7a22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "complaints",
        sa.Column(
            "assigned_technician_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_complaints_assigned_technician_id"),
        "complaints",
        ["assigned_technician_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_complaints_assigned_technician",
        "complaints",
        "technicians",
        ["assigned_technician_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_complaints_assigned_technician",
        "complaints",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_complaints_assigned_technician_id"),
        table_name="complaints",
    )

    op.drop_column(
        "complaints",
        "assigned_technician_id",
    )
