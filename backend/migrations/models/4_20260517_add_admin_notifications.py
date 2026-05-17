from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "admin_notifications" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "type" VARCHAR(50) NOT NULL,
    "title" VARCHAR(200) NOT NULL,
    "content" TEXT,
    "link" VARCHAR(500),
    "source_id" INT,
    "is_read" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_admin_notifications_type_7de603" ON "admin_notifications" ("type");
CREATE INDEX IF NOT EXISTS "idx_admin_notifications_is_read_b3abf4" ON "admin_notifications" ("is_read");
"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "admin_notifications";
"""
