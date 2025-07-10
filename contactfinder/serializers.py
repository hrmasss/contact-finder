from rest_framework import serializers


class ContactFinderRequestSerializer(serializers.Serializer):
    """Serializer for contact finder request."""

    company_query = serializers.CharField(
        max_length=255, help_text="Company name or identifier"
    )
    person_name = serializers.CharField(
        max_length=255, help_text="Full name of the person"
    )
    use_cache = serializers.BooleanField(
        required=False,
        default=True,
        help_text="Use cached data when available (default: True)",
    )


class ContactFinderResponseSerializer(serializers.Serializer):
    """Serializer for contact finder response."""

    email = serializers.EmailField(
        allow_null=True, help_text="Most likely email address"
    )
    confidence = serializers.FloatField(
        help_text="Confidence score between 0.0 and 1.0"
    )
    pattern_used = serializers.CharField(
        allow_null=True, help_text="Email pattern used"
    )
    alternatives = serializers.ListField(
        child=serializers.EmailField(), help_text="Alternative email candidates"
    )
    reasoning = serializers.CharField(help_text="Step-by-step reasoning trail")
    cache_hit = serializers.CharField(
        help_text="Cache hit level: none, company, employee, both"
    )
    company_name = serializers.CharField(
        help_text="Resolved company name"
    )
    primary_domain = serializers.CharField(
        help_text="Primary email domain for the company"
    )
