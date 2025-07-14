from rest_framework import serializers


class AdditionalInfoSerializer(serializers.Serializer):
    """Additional context information for company disambiguation."""

    location = serializers.CharField(
        max_length=255,
        required=False,
        help_text="Company location (e.g., 'San Francisco, CA')",
    )
    industry = serializers.CharField(
        max_length=100,
        required=False,
        help_text="Industry sector (e.g., 'Technology', 'Finance')",
    )


class MetadataSerializer(serializers.Serializer):
    """Company metadata from discovery."""

    website = serializers.URLField(required=False, help_text="Company website URL")
    linkedin = serializers.URLField(required=False, help_text="LinkedIn company page")
    summary = serializers.CharField(required=False, help_text="Company description")
    location = serializers.CharField(required=False, help_text="Company location")
    industry = serializers.CharField(required=False, help_text="Industry sector")
    employee_count = serializers.CharField(
        required=False, help_text="Employee count range"
    )
    founded = serializers.CharField(required=False, help_text="Founded year")


class DiscoveryRequestSerializer(serializers.Serializer):
    """Request for company domain discovery."""

    company_query = serializers.CharField(
        max_length=255, help_text="Company name to search for"
    )
    search_level = serializers.ChoiceField(
        choices=[("basic", "Basic"), ("advanced", "Advanced")],
        default="basic",
        help_text="Search level: basic (Gemini) or advanced (paid APIs)",
    )
    additional_info = AdditionalInfoSerializer(
        required=False, help_text="Optional context for disambiguation"
    )
    force_refresh = serializers.BooleanField(
        default=False, help_text="Force refresh even if cached data exists"
    )


class DomainSerializer(serializers.Serializer):
    """Email domain with confidence score."""

    domain = serializers.CharField(help_text="Email domain (e.g., 'company.com')")
    confidence = serializers.FloatField(help_text="Confidence score (0.0-1.0)")
    source = serializers.CharField(help_text="Discovery source")


class PatternSerializer(serializers.Serializer):
    """Email pattern with confidence and verification."""

    domain = serializers.CharField(help_text="Associated domain")
    pattern = serializers.CharField(help_text="Email pattern (e.g., 'first.last')")
    confidence = serializers.FloatField(help_text="Confidence score (0.0-1.0)")
    source = serializers.CharField(help_text="Discovery source")
    verified_count = serializers.IntegerField(help_text="Number of verified examples")


class EmailSerializer(serializers.Serializer):
    """Known public email address."""

    email = serializers.EmailField(help_text="Email address")
    source = serializers.CharField(help_text="Where the email was found")
    confidence = serializers.FloatField(help_text="Confidence score (0.0-1.0)")


class CompanySerializer(serializers.Serializer):
    """Company discovery result."""

    id = serializers.IntegerField(read_only=True, help_text="Company ID")
    name = serializers.CharField(help_text="Company name")
    email_domains = DomainSerializer(many=True, help_text="Email domains")
    email_patterns = PatternSerializer(many=True, help_text="Email patterns")
    known_emails = EmailSerializer(many=True, help_text="Known public emails")
    search_aliases = serializers.ListField(
        child=serializers.CharField(), help_text="Alternative names for this company"
    )
    metadata = MetadataSerializer(help_text="Company metadata")
    search_level = serializers.CharField(help_text="Search level used")
    additional_info = AdditionalInfoSerializer(help_text="Context provided")
    cache_expires_at = serializers.DateTimeField(
        read_only=True, help_text="Cache expiration"
    )
    last_validated_at = serializers.DateTimeField(
        read_only=True, help_text="Last validation"
    )
    created_at = serializers.DateTimeField(
        read_only=True, help_text="Created timestamp"
    )
    updated_at = serializers.DateTimeField(
        read_only=True, help_text="Updated timestamp"
    )

    # Computed fields
    is_cached = serializers.SerializerMethodField(
        help_text="Whether result came from cache"
    )
    best_domain = serializers.SerializerMethodField(
        help_text="Best domain for this company"
    )
    best_patterns = serializers.SerializerMethodField(
        help_text="Top 3 patterns for this company"
    )

    def get_is_cached(self, obj) -> bool:
        """Check if result came from cache."""
        return hasattr(obj, "_from_cache") and obj._from_cache

    def get_best_domain(self, obj) -> dict:
        """Get the best domain for this company."""
        best_domains = obj.get_best_domains(limit=1)
        return best_domains[0] if best_domains else None

    def get_best_patterns(self, obj) -> list:
        """Get the best patterns for this company."""
        return obj.get_best_patterns(limit=3)


class DiscoveryResponseSerializer(serializers.Serializer):
    """Response from company domain discovery."""

    companies = CompanySerializer(many=True, help_text="Discovered companies")
    total_found = serializers.IntegerField(help_text="Total companies found")
    search_level = serializers.CharField(help_text="Search level used")
    from_cache = serializers.BooleanField(
        help_text="Whether any results came from cache"
    )
    query_time_ms = serializers.IntegerField(
        help_text="Query processing time in milliseconds"
    )
