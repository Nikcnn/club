"""payments resilience and idempotency tables

Revision ID: a9d2f7c1e301
Revises: 2f4e7a9b1c22
Create Date: 2026-02-17 18:30:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9d2f7c1e301"
down_revision: Union[str, Sequence[str], None] = "2f4e7a9b1c22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE payment_status RENAME VALUE 'init' TO 'created';")
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'canceled';")
    op.execute("ALTER TYPE payment_status ADD VALUE IF NOT EXISTS 'refunded';")

    op.add_column("payments", sa.Column("idempotency_key", sa.String(length=128), nullable=True))
    op.add_column("payments", sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("payments", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.alter_column("payments", "provider_payment_id", existing_type=sa.String(length=100), type_=sa.String(length=255), nullable=True)
    op.create_index("idx_payment_status_created", "payments", ["status", "created_at"], unique=False)

    op.create_table(
        "payment_idempotency",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("response_code", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "scope", "idempotency_key", name="uq_payment_idempotency_user_scope_key"),
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("signature_valid", sa.Boolean(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(length=64), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Enum("received", "processed", "ignored", "failed", name="webhook_event_status"), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_event_id", name="uq_webhook_provider_event"),
        sa.UniqueConstraint("provider", "payload_hash", name="uq_webhook_provider_hash"),
    )
    op.create_index("idx_webhook_status_received", "webhook_events", ["status", "received_at"], unique=False)

    op.create_table(
        "webhook_delivery_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("webhook_event_id", sa.Integer(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("http_headers", sa.JSON(), nullable=False),
        sa.Column("remote_addr", sa.String(length=64), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["webhook_event_id"], ["webhook_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("webhook_event_id", "attempt_no", name="uq_delivery_attempt"),
    )

    op.create_table(
        "payment_state_transition_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.Enum("created", "pending", "success", "failed", "canceled", "refunded", name="payment_status"), nullable=False),
        sa.Column("to_status", sa.Enum("created", "pending", "success", "failed", "canceled", "refunded", name="payment_status"), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("actor_type", sa.Enum("system", "user", "webhook", name="payment_actor_type"), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_payment_transition_payment_created",
        "payment_state_transition_logs",
        ["payment_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_payment_transition_payment_created", table_name="payment_state_transition_logs")
    op.drop_table("payment_state_transition_logs")
    op.drop_table("webhook_delivery_logs")
    op.drop_index("idx_webhook_status_received", table_name="webhook_events")
    op.drop_table("webhook_events")
    op.drop_table("payment_idempotency")

    op.drop_index("idx_payment_status_created", table_name="payments")
    op.alter_column("payments", "provider_payment_id", existing_type=sa.String(length=255), type_=sa.String(length=100), nullable=False)
    op.drop_column("payments", "version")
    op.drop_column("payments", "last_event_at")
    op.drop_column("payments", "idempotency_key")

    op.execute("DELETE FROM payments WHERE status IN ('canceled', 'refunded');")
    op.execute("UPDATE payments SET status='pending' WHERE status='created';")
