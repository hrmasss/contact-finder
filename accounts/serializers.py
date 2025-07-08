from accounts.models import User
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field


def get_user_permissions(user):
    """Extract clean permission names for a user."""
    if user.is_superuser:
        return ["*"]

    # Get all user permissions (both user and group permissions)
    all_perms = user.get_all_permissions()

    # Clean permission names - remove app prefix and exclude internal permissions
    cleaned_perms = []
    exclude_apps = {"auth", "admin", "contenttypes", "sessions"}

    for perm in all_perms:
        if "." in perm:
            app_label, perm_name = perm.split(".", 1)
            if app_label not in exclude_apps:
                cleaned_perms.append(perm_name)

    return sorted(list(set(cleaned_perms)))


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data (read-only)."""

    full_name = serializers.SerializerMethodField()
    groups = serializers.StringRelatedField(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "full_name",
            "image",
            "groups",
            "permissions",
        ]
        read_only_fields = [
            "id",
            "username",
            "email",
            "groups",
            "permissions",
        ]

    @extend_schema_field(
        {
            "type": "string",
            "format": "email",
            "nullable": True,
            "title": "Email address",
        }
    )
    def get_email(self, obj):
        return obj.email or None

    @extend_schema_field(
        {
            "type": "string",
            "description": "User's full name or username in title case if full name is blank",
            "example": "John Doe",
        }
    )
    def get_full_name(self, obj) -> str:
        """Return full name or username in title case if full name is blank."""
        full_name = obj.get_full_name().strip()
        if full_name:
            return full_name
        return obj.username.title()

    @extend_schema_field(
        {
            "type": "array",
            "items": {"type": "string"},
            "description": 'User permissions. "*" indicates all permissions (superuser).',
            "example": ["view_order", "add_order"],
        }
    )
    def get_permissions(self, obj):
        """Return clean permission names for the user."""
        return get_user_permissions(obj)


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile (limited fields)."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "image"]

    def validate_image(self, value):
        """Validate image file size and type."""
        if value:
            # Limit file size to 5MB
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file too large ( > 5MB )")

            # Basic file type validation
            if not value.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                raise serializers.ValidationError("Unsupported image format.")

        return value
