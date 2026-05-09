from tortoise import fields
from tortoise.models import Model


class Category(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    slug = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(null=True)
    sort_order = fields.IntField(default=0)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "categories"


class Tag(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=50, unique=True)
    slug = fields.CharField(max_length=50, unique=True)
    color = fields.CharField(max_length=20, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tags"


class Article(Model):
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_UNPUBLISHED = "unpublished"
    
    STATUS_CHOICES = [
        (STATUS_DRAFT, "草稿"),
        (STATUS_PUBLISHED, "已发布"),
        (STATUS_UNPUBLISHED, "已下线"),
    ]

    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True, index=True)
    summary = fields.TextField(null=True)
    content = fields.TextField()
    rendered_content = fields.TextField(null=True)
    status = fields.CharField(max_length=20, default=STATUS_DRAFT)
    category = fields.ForeignKeyField("models.Category", related_name="articles", null=True, on_delete=fields.SET_NULL)
    cover_image = fields.CharField(max_length=255, null=True)
    view_count = fields.IntField(default=0)
    is_featured = fields.BooleanField(default=False)
    allow_comment = fields.BooleanField(default=True)
    seo_title = fields.CharField(max_length=200, null=True)
    seo_description = fields.CharField(max_length=500, null=True)
    seo_keywords = fields.CharField(max_length=200, null=True)
    published_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "articles"
        indexes = [("status", "published_at")]


class ArticleTag(Model):
    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField("models.Article", related_name="article_tags", on_delete=fields.CASCADE)
    tag = fields.ForeignKeyField("models.Tag", related_name="article_tags", on_delete=fields.CASCADE)

    class Meta:
        table = "article_tags"
        unique_together = (("article", "tag"),)


class ArticleView(Model):
    id = fields.IntField(pk=True)
    article = fields.ForeignKeyField("models.Article", related_name="views", on_delete=fields.CASCADE)
    ip_address = fields.CharField(max_length=50)
    user_agent = fields.TextField(null=True)
    viewed_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "article_views"


class ArticleDraftLink(Model):
    id = fields.IntField(pk=True)
    source_article = fields.ForeignKeyField(
        "models.Article",
        related_name="draft_links",
        on_delete=fields.CASCADE,
    )
    draft_article = fields.ForeignKeyField(
        "models.Article",
        related_name="source_links",
        on_delete=fields.CASCADE,
        unique=True,
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "article_draft_links"
        unique_together = (("source_article", "draft_article"),)
