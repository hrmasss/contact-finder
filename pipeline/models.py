from django.db import models
from django.utils import timezone
from common.models import BaseModel


class DiscoveredCompany(BaseModel):
    """
    Company model for domain discovery and email pattern caching.

    This model stores the results of domain discovery including:
    - Primary domain for email generation
    - All related domains with confidence scores
    - Email patterns ranked by confidence
    - Publicly found emails for pattern validation
    - Search aliases for cache hit optimization
    """

    name = models.CharField(
        max_length=255, help_text="Primary company name as found/confirmed"
    )

    email_domains = models.JSONField(
        default=list,
        help_text="Email domains for this company with confidence scores. "
        "Structure: [{"
        "  'domain': 'acme.com', "
        "  'confidence': 0.95, "
        "  'source': 'gemini_search'  # gemini_search|api_lookup|scraped"
        "}]",
    )

    email_patterns = models.JSONField(
        default=list,
        help_text="Ranked email patterns for this company with confidence scores. "
        "Structure: [{"
        "  'domain': 'acme.com', "
        "  'pattern': 'first.last', "
        "  'confidence': 0.95, "
        "  'source': 'verified_emails',  # verified_emails|api_lookup|scraped|inferred"
        "  'verified_count': 5"
        "}]",
    )

    known_emails = models.JSONField(
        default=list,
        help_text="Publicly found emails for pattern validation and confidence scoring. "
        "Structure: [{"
        "  'email': 'john.doe@acme.com', "
        "  'source': 'company_website',  # company_website|linkedin|others"
        "  'confidence': 0.9 "
        "}] "
        "Used to validate and rank email patterns.",
    )

    search_aliases = models.JSONField(
        default=list,
        help_text="Query variations that lead to this company for cache hits. "
        "Structure: ['Acme Corp', 'ACME', 'Acme Corporation', 'acme inc'] "
        "Dynamically built: when someone searches 'ACME Corp' and we find 'Acme Corporation', "
        "we add 'ACME Corp' to aliases to avoid duplicate work.",
    )

    metadata = models.JSONField(
        default=dict,
        help_text="Additional company information from discovery. "
        "Structure: {"
        "  'website': 'https://acme.com', "
        "  'linkedin': 'https://www.linkedin.com/company/acme', "
        "  'summary': 'LLM-generated company summary', "
        "  'location': 'San Francisco, CA', "
        "  'industry': 'Technology', "
        "  'employee_count': '1000-5000', "
        "  'founded': '2010'"
        "}",
    )

    # Discovery context
    search_level = models.CharField(
        max_length=20,
        choices=[("basic", "Basic"), ("advanced", "Advanced")],
        default="basic",
        help_text="Search level used for discovery (basic=Gemini, advanced=APIs)",
    )

    additional_info = models.JSONField(
        default=dict,
        help_text="Context provided during discovery for disambiguation. "
        "Structure: {'location': 'San Francisco', 'industry': 'tech', 'size': 'startup'}",
    )

    # Cache management
    cache_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this company data becomes stale and needs refresh (default: 90 days). "
        "Null means never expires (manually managed).",
    )

    last_validated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When we last verified/updated this company's domain and pattern data. "
        "Used for cache invalidation and data freshness tracking.",
    )

    class Meta:
        verbose_name_plural = "Companies"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["cache_expires_at"]),
        ]
        ordering = ["-last_validated_at", "name"]

    def __str__(self):
        best_domain = self.get_best_domains(limit=1)
        domain = best_domain[0]["domain"] if best_domain else "no-domain"
        return f"{self.name} ({domain})"

    def add_search_alias(self, alias):
        """
        Dynamically add search aliases to improve cache hit rates.

        When a search query resolves to this company, we add the query
        as an alias to avoid redundant work in future searches.
        """
        if alias and alias.lower() not in [a.lower() for a in self.search_aliases]:
            self.search_aliases.append(alias)
            self.save(update_fields=["search_aliases"])

    @classmethod
    def find_by_alias(cls, search_term):
        """
        Find company by exact name match or search aliases.
        """
        search_lower = search_term.lower().strip()

        # First try exact name match
        company = cls.objects.filter(name__iexact=search_lower).first()
        if company:
            return company

        # Then check if search_term exactly matches any alias
        companies = cls.objects.all()
        for company in companies:
            aliases = [alias.lower().strip() for alias in company.search_aliases]
            if search_lower in aliases:
                return company

        return None

    def is_cache_valid(self):
        """Check if company data is still fresh and doesn't need refresh."""
        if not self.cache_expires_at:
            return True  # Never expires

        return timezone.now() < self.cache_expires_at

    def get_best_patterns(self, domain=None, limit=3):
        """
        Get top email patterns by confidence.

        Args:
            domain: Filter patterns for specific domain, or None for all
            limit: Maximum number of patterns to return

        Returns:
            List of pattern dictionaries sorted by confidence
        """
        patterns = self.email_patterns

        if domain:
            patterns = [p for p in patterns if p.get("domain") == domain]

        # Sort by confidence descending
        sorted_patterns = sorted(
            patterns, key=lambda p: p.get("confidence", 0), reverse=True
        )

        return sorted_patterns[:limit]

    def get_best_domains(self, limit=1):
        """
        Get top email domains by confidence.

        Args:
            limit: Maximum number of domains to return (default: 1)

        Returns:
            List of domain dictionaries sorted by confidence
        """
        domains = self.email_domains

        # Sort by confidence descending
        sorted_domains = sorted(
            domains, key=lambda d: d.get("confidence", 0), reverse=True
        )

        return sorted_domains[:limit]

    def get_primary_email_domain(self):
        """Get the primary email domain (highest confidence)."""
        best_domains = self.get_best_domains(limit=1)
        return best_domains[0]["domain"] if best_domains else None

    def update_cache_expiry(self, days=90):
        """Update cache expiry to specified days from now."""
        self.cache_expires_at = timezone.now() + timezone.timedelta(days=days)
        self.last_validated_at = timezone.now()
        self.save(update_fields=["cache_expires_at", "last_validated_at"])
