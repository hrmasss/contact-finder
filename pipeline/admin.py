from django.contrib import admin
from .models import DiscoveredCompany


@admin.register(DiscoveredCompany)
class DiscoveredCompanyAdmin(admin.ModelAdmin):
    """Admin interface for DiscoveredCompany model."""

    list_display = [
        "name",
        "search_level",
        "last_validated_at",
        "created_at",
        "get_best_domain",
        "get_email_count",
    ]
    list_filter = ["search_level", "created_at", "last_validated_at"]
    search_fields = ["name", "search_aliases"]
    ordering = ["-last_validated_at", "name"]
    readonly_fields = ["created_at", "updated_at", "last_validated_at"]

    fieldsets = [
        (
            "Basic Information",
            {"fields": ["name", "search_aliases"]},
        ),
        (
            "Discovery Context",
            {"fields": ["search_level", "additional_info"]},
        ),
        (
            "Results",
            {"fields": ["email_domains", "email_patterns", "known_emails", "metadata"]},
        ),
        (
            "Cache Management",
            {"fields": ["cache_expires_at", "last_validated_at"]},
        ),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"]},
        ),
    ]

    def get_best_domain(self, obj):
        """Get the best domain for display."""
        best_domains = obj.get_best_domains(limit=1)
        return best_domains[0]["domain"] if best_domains else "No domains"

    get_best_domain.short_description = "Best Domain"

    def get_email_count(self, obj):
        """Get count of known emails."""
        return len(obj.known_emails)

    get_email_count.short_description = "Email Count"
