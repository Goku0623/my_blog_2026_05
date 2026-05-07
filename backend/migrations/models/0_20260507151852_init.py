from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "admin_users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "last_login_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_admin_users_usernam_5ac102" ON "admin_users" ("username");
CREATE INDEX IF NOT EXISTS "idx_admin_users_email_a5cbe4" ON "admin_users" ("email");
CREATE TABLE IF NOT EXISTS "login_attempts" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "ip_address" VARCHAR(50) NOT NULL,
    "username_tried" VARCHAR(50) NOT NULL,
    "success" BOOL NOT NULL DEFAULT False,
    "attempted_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "token_blacklist" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "jti" VARCHAR(255) NOT NULL UNIQUE,
    "token_type" VARCHAR(20) NOT NULL,
    "expired_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_token_black_jti_6fe842" ON "token_blacklist" ("jti");
CREATE TABLE IF NOT EXISTS "categories" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT,
    "sort_order" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "articles" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "title" VARCHAR(200) NOT NULL,
    "slug" VARCHAR(200) NOT NULL UNIQUE,
    "summary" TEXT,
    "content" TEXT NOT NULL,
    "rendered_content" TEXT,
    "status" VARCHAR(20) NOT NULL DEFAULT 'draft',
    "cover_image" VARCHAR(255),
    "view_count" INT NOT NULL DEFAULT 0,
    "is_featured" BOOL NOT NULL DEFAULT False,
    "allow_comment" BOOL NOT NULL DEFAULT True,
    "seo_title" VARCHAR(200),
    "seo_description" VARCHAR(500),
    "seo_keywords" VARCHAR(200),
    "published_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "category_id" INT REFERENCES "categories" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_articles_slug_e59363" ON "articles" ("slug");
CREATE INDEX IF NOT EXISTS "idx_articles_status_40db49" ON "articles" ("status", "published_at");
CREATE TABLE IF NOT EXISTS "article_views" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "ip_address" VARCHAR(50) NOT NULL,
    "user_agent" VARCHAR(255),
    "viewed_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "tags" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(50) NOT NULL UNIQUE,
    "slug" VARCHAR(50) NOT NULL UNIQUE,
    "color" VARCHAR(20),
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "article_tags" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "tag_id" INT NOT NULL REFERENCES "tags" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_article_tag_article_53c588" UNIQUE ("article_id", "tag_id")
);
CREATE TABLE IF NOT EXISTS "guest_identities" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "guest_token" VARCHAR(255) NOT NULL UNIQUE,
    "nickname" VARCHAR(50) UNIQUE,
    "ip_address" VARCHAR(50) NOT NULL,
    "user_agent" VARCHAR(255),
    "is_banned" BOOL NOT NULL DEFAULT False,
    "ban_reason" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_guest_ident_guest_t_21a447" ON "guest_identities" ("guest_token");
CREATE TABLE IF NOT EXISTS "comments" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "reply_to_nickname" VARCHAR(50),
    "content" TEXT NOT NULL,
    "rendered_content" TEXT,
    "status" VARCHAR(20) NOT NULL DEFAULT 'pending',
    "is_pinned" BOOL NOT NULL DEFAULT False,
    "admin_reply" TEXT,
    "ip_address" VARCHAR(50) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "guest_id" INT NOT NULL REFERENCES "guest_identities" ("id") ON DELETE CASCADE,
    "parent_id" INT REFERENCES "comments" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "chat_bans" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "reason" TEXT NOT NULL,
    "banned_by" VARCHAR(50) NOT NULL,
    "ban_expires_at" TIMESTAMPTZ,
    "is_permanent" BOOL NOT NULL DEFAULT False,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "guest_id" INT NOT NULL REFERENCES "guest_identities" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "chat_messages" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "sender_nickname" VARCHAR(50) NOT NULL,
    "message_type" VARCHAR(20) NOT NULL DEFAULT 'text',
    "content" TEXT NOT NULL,
    "is_recalled" BOOL NOT NULL DEFAULT False,
    "recalled_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "guest_id" INT REFERENCES "guest_identities" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "operation_logs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "operator" VARCHAR(50) NOT NULL,
    "action" VARCHAR(100) NOT NULL,
    "target_type" VARCHAR(50),
    "target_id" INT,
    "detail" TEXT,
    "ip_address" VARCHAR(50) NOT NULL,
    "result" VARCHAR(20) NOT NULL DEFAULT 'success',
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "scheduled_tasks" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "task_path" VARCHAR(200) NOT NULL,
    "cron_expression" VARCHAR(100) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "last_run_at" TIMESTAMPTZ,
    "next_run_at" TIMESTAMPTZ,
    "last_result" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "sensitive_words" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "word" VARCHAR(100) NOT NULL UNIQUE,
    "category" VARCHAR(50),
    "is_active" BOOL NOT NULL DEFAULT True,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "site_configs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "key" VARCHAR(100) NOT NULL UNIQUE,
    "value" TEXT NOT NULL,
    "value_type" VARCHAR(20) NOT NULL DEFAULT 'str',
    "description" TEXT,
    "is_public" BOOL NOT NULL DEFAULT False,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS "idx_site_config_key_186b69" ON "site_configs" ("key");
CREATE TABLE IF NOT EXISTS "api_call_logs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "endpoint" VARCHAR(200) NOT NULL,
    "method" VARCHAR(10) NOT NULL,
    "status_code" INT NOT NULL,
    "response_time_ms" INT NOT NULL,
    "ip_address" VARCHAR(50) NOT NULL,
    "error_message" TEXT,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "daily_stats" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "stat_date" DATE NOT NULL UNIQUE,
    "new_articles" INT NOT NULL DEFAULT 0,
    "total_views" INT NOT NULL DEFAULT 0,
    "new_comments" INT NOT NULL DEFAULT 0,
    "unique_visitors" INT NOT NULL DEFAULT 0,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
