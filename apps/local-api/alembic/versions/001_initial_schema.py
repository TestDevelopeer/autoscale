"""Initial schema

Revision ID: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "license_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("license_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(50), server_default="missing"),
        sa.Column("raw_file", sa.Text(), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monotonic_counter", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "drivers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "terminals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("driver_type", sa.String(50), nullable=False),
        sa.Column("config", postgresql.JSONB(), server_default="{}"),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("connection_type", sa.String(50), nullable=False),
        sa.Column("config", postgresql.JSONB(), server_default="{}"),
        sa.Column("alpr_provider", sa.String(50), server_default="demo"),
        sa.Column("roi", postgresql.JSONB(), nullable=True),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "vehicles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plate_raw", sa.String(20), nullable=False),
        sa.Column("plate_normalized", sa.String(20), nullable=False),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_vehicles_plate_normalized", "vehicles", ["plate_normalized"])
    op.create_table(
        "workplaces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("terminal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("terminals.id"), nullable=False),
        sa.Column("alpr_provider", sa.String(50), server_default="demo"),
        sa.Column("min_weight_threshold", sa.Numeric(12, 3), server_default="100"),
        sa.Column("stable_seconds", sa.Numeric(6, 2), server_default="2"),
        sa.Column("max_weight_delta", sa.Numeric(12, 3), server_default="5"),
        sa.Column("auto_confirm", sa.Boolean(), server_default="true"),
        sa.Column("manual_confirm", sa.Boolean(), server_default="false"),
        sa.Column("snapshot_policy", sa.String(50), server_default="on_capture"),
        sa.Column("duplicate_protection_window_sec", sa.Integer(), server_default="60"),
        sa.Column("enabled", sa.Boolean(), server_default="true"),
        sa.Column("is_running", sa.Boolean(), server_default="false"),
        sa.Column("fsm_state", sa.String(50), server_default="IDLE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_table(
        "workplace_cameras",
        sa.Column("workplace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workplaces.id"), primary_key=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id"), primary_key=True),
    )
    op.create_table(
        "weighing_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("workplace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workplaces.id"), nullable=False),
        sa.Column("terminal_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("terminals.id"), nullable=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id"), nullable=True),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("driver_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("drivers.id"), nullable=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vehicles.id"), nullable=True),
        sa.Column("plate_raw", sa.String(20), nullable=True),
        sa.Column("plate_normalized", sa.String(20), nullable=True),
        sa.Column("weight", sa.Numeric(12, 3), nullable=True),
        sa.Column("unit", sa.String(10), server_default="kg"),
        sa.Column("stable", sa.Boolean(), server_default="false"),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column("fsm_state", sa.String(50), nullable=True),
        sa.Column("terminal_raw", sa.Text(), nullable=True),
        sa.Column("plate_alternatives", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_weighing_records_plate_normalized", "weighing_records", ["plate_normalized"])
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.String(50), nullable=True),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("weighing_records")
    op.drop_table("workplace_cameras")
    op.drop_table("workplaces")
    op.drop_table("vehicles")
    op.drop_table("cameras")
    op.drop_table("terminals")
    op.drop_table("drivers")
    op.drop_table("license_state")
    op.drop_table("users")
