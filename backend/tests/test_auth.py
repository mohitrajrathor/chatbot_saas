import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_api_key,
    generate_api_key,
)


def test_password_hashing_and_verification():
    plain = "MySecretPass123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPass", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = "12345678-1234-5678-1234-567812345678"
    access_token = create_access_token(data={"sub": user_id})
    payload = decode_token(access_token)

    assert payload is not None
    assert payload.get("sub") == user_id
    assert payload.get("type") == "access"

    refresh_token = create_refresh_token(data={"sub": user_id})
    refresh_payload = decode_token(refresh_token)

    assert refresh_payload is not None
    assert refresh_payload.get("sub") == user_id
    assert refresh_payload.get("type") == "refresh"


def test_api_key_generation_and_hashing():
    plaintext, key_hash = generate_api_key()
    assert plaintext.startswith("sk_")
    assert len(key_hash) == 64  # SHA-256 hex string length
    assert hash_api_key(plaintext) == key_hash


@pytest.mark.asyncio
async def test_user_registration_and_login_flow():
    import uuid
    random_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "securePassword123"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register user
        reg_response = await ac.post(
            "/api/v1/auth/register",
            json={"email": random_email, "password": password}
        )
        assert reg_response.status_code == 201
        token_data = reg_response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data

        # Duplicate registration attempt
        dup_response = await ac.post(
            "/api/v1/auth/register",
            json={"email": random_email, "password": password}
        )
        assert dup_response.status_code == 400

        # Login user
        login_response = await ac.post(
            "/api/v1/auth/login",
            json={"email": random_email, "password": password}
        )
        assert login_response.status_code == 200
        login_tokens = login_response.json()
        assert "access_token" in login_tokens

        # Access /me endpoint
        headers = {"Authorization": f"Bearer {login_tokens['access_token']}"}
        me_response = await ac.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == random_email


@pytest.mark.asyncio
async def test_me_unauthorized_without_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/auth/me")
        assert response.status_code == 401
