from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "admin_users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "avatar" TEXT,
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
    "cover_image_thumb" TEXT,
    "cover_image_large" TEXT,
    "view_count" INT NOT NULL DEFAULT 0,
    "is_featured" BOOL NOT NULL DEFAULT False,
    "allow_comment" BOOL NOT NULL DEFAULT True,
    "seo_title" VARCHAR(200),
    "seo_description" VARCHAR(500),
    "seo_keywords" VARCHAR(200),
    "scheduled_publish_at" TIMESTAMPTZ,
    "published_at" TIMESTAMPTZ,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "category_id" INT REFERENCES "categories" ("id") ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS "idx_articles_slug_e59363" ON "articles" ("slug");
CREATE INDEX IF NOT EXISTS "idx_articles_status_40db49" ON "articles" ("status", "published_at");
CREATE INDEX IF NOT EXISTS "idx_articles_status_7c10e8" ON "articles" ("status", "scheduled_publish_at");
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
CREATE INDEX IF NOT EXISTS "idx_admin_notif_type_b6d762" ON "admin_notifications" ("type");
CREATE INDEX IF NOT EXISTS "idx_admin_notif_is_read_20e39b" ON "admin_notifications" ("is_read");
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
    "GMw3+r"
)
