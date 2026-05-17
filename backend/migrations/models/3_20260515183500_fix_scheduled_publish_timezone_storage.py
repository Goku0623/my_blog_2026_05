from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "articles"
        ALTER COLUMN "scheduled_publish_at" TYPE TIMESTAMP
        USING ("scheduled_publish_at" AT TIME ZONE 'Asia/Shanghai');
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "articles"
        ALTER COLUMN "scheduled_publish_at" TYPE TIMESTAMPTZ
        USING ("scheduled_publish_at" AT TIME ZONE 'Asia/Shanghai');
    """

