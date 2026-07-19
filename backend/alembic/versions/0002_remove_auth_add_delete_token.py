"""remove accounts entirely; add anonymous delete-token column

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("idx_files_owner_id", table_name="files")
    op.drop_constraint("files_owner_id_fkey", "files", type_="foreignkey")
    op.drop_column("files", "owner_id")

    # Existing rows (if any) predate this column and have no real token to
    # backfill — the placeholder default hash can never match a real
    # SHA-256 digest of a provided token, so those rows simply become
    # permanently undeletable via the API, which is the safe default.
    op.add_column(
        "files",
        sa.Column("delete_token_hash", sa.String(), nullable=False, server_default=""),
    )
    op.alter_column("files", "delete_token_hash", server_default=None)

    op.drop_table("users")


def downgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.drop_column("files", "delete_token_hash")

    op.add_column("files", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("files_owner_id_fkey", "files", "users", ["owner_id"], ["id"], ondelete="CASCADE")
    op.create_index("idx_files_owner_id", "files", ["owner_id"])
