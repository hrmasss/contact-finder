from django.db import models
from django.utils import timezone
from common.models import BaseModel


class Company(BaseModel):
    """
    Company model for domain and email pattern caching.

    This model serves as the central cache for company information, particularly
    focused on email domain patterns and validation. Once we lock onto a primary
    domain for a company, all employee email generation happens based on this
    domain's patterns.
    """

    name = models.CharField(
        max_length=255, help_text="Primary company name as found/confirmed"
    )

    summary = models.TextField(
        blank=True,
        help_text="LLM-generated company summary for context and relevance scoring",
    )

    primary_domain = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Main contact domain for email generation (e.g., 'acme.com'). "
        "This is the domain we've locked onto for employee email inference.",
    )

    email_patterns = models.JSONField(
        default=list,
        help_text="Ranked email patterns for this domain with confidence scores. "
        "Structure: [{"
        "  'pattern': 'first.last', "
        "  'confidence': 0.95, "
        "  'source': 'verified_emails'  # verified_emails|api_lookup|scraped"
        "}] ",
    )

    known_emails = models.JSONField(
        default=list,
        help_text="Publicly found emails for pattern validation and confidence scoring. "
        "Structure: [{'email': 'john.doe@acme.com', 'source': 'www.acme.com'}] "
        "Used to validate and rank email patterns.",
    )

    all_domains = models.JSONField(
        default=list,
        help_text="All domains related to this company with confidence scores. "
        "Structure: [{"
        "  'domain': 'acme.com', "
        "  'type': 'primary',  # primary|website|parent|subsidiary|other"
        "  'confidence': 0.95, "
        "}] ",
    )

    search_aliases = models.JSONField(
        default=list,
        help_text="Query variations that lead to this company for cache hits. "
        "Structure: ['Acme Corp', 'ACME', 'Acme Corporation', 'acme inc'] "
        "Dynamically built: when someone searches 'ACME Corp' and we find 'Acme Corporation', "
        "we add 'ACME Corp' to aliases to avoid duplicate work.",
    )

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
            models.Index(fields=["primary_domain"]),
            models.Index(fields=["name"]),
            models.Index(fields=["cache_expires_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.primary_domain})"

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


class Employee(BaseModel):
    """
    Employee model for contact caching with email verification.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="employees",
        help_text="Company this employee belongs to. Email generation uses company's primary_domain.",
    )

    full_name = models.CharField(
        max_length=255,
        help_text="Complete name as found from source. Primary identifier for this person.",
    )

    name_variations = models.JSONField(
        default=dict,
        help_text="Name components and variations for email generation. "
        "Structure: {"
        "  'first_name': 'Timothy', "
        "  'last_name': 'Johnson', "
        "  'nickname': 'Tim', "
        "  'initials': 'TJ', "
        "  'cultural_variants': ['T. Johnson', 'Tim J.'], "
        "} ",
    )

    additional_info = models.JSONField(
        default=dict,
        help_text="Flexible storage for any additional employee information. "
        "Structure: {"
        "  'title': 'Manager', "
        "  'department': 'Administration', "
        "  'linkedin_url': 'https://...', "
        "  'phone': '+1-555-...', "
        "  'location': 'New York, NY', "
        "  'employee_id': 'EMP001'"
        "} ",
    )

    primary_email = models.EmailField(
        blank=True,
        help_text="Best-confidence verified email. Auto-selected from candidate_emails "
        "based on highest (confidence * relevance_score). May still be probabilistic.",
    )

    candidate_emails = models.JSONField(
        default=list,
        help_text="All possible emails with detailed verification status. "
        "Structure: [{"
        "  'email': 'tim.johnson@acme.com', "
        "  'confidence': 0.92, "
        "  'smtp_status': 'deliverable',  # deliverable|undeliverable|catch_all|unknown"
        "  'smtp_code': 250, "
        "  'verification_method': 'smtp_check',  # smtp_check|api_verify|send_test|other"
        "  'source': 'pattern_generated',  # pattern_generated|scraped|api_lookup|other"
        "  'last_checked': '2025-01-15T10:30:00Z', "
        "  'relevance_score': 0.95,  # LLM confidence this email belongs to this person"
        "  'final_score': 0.874  # confidence * relevance_score"
        "}] ",
    )

    cache_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this employee data becomes stale (default: 30 days). "
        "Triggers re-verification of email candidates.",
    )

    last_validated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When we last verified/updated this employee's email candidates. "
        "Used for cache invalidation and re-verification scheduling.",
    )

    class Meta:
        indexes = [
            models.Index(fields=["company", "full_name"]),
            models.Index(fields=["primary_email"]),
            models.Index(fields=["cache_expires_at"]),
        ]

    def __str__(self):
        return f"{self.full_name} at {self.company.name}"

    def add_candidate_email(
        self,
        email,
        confidence,
        source="generated",
        smtp_status="unknown",
        relevance_score=1.0,
    ):
        """
        Add a new candidate email with verification details.

        Args:
            email: The email address
            confidence: Technical confidence (0-1) from generation/verification
            source: How this email was obtained
            smtp_status: SMTP verification result
            relevance_score: LLM confidence this belongs to this person (0-1)
        """

        candidate = {
            "email": email,
            "confidence": confidence,
            "smtp_status": smtp_status,
            "smtp_code": None,
            "is_catch_all": smtp_status == "catch_all",
            "verification_method": "pending",
            "source": source,
            "last_checked": timezone.now().isoformat(),
            "relevance_score": relevance_score,
            "final_score": confidence * relevance_score,
        }

        # Remove duplicates and add new candidate
        existing = [c for c in self.candidate_emails if c["email"] != email]
        existing.append(candidate)

        # Sort by final_score descending
        self.candidate_emails = sorted(
            existing, key=lambda x: x["final_score"], reverse=True
        )

        # Auto-update primary email if this is the best candidate
        if self.candidate_emails and self.candidate_emails[0]["email"] == email:
            self.primary_email = email

        self.save(update_fields=["candidate_emails", "primary_email"])

    def update_email_verification(
        self, email, smtp_status, smtp_code, verification_method
    ):
        """
        Update verification status for a specific candidate email.

        Handles the complex verification scenarios:
        - deliverable: Clear success
        - undeliverable: Clear failure
        - catch_all: Uncertain (needs additional verification)
        - unknown: Technical issues (retry later)
        """

        for candidate in self.candidate_emails:
            if candidate["email"] == email:
                candidate.update(
                    {
                        "smtp_status": smtp_status,
                        "smtp_code": smtp_code,
                        "is_catch_all": smtp_status == "catch_all",
                        "verification_method": verification_method,
                        "last_checked": timezone.now().isoformat(),
                    }
                )

                # Adjust confidence based on verification
                if smtp_status == "deliverable":
                    candidate["confidence"] = min(candidate["confidence"] * 1.2, 1.0)
                elif smtp_status == "undeliverable":
                    candidate["confidence"] = candidate["confidence"] * 0.1
                elif smtp_status == "catch_all":
                    candidate["confidence"] = (
                        candidate["confidence"] * 0.7
                    )  # Uncertainty penalty

                # Recalculate final score
                candidate["final_score"] = (
                    candidate["confidence"] * candidate["relevance_score"]
                )
                break

        # Re-sort and update primary email
        self.candidate_emails = sorted(
            self.candidate_emails, key=lambda x: x["final_score"], reverse=True
        )
        if self.candidate_emails:
            self.primary_email = self.candidate_emails[0]["email"]

        self.save(update_fields=["candidate_emails", "primary_email"])

    def get_best_email(self):
        """Get email with highest final score (confidence * relevance)."""
        if not self.candidate_emails:
            return None
        return max(self.candidate_emails, key=lambda x: x["final_score"])

    def is_cache_valid(self):
        """Check if employee data is still fresh."""
        if not self.cache_expires_at:
            return True

        return timezone.now() < self.cache_expires_at
