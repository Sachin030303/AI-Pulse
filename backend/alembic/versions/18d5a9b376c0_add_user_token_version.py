"""Add user JWT revocation version."""

from alembic import op
import sqlalchemy as sa

revision = '18d5a9b376c0'
down_revision = '2b5889707edc'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade():
    op.drop_column("users", "token_version")
