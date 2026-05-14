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
    "cover_image" TEXT,
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
CREATE TABLE IF NOT EXISTS "article_draft_links" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "draft_article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "source_article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_article_dra_source__870ceb" UNIQUE ("source_article_id", "draft_article_id")
);
CREATE TABLE IF NOT EXISTS "article_views" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "ip_address" VARCHAR(50) NOT NULL,
    "user_agent" TEXT,
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
    "status" VARCHAR(20) NOT NULL DEFAULT 'approved',
    "is_pinned" BOOL NOT NULL DEFAULT False,
    "admin_reply" TEXT,
    "ip_address" VARCHAR(50) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE,
    "guest_id" INT NOT NULL REFERENCES "guest_identities" ("id") ON DELETE CASCADE,
    "parent_id" INT REFERENCES "comments" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "guestbook_messages" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "content" TEXT NOT NULL,
    "rendered_content" TEXT,
    "status" VARCHAR(20) NOT NULL DEFAULT 'approved',
    "ip_address" VARCHAR(50) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "guest_id" INT NOT NULL REFERENCES "guest_identities" ("id") ON DELETE CASCADE
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
    "BZrM4="
)
