import pytest
from httpx import AsyncClient

from tests.conftest import FakeUser, TestMediaData
from app.dependencies import get_current_active_user
from app.main import app


class TestAdmin:

    # ==================== AUTHORIZATION / SECURITY ====================

    async def test_non_admin_cannot_list_users(self, authenticated_client: AsyncClient):
        """Regular users should be blocked from admin routes."""
        response = await authenticated_client.get("/api/v1/admin/users")
        assert response.status_code == 403

    async def test_unauthenticated_user_cannot_access_admin(self, client: AsyncClient):
        """Unauthenticated users should get 401."""
        response = await client.get("/api/v1/admin/users")
        assert response.status_code == 401

    # ==================== USER MANAGEMENT ====================

    async def test_admin_can_list_all_users(self, admin_client: AsyncClient):
        response = await admin_client.get("/api/v1/admin/users")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_admin_can_get_user_by_id(self, admin_client: AsyncClient, test_user):
        response = await admin_client.get(f"/api/v1/admin/users/{test_user.id}")
        assert response.status_code == 200
        assert response.json()["id"] == test_user.id

    async def test_admin_get_nonexistent_user_returns_404(self, admin_client: AsyncClient):
        response = await admin_client.get("/api/v1/admin/users/999999")
        assert response.status_code == 404

    async def test_admin_can_promote_user(self, admin_client: AsyncClient, test_user):
        response = await admin_client.post(f"/api/v1/admin/users/{test_user.id}/promote")
        assert response.status_code == 200
        assert "promoted to admin" in response.json()["message"].lower()

    async def test_admin_cannot_promote_already_admin(self, admin_client: AsyncClient, test_admin):
        response = await admin_client.post(f"/api/v1/admin/users/{test_admin.id}/promote")
        assert response.status_code == 400

    async def test_admin_can_demote_user(self, admin_client: AsyncClient, test_user):
        # First promote them
        await admin_client.post(f"/api/v1/admin/users/{test_user.id}/promote")

        # Then demote
        response = await admin_client.post(f"/api/v1/admin/users/{test_user.id}/demote")
        assert response.status_code == 200
        assert "demoted" in response.json()["message"].lower()

    async def test_admin_cannot_demote_non_admin(self, admin_client: AsyncClient, test_user):
        response = await admin_client.post(f"/api/v1/admin/users/{test_user.id}/demote")
        assert response.status_code == 400

    async def test_admin_can_delete_user(self, admin_client: AsyncClient, test_user):
        response = await admin_client.delete(f"/api/v1/admin/users/{test_user.id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    # ==================== ADMIN COMMENT HARD DELETE ====================
    async def test_admin_can_hard_delete_comment_and_replies(
        self, admin_client: AsyncClient, test_media: TestMediaData
    ):
        """Admin can hard delete a comment thread (including replies)."""

        # Create a parent comment + reply using the admin client
        parent_resp = await admin_client.post("/api/v1/comments/", json={
            "content": "Parent comment for deletion test",
            "media_id": test_media.id,
            "parent_id": None
        })
        assert parent_resp.status_code == 201
        parent_id = parent_resp.json()["id"]

        # Create a reply
        reply_resp = await admin_client.post("/api/v1/comments/", json={
            "content": "Child reply",
            "media_id": test_media.id,
            "parent_id": parent_id
        })
        assert reply_resp.status_code == 201

        # Admin hard deletes the entire thread
        delete_resp = await admin_client.delete(f"/api/v1/admin/comments/{parent_id}")
        assert delete_resp.status_code == 200
        assert "permanently deleted" in delete_resp.json()["message"].lower()