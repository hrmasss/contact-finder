from typing import List, Dict, Any, Optional
from django.utils import timezone
from .domain.gemini import GeminiDomainService
from .pattern.gemini import GeminiPatternService
from .domain.base import CompanyResult
from .pattern.base import PatternResult, EmailResult
from ..models import DiscoveredCompany


class DiscoveryPipeline:
    """
    Main pipeline for domain and pattern discovery with caching.
    """

    def __init__(self):
        self.domain_service = GeminiDomainService()
        self.pattern_service = GeminiPatternService()

    def discover(
        self,
        company_query: str,
        search_level: str = "basic",
        additional_info: Dict[str, Any] = None,
        force_refresh: bool = False,
    ) -> List[DiscoveredCompany]:
        """
        Discover company domains and patterns with caching.

        Args:
            company_query: Company name to search for
            search_level: Search level (basic/advanced)
            additional_info: Optional context for disambiguation
            force_refresh: Force refresh even if cached data exists

        Returns:
            List[Company]: Discovered companies with patterns
        """
        if additional_info is None:
            additional_info = {}

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_company = self._check_cache(company_query)
            if cached_company:
                return [cached_company]

        # Step 1: Discover company domains
        company_results = self.domain_service.discover_company_domains(
            company_query=company_query, additional_info=additional_info
        )

        # Step 2: For each company, discover email patterns and known emails
        companies = []
        for company_result in company_results:
            patterns, known_emails = self._discover_patterns_and_emails(company_result)

            # Create or update Company model instance
            company = self._create_or_update_company(
                company_result=company_result,
                patterns=patterns,
                known_emails=known_emails,
                search_level=search_level,
                additional_info=additional_info,
                company_query=company_query,
            )
            companies.append(company)

        # Step 3: Sort companies by best domain confidence
        companies.sort(key=lambda c: self._get_best_domain_confidence(c), reverse=True)

        return companies

    def _check_cache(self, company_query: str) -> Optional[DiscoveredCompany]:
        """Check if company exists in cache and is still valid."""
        try:
            # First try exact name match
            company = DiscoveredCompany.objects.filter(name__iexact=company_query.strip()).first()
            if company and company.is_cache_valid():
                return company

            # Then try alias match
            company = DiscoveredCompany.find_by_alias(company_query)
            if company and company.is_cache_valid():
                return company

            return None
        except Exception:
            return None

    def _discover_patterns_and_emails(
        self, company_result: CompanyResult
    ) -> tuple[List[PatternResult], List[EmailResult]]:
        """Discover email patterns and known emails for all company domains."""
        all_patterns = []
        all_emails = []

        # Get patterns and emails for all email domains
        for domain_result in company_result.email_domains:
            patterns = self.pattern_service.discover_email_patterns(
                domain_result.domain
            )
            emails = self.pattern_service.discover_known_emails(domain_result.domain)

            all_patterns.extend(patterns)
            all_emails.extend(emails)

        # Remove duplicates and sort by confidence
        unique_patterns = {}
        for pattern in all_patterns:
            key = (pattern.domain, pattern.pattern)
            if (
                key not in unique_patterns
                or pattern.confidence > unique_patterns[key].confidence
            ):
                unique_patterns[key] = pattern

        unique_emails = {}
        for email in all_emails:
            key = email.email
            if (
                key not in unique_emails
                or email.confidence > unique_emails[key].confidence
            ):
                unique_emails[key] = email

        sorted_patterns = sorted(
            unique_patterns.values(), key=lambda p: p.confidence, reverse=True
        )
        sorted_emails = sorted(
            unique_emails.values(), key=lambda e: e.confidence, reverse=True
        )

        return sorted_patterns, sorted_emails

    def _create_or_update_company(
        self,
        company_result: CompanyResult,
        patterns: List[PatternResult],
        known_emails: List[EmailResult],
        search_level: str,
        additional_info: Dict[str, Any],
        company_query: str,
    ) -> DiscoveredCompany:
        """Create or update DiscoveredCompany model instance."""

        # Try to find existing company
        company = DiscoveredCompany.objects.filter(name__iexact=company_result.name).first()

        if company:
            # Update existing company
            company.email_domains = self._serialize_domains(
                company_result.email_domains
            )
            company.email_patterns = self._serialize_patterns(patterns)
            company.known_emails = self._serialize_emails(known_emails)
            company.metadata = company_result.metadata
            company.search_aliases = list(
                set(company.search_aliases + company_result.search_aliases)
            )
            company.search_level = search_level
            company.additional_info = additional_info
            company.last_validated_at = timezone.now()
            company.update_cache_expiry()

            # Add search query as alias if different from name
            if company_query.lower().strip() != company.name.lower().strip():
                company.add_search_alias(company_query)

            company.save()
        else:
            # Create new company
            company = DiscoveredCompany.objects.create(
                name=company_result.name,
                email_domains=self._serialize_domains(company_result.email_domains),
                email_patterns=self._serialize_patterns(patterns),
                known_emails=self._serialize_emails(known_emails),
                search_aliases=company_result.search_aliases,
                metadata=company_result.metadata,
                search_level=search_level,
                additional_info=additional_info,
                last_validated_at=timezone.now(),
            )
            company.update_cache_expiry()

            # Add search query as alias if different from name
            if company_query.lower().strip() != company.name.lower().strip():
                company.add_search_alias(company_query)

        return company

    def _serialize_domains(self, domains: List) -> List[Dict[str, Any]]:
        """Serialize domain results for JSON storage."""
        return [
            {
                "domain": domain.domain,
                "confidence": domain.confidence,
                "source": domain.source,
            }
            for domain in domains
        ]

    def _serialize_patterns(
        self, patterns: List[PatternResult]
    ) -> List[Dict[str, Any]]:
        """Serialize pattern results for JSON storage."""
        return [
            {
                "domain": pattern.domain,
                "pattern": pattern.pattern,
                "confidence": pattern.confidence,
                "source": pattern.source,
                "verified_count": pattern.verified_count,
            }
            for pattern in patterns
        ]

    def _serialize_emails(self, emails: List[EmailResult]) -> List[Dict[str, Any]]:
        """Serialize email results for JSON storage."""
        return [
            {
                "email": email.email,
                "source": email.source,
                "confidence": email.confidence,
            }
            for email in emails
        ]

    def _get_best_domain_confidence(self, company: DiscoveredCompany) -> float:
        """Get the confidence of the best domain for sorting."""
        best_domains = company.get_best_domains(limit=1)
        return best_domains[0]["confidence"] if best_domains else 0.0
