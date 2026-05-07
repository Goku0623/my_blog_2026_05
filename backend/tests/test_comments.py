import pytest
from httpx import AsyncClient

from app.modules.comments.models import Comment


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
        status=Comment.STATUS_PENDING,
        ip_address="127.0.0.1",
    )

    action_resp = await client.post(
        f"/api/v1/admin/comments/{comment.id}/action",
        json={"action": "approve"},
        headers=auth_headers,
    )
    assert action_resp.status_code == 200
    assert action_resp.json()["data"]["status"] == "approved"

    reply_resp = await client.post(
        f"/api/v1/admin/comments/{comment.id}/reply",
        json={"content": "handled by admin"},
        headers=auth_headers,
    )
    assert reply_resp.status_code == 200
    assert reply_resp.json()["data"]["admin_reply"] == "handled by admin"
