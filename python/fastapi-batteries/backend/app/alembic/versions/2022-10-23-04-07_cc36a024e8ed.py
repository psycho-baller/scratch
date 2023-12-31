"""empty message

Revision ID: cc36a024e8ed
Revises: 3223652d21bd
Create Date: 2022-10-23 04:07:49.888323

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel  # added


# revision identifiers, used by Alembic.
revision = "cc36a024e8ed"
down_revision = "3223652d21bd"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "UserFollow",
        sa.Column("is_mutual", sa.Boolean(), server_default="0", nullable=True),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("target_user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_UserFollow_id"), "UserFollow", ["id"], unique=False)
    op.add_column(
        "User",
        sa.Column("follower_count", sa.BigInteger(), server_default="0", nullable=True),
    )
    op.add_column(
        "User",
        sa.Column(
            "following_count", sa.BigInteger(), server_default="0", nullable=True
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("User", "following_count")
    op.drop_column("User", "follower_count")
    op.drop_index(op.f("ix_UserFollow_id"), table_name="UserFollow")
    op.drop_table("UserFollow")
    # ### end Alembic commands ###
