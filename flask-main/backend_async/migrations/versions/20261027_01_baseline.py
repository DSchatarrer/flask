"""Baseline de usuarios/sesiones para BD NUEVA.

Revision ID: 20261027_01
Revises:
Create Date: 2026-10-27
"""
from alembic import op
import sqlalchemy as sa

revision = "20261027_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "usuarios",
        sa.Column("usu", sa.String(255), nullable=False),
        sa.Column("hash_pwd", sa.String(255), nullable=True),
        sa.Column("role", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("usu"),
    )
    op.create_table(
        "sesiones",
        sa.Column("token", sa.String(300), nullable=False),
        sa.Column("usu", sa.String(255), nullable=True),
        sa.Column("exp", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("token"),
    )


def downgrade():
    op.drop_table("sesiones")
    op.drop_table("usuarios")
