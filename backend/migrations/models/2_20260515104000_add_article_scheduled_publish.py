from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "articles" ADD "scheduled_publish_at" TIMESTAMPTZ;
        CREATE INDEX IF NOT EXISTS "idx_articles_status_scheduled_publish" ON "articles" ("status", "scheduled_publish_at");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP INDEX IF EXISTS "idx_articles_status_scheduled_publish";
        ALTER TABLE "articles" DROP COLUMN "scheduled_publish_at";"""


MODELS_STATE = (
    "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"
    "W6d5efk/c0I8Gg=="
)
