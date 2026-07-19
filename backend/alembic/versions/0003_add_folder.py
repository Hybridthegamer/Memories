"""add folder label to files

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-19

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("files", sa.Column("folder", sa.String(length=60), nullable=True))
    op.create_index("idx_files_folder", "files", ["folder"])


def downgrade() -> None:
    op.drop_index("idx_files_folder", table_name="files")
    op.drop_column("files", "folder")
