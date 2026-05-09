import pytest
from httpx import AsyncClient

from app.modules.comments.models import Comment
from app.modules.system.models import SensitiveWord


@pytest.mark.asyncio
async def test_guest_identity_and_set_nickname(client: AsyncClient):
    identity_resp = await client.get("/api/v1/guest/identity")
    assert identity_resp.status_code == 200
    token = identity_resp.json()["data"]["guest_token"]
    assert token

    client.cookies.set("guest_token", token)
    nickname_resp = await client.put(
        "/api/v1/guest/nickname",
        json={"nickname": "guest_one"},
    )
    assert nickname_resp.status_code == 200
    assert nickname_resp.json()["data"]["nickname"] == "guest_one"


@pytest.mark.asyncio
async def test_create_comment_and_list_article_comments(client: AsyncClient, create_article, create_guest):
    article = await create_article(
        title="Comment Target",
        slug="comment-target",
        content="content",
        status="published",
        allow_comment=True,
    )
    guest = await create_guest(
        guest_token="guest_for_comment",
        nickname="commenter",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    client.cookies.set("guest_token", guest.guest_token)
    create_resp = await client.post(
        "/api/v1/comments",
        json={"article_id": article.id, "content": "first comment"},
    )
    assert create_resp.status_code == 200
    assert create_resp.json()["code"] == 0

    list_resp = await client.get(f"/api/v1/articles/{article.id}/comments")
    assert list_resp.status_code == 200
    assert list_resp.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_admin_comment_action_and_reply(
    client: AsyncClient, auth_headers: dict, create_article, create_guest
):
    article = await create_article(
        title="Admin Comment Target",
        slug="admin-comment-target",
        content="content",
        status="published",
        allow_comment=True,
    )
    guest = await create_guest(
        guest_token="guest_for_admin_comment",
        nickname="admin_target",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    comment = await Comment.create(
        article=article,
        guest=guest,
        content="need admin action",
        rendered_content="<p>need admin action</p>",
        status=Comment.STATUS_APPROVED,
        ip_address="127.0.0.1",
    )

    action_resp = await client.post(
        f"/api/v1/admin/comments/{comment.id}/action",
        json={"action": "hide"},
        headers=auth_headers,
    )
    assert action_resp.status_code == 200
    assert action_resp.json()["data"]["status"] == Comment.STATUS_HIDDEN

    reply_resp = await client.post(
        f"/api/v1/admin/comments/{comment.id}/reply",
        json={"content": "handled by admin"},
        headers=auth_headers,
    )
    assert reply_resp.status_code == 200
    assert reply_resp.json()["data"]["admin_reply"] == "handled by admin"


@pytest.mark.asyncio
async def test_sensitive_words_should_block_comment(
    client: AsyncClient, create_article, create_guest
):
    article = await create_article(
        title="Sensitive Word Target",
        slug="sensitive-word-target",
        content="content",
        status="published",
        allow_comment=True,
    )
    guest = await create_guest(
        guest_token="guest_for_sensitive_word",
        nickname="sensitive_user",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    await SensitiveWord.create(word="违禁词", category="test", is_active=True)

    client.cookies.set("guest_token", guest.guest_token)
    resp = await client.post(
        "/api/v1/comments",
        json={"article_id": article.id, "content": "这条评论包含违禁词"},
    )
    assert resp.status_code == 400
    assert "内容包含敏感词" in resp.json()["message"]


@pytest.mark.asyncio
async def test_comment_should_always_be_approved(
    client: AsyncClient, create_article, create_guest
):
    article = await create_article(
        title="Need Review Target",
        slug="need-review-target",
        content="content",
        status="published",
        allow_comment=True,
    )
    guest = await create_guest(
        guest_token="guest_need_review",
        nickname="review_user",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    client.cookies.set("guest_token", guest.guest_token)
    resp = await client.post(
        "/api/v1/comments",
        json={"article_id": article.id, "content": "立即发布的评论"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == Comment.STATUS_APPROVED
