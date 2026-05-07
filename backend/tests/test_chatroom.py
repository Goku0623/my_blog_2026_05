import pytest
from httpx import AsyncClient

from app.modules.chatroom.models import ChatMessage


@pytest.mark.asyncio
async def test_get_chatroom_history(client: AsyncClient, create_guest):
    guest = await create_guest(
        guest_token="chat_guest_1",
        nickname="chat_user",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    await ChatMessage.create(
        guest=guest,
        sender_nickname="chat_user",
        message_type="text",
        content="hello chatroom",
    )

    response = await client.get("/api/v1/chatroom/history")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(message["content"] == "hello chatroom" for message in data["messages"])


@pytest.mark.asyncio
async def test_get_chatroom_online(client: AsyncClient, create_guest, fake_redis):
    guest = await create_guest(
        guest_token="chat_guest_online",
        nickname="online_user",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )
    await fake_redis.setex(f"chatroom:online:{guest.guest_token}", 60, "online")

    response = await client.get("/api/v1/chatroom/online")
    assert response.status_code == 200
    data = response.json()
    assert data["online_count"] == 1
    assert data["online_list"][0]["guest_token"] == guest.guest_token


@pytest.mark.asyncio
async def test_admin_chatroom_announcement(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/api/v1/chatroom/admin/chatroom/action",
        json={"action": "announcement", "content": "system notice"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["code"] == 0

    announcement = await ChatMessage.filter(message_type="announcement").first()
    assert announcement is not None
    assert announcement.content == "system notice"
