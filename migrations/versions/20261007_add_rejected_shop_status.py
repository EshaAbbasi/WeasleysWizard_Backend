from alembic import op


revision = "20261007_rejected"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'shop_status') THEN
                EXECUTE 'ALTER TYPE shop_status ADD VALUE IF NOT EXISTS ''rejected''';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("UPDATE shops SET status = 'pending' WHERE status = 'rejected'")
    op.execute("ALTER TABLE shops ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE shop_status RENAME TO shop_status_old")
    op.execute("CREATE TYPE shop_status AS ENUM ('pending', 'approved', 'suspended')")
    op.execute(
        "ALTER TABLE shops ALTER COLUMN status TYPE shop_status "
        "USING status::text::shop_status"
    )
    op.execute("ALTER TABLE shops ALTER COLUMN status SET DEFAULT 'pending'::shop_status")
    op.execute("DROP TYPE shop_status_old")