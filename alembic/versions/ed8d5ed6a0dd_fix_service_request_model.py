"""fix service request model

Revision ID: ed8d5ed6a0dd
Revises: 9fbd7d3be3f9
Create Date: 2026-09-24 11:47:55.816770

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ed8d5ed6a0dd"
down_revision: Union[str, Sequence[str], None] = "9fbd7d3be3f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add request number to service requests.
    op.add_column(
        "service_requests",
        sa.Column(
            "request_number",
            sa.String(length=50),
            nullable=False,
        ),
    )

    op.create_index(
        op.f("ix_service_requests_request_number"),
        "service_requests",
        ["request_number"],
        unique=True,
    )

    # Remove fields no longer used by the ServiceRequest model.
    op.drop_column(
        "service_requests",
        "subject",
    )

    op.drop_column(
        "service_requests",
        "priority",
    )


def downgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
        ),
    )

    op.add_column(
        "service_requests",
        sa.Column(
            "subject",
            sa.String(length=200),
            nullable=False,
        ),
    )

    op.drop_index(
        op.f("ix_service_requests_request_number"),
        table_name="service_requests",
    )

    op.drop_column(
        "service_requests",
        "request_number",
    )