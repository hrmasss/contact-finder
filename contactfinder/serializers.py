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
    advanced_validation = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Enable advanced email validation (SMTP, external APIs) for more accurate confidence scores (default: False)",
    )


class ContactFinderResponseSerializer(serializers.Serializer):
    """Serializer for contact finder response."""

    # Employee data
    email = serializers.EmailField(
        allow_null=True, help_text="Most likely email address"
    )
    confidence = serializers.FloatField(
        help_text="Confidence score between 0.0 and 1.0"
    )
    candidate_emails = serializers.ListField(
        child=serializers.DictField(),
        help_text="All candidate emails with scores and details",
    )
    additional_info = serializers.DictField(
        help_text="Additional employee information (title, role, location, etc.)"
    )

    # Company data
    company_name = serializers.CharField(help_text="Resolved company name")
    company_summary = serializers.CharField(
        help_text="Brief summary of what the company does"
    )
    primary_domain = serializers.CharField(
        help_text="Primary email domain for the company"
    )
    email_patterns = serializers.ListField(
        child=serializers.DictField(),
        help_text="Company email patterns with confidence scores",
    )
    all_domains = serializers.ListField(
        child=serializers.DictField(),
        help_text="All domains associated with the company",
    )
    known_emails = serializers.ListField(
        child=serializers.DictField(), help_text="Known public emails for the company"
    )

    # Process metadata
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
