from httpx import AsyncClient
from tests.conftest import TestUserData


class TestAuth:

    # ==================== POSITIVE CASES ====================

    async def test_register_user_success(self, client: AsyncClient):
        payload = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "securepassword123"
        }
        response = await client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 201

    async def test_login_success(self, client: AsyncClient, test_user: TestUserData):
        form_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        response = await client.post("/api/v1/users/token", data=form_data)
        assert response.status_code == 200

    # ==================== NEGATIVE / VALIDATION CASES ====================

    async def test_register_duplicate_email_fails(self, client: AsyncClient, test_user: TestUserData):
        payload = {
            "email": test_user.email,
            "username": "differentusername",
            "password": "password123"
        }
        response = await client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 400

    async def test_register_duplicate_username_fails(self, client: AsyncClient, test_user: TestUserData):
        payload = {
            "email": "different@example.com",
            "username": test_user.username,
            "password": "password123"
        }
        response = await client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 400

    async def test_login_wrong_password(self, client: AsyncClient, test_user: TestUserData):
        form_data = {
            "username": test_user.username,
            "password": "wrongpassword"
        }
        response = await client.post("/api/v1/users/token", data=form_data)
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        form_data = {
            "username": "nonexistentuser123",
            "password": "somepassword"
        }
        response = await client.post("/api/v1/users/token", data=form_data)
        assert response.status_code == 401

    async def test_get_profile_without_token_fails(self, client: AsyncClient):
        response = await client.get("/api/v1/users/profile")
        assert response.status_code == 401

    async def test_register_with_missing_fields(self, client: AsyncClient):
        """Pydantic should reject incomplete payloads."""
        payload = {
            "email": "incomplete@example.com"
            # missing username and password
        }
        response = await client.post("/api/v1/users/register", json=payload)
        assert response.status_code == 422