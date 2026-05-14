from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "articles" ADD "cover_image_large" TEXT;
        ALTER TABLE "articles" ADD "cover_image_thumb" TEXT;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "articles" DROP COLUMN "cover_image_large";
        ALTER TABLE "articles" DROP COLUMN "cover_image_thumb";"""


MODELS_STATE = (
    "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"
)
