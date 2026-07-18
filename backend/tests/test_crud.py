import io
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


async def _get_auth_headers(ac: AsyncClient, email: str = "crud_user@example.com") -> dict[str, str]:
    password = "password123"
    response = await ac.post("/api/v1/auth/register", json={"email": email, "password": password})
    if response.status_code == 201:
        token = response.json()["access_token"]
    else:
        login_res = await ac.post("/api/v1/auth/login", json={"email": email, "password": password})
        token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_chatbot_crud_operations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await _get_auth_headers(ac, "cb_owner@example.com")

        # 1. Create chatbot
        create_res = await ac.post(
            "/api/v1/chatbots",
            headers=headers,
            json={"name": "Support Bot", "instructions": "Help customers.", "access_type": "public"}
        )
        assert create_res.status_code == 201
        cb_data = create_res.json()
        cb_id = cb_data["id"]
        assert cb_data["name"] == "Support Bot"

        # 2. List chatbots
        list_res = await ac.get("/api/v1/chatbots", headers=headers)
        assert list_res.status_code == 200
        chatbots = list_res.json()
        assert any(c["id"] == cb_id for c in chatbots)

        # 3. Update chatbot
        update_res = await ac.put(
            f"/api/v1/chatbots/{cb_id}",
            headers=headers,
            json={"name": "Updated Support Bot"}
        )
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Updated Support Bot"

        # 4. Ownership enforcement: another user cannot access this chatbot
        other_headers = await _get_auth_headers(ac, "cb_other@example.com")
        other_get = await ac.get(f"/api/v1/chatbots/{cb_id}", headers=other_headers)
        assert other_get.status_code == 404

        # 5. Delete chatbot
        del_res = await ac.delete(f"/api/v1/chatbots/{cb_id}", headers=headers)
        assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_api_key_crud_operations():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await _get_auth_headers(ac, "key_owner@example.com")

        # Create chatbot
        cb_res = await ac.post(
            "/api/v1/chatbots",
            headers=headers,
            json={"name": "Key Bot"}
        )
        cb_id = cb_res.json()["id"]

        # Generate API key
        gen_res = await ac.post(
            f"/api/v1/chatbots/{cb_id}/keys",
            headers=headers,
            json={"key_name": "Development Key"}
        )
        assert gen_res.status_code == 201
        key_data = gen_res.json()
        key_id = key_data["id"]
        assert "plaintext_key" in key_data
        assert key_data["plaintext_key"].startswith("sk_")

        # List API keys (verify plaintext_key is NOT returned on list)
        list_res = await ac.get(f"/api/v1/chatbots/{cb_id}/keys", headers=headers)
        assert list_res.status_code == 200
        keys = list_res.json()
        matching_key = next(k for k in keys if k["id"] == key_id)
        assert matching_key.get("plaintext_key") is None

        # Revoke API key
        revoke_res = await ac.delete(f"/api/v1/chatbots/{cb_id}/keys/{key_id}", headers=headers)
        assert revoke_res.status_code == 204


@pytest.mark.asyncio
async def test_document_upload_and_management():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await _get_auth_headers(ac, "doc_owner@example.com")

        # Create chatbot
        cb_res = await ac.post("/api/v1/chatbots", headers=headers, json={"name": "Doc Bot"})
        cb_id = cb_res.json()["id"]

        # Upload valid text file
        file_content = b"Sample text document for RAG ingestion."
        files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
        up_res = await ac.post(f"/api/v1/chatbots/{cb_id}/documents", headers=headers, files=files)
        assert up_res.status_code == 201
        doc_data = up_res.json()
        doc_id = doc_data["id"]
        assert doc_data["status"] == "pending"

        # List documents
        list_res = await ac.get(f"/api/v1/chatbots/{cb_id}/documents", headers=headers)
        assert list_res.status_code == 200
        assert any(d["id"] == doc_id for d in list_res.json())

        # Delete document
        del_res = await ac.delete(f"/api/v1/chatbots/{cb_id}/documents/{doc_id}", headers=headers)
        assert del_res.status_code == 204
