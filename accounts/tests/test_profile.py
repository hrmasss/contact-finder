import pytest
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.tests.conftest import UserFactory
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


User = get_user_model()


@pytest.mark.django_db
class TestUserProfileEndpoints:
    """Test cases for user profile endpoints."""

    def test_get_profile_success(self, authenticated_client, user):
        """Test retrieving profile for authenticated user."""
        user.first_name = "John"
        user.last_name = "Doe"
        user.email = "john.doe@example.com"
        user.save()

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK

        # Check response shape
        data = response.data
        expected_fields = [
            "id",
            "username",
            "email",
            "full_name",
            "image",
            "groups",
            "permissions",
        ]
        for field in expected_fields:
            assert field in data

        # Check values
        assert data["username"] == user.username
        assert data["email"] == "john.doe@example.com"
        assert data["full_name"] == "John Doe"
        assert isinstance(data["groups"], list)
        assert isinstance(data["permissions"], list)

    def test_get_profile_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot access profile."""
        url = reverse("user-profile")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_full_name_fallback(self, authenticated_client, user):
        """Test that full_name falls back to username in title case when names are empty."""
        user.first_name = ""
        user.last_name = ""
        user.save()

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == user.username.title()

    def test_get_profile_superuser_permissions(self, authenticated_client):
        """Test that superuser gets wildcard permissions."""
        superuser = UserFactory(is_superuser=True)
        authenticated_client.force_authenticate(user=superuser)

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["permissions"] == ["*"]

    def test_get_profile_user_with_groups(self, authenticated_client, user):
        """Test that user groups are included in response."""
        group = Group.objects.create(name="Test Group")
        user.groups.add(group)

        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "Test Group" in response.data["groups"]

    def test_update_profile_success(self, authenticated_client, user):
        """Test successful profile update."""
        url = reverse("user-profile-update")
        data = {"first_name": "Jane", "last_name": "Smith"}
        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Jane Smith"

        # Verify user was actually updated
        user.refresh_from_db()
        assert user.first_name == "Jane"
        assert user.last_name == "Smith"

    def test_update_profile_partial(self, authenticated_client, user):
        """Test partial profile update."""
        user.first_name = "John"
        user.last_name = "Doe"
        user.save()

        url = reverse("user-profile-update")
        data = {"first_name": "Jane"}
        response = authenticated_client.patch(url, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["full_name"] == "Jane Doe"  # Last name unchanged

    def test_update_profile_unauthenticated(self, api_client):
        """Test that unauthenticated users cannot update profile."""
        url = reverse("user-profile-update")
        data = {"first_name": "Jane"}
        response = api_client.patch(url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_only_patch_allowed(self, authenticated_client):
        """Test that only PATCH method is allowed for profile update."""
        url = reverse("user-profile-update")
        data = {"first_name": "Jane"}

        # PUT should not be allowed
        response = authenticated_client.put(url, data)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_profile_response_structure(self, authenticated_client, user):
        """Test the exact structure of profile response."""
        url = reverse("user-profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        data = response.data

        # Check all required fields are present
        required_fields = [
            "id",
            "username",
            "email",
            "full_name",
            "image",
            "groups",
            "permissions",
        ]
        for field in required_fields:
            assert field in data

        # Check data types
        assert isinstance(data["id"], int)
        assert isinstance(data["username"], str)
        assert isinstance(data["email"], str)
        assert isinstance(data["full_name"], str)
        assert isinstance(data["groups"], list)
        assert isinstance(data["permissions"], list)
