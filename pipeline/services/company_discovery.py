from typing import List, Dict, Any, Optional
from django.utils import timezone
from .domain.gemini import GeminiDomainService
from .domain.rocketreach import RocketReachDomainService
from .pattern.gemini import GeminiPatternService
from .domain.base import CompanyResult
from .pattern.base import PatternResult, EmailResult
from .validator import DataValidator
from .confidence import MAX_RESULTS_PER_SERVICE
from ..models import DiscoveredCompany


class CompanyDiscoveryPipeline:
    """
    Main pipeline for domain and pattern discovery with caching.
    """

    def __init__(self):
        self.gemini_domain_service = GeminiDomainService()
        self.rocketreach_domain_service = None
        self.pattern_service = GeminiPatternService()

        # Initialize RocketReach service if API key is available
        try:
            self.rocketreach_domain_service = RocketReachDomainService()
        except ValueError:
            print(
                "RocketReach API key not found - advanced search will use Gemini only"
            )

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
                # Update cache status and return
                cached_company.is_cached = True
                return [cached_company]

        # Step 1: Discover company domains with context-enhanced approach
        company_results = []
        third_party_context = {}

        # Phase 1: Third-party lookups first (RocketReach for advanced search)
        if search_level == "advanced" and self.rocketreach_domain_service:
            try:
                rocketreach_results = (
                    self.rocketreach_domain_service.discover_company_domains(
                        company_query=company_query, additional_info=additional_info
                    )
                )

                # Filter and validate RocketReach results
                for result in rocketreach_results[
                    : MAX_RESULTS_PER_SERVICE["rocketreach"]
                ]:
                    # Validate domains
                    validated_domains = []
                    for domain in result.email_domains:
                        if DataValidator.validate_domain(domain.domain):
                            domain.confidence = DataValidator.adjust_confidence(
                                domain.confidence, domain.source
                            )
                            validated_domains.append(domain)

                    if validated_domains:
                        result.email_domains = validated_domains
                        company_results.append(result)

                        # Build context for Gemini
                        third_party_context[result.name] = {
                            "domains": [d.domain for d in validated_domains],
                            "metadata": result.metadata,
                            "source": "rocketreach",
                        }

            except Exception as e:
                print(f"RocketReach search failed, falling back to Gemini: {e}")

        # Phase 2: Use Gemini with third-party context for enhanced results
        enhanced_additional_info = dict(additional_info)
        if third_party_context:
            enhanced_additional_info["third_party_context"] = third_party_context

        gemini_results = self.gemini_domain_service.discover_company_domains(
            company_query=company_query, additional_info=enhanced_additional_info
        )

        # Process Gemini results with validation and context awareness
        for result in gemini_results[: MAX_RESULTS_PER_SERVICE["gemini"]]:
            # Validate and adjust confidence for Gemini domains
            validated_domains = []
            for domain in result.email_domains:
                if DataValidator.validate_domain(domain.domain):
                    # Higher confidence if domain was verified by third-party
                    source = domain.source
                    if any(
                        domain.domain in ctx.get("domains", [])
                        for ctx in third_party_context.values()
                    ):
                        source = "gemini_verified"
                    else:
                        source = "gemini_raw"

                    domain.confidence = DataValidator.adjust_confidence(
                        domain.confidence, source
                    )
                    validated_domains.append(domain)

            if validated_domains:
                result.email_domains = validated_domains
                company_results.append(result)

        # Deduplicate results by company name
        company_results = self._deduplicate_companies(company_results)

        # Step 2: For each company, discover email patterns and known emails with validation
        companies = []
        for company_result in company_results:
            patterns, known_emails = self._discover_patterns_and_emails_with_validation(
                company_result
            )

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
            company = DiscoveredCompany.objects.filter(
                name__iexact=company_query.strip()
            ).first()
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

    def _discover_patterns_and_emails_with_validation(
        self, company_result: CompanyResult
    ) -> tuple[List[PatternResult], List[EmailResult]]:
        """
        Discover patterns and emails with validation and confidence adjustment.

        Args:
            company_result: Company result to discover patterns for

        Returns:
            Tuple of (patterns, known_emails) with validation applied
        """
        patterns, known_emails = self._discover_patterns_and_emails(company_result)

        # Validate and filter patterns
        validated_patterns = []
        for pattern in patterns:
            if DataValidator.validate_email_pattern(pattern.pattern):
                pattern.confidence = DataValidator.adjust_confidence(
                    pattern.confidence, pattern.source
                )
                validated_patterns.append(pattern)

        # Validate and filter known emails
        validated_emails = []
        for email in known_emails:
            if DataValidator.validate_email(email.email):
                email.confidence = DataValidator.adjust_confidence(
                    email.confidence, email.source
                )
                validated_emails.append(email)

        return validated_patterns, validated_emails

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
        company = DiscoveredCompany.objects.filter(
            name__iexact=company_result.name
        ).first()

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

        # Set cache status (new/updated companies are not from cache)
        company.is_cached = False
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

    def _deduplicate_companies(
        self, company_results: List[CompanyResult]
    ) -> List[CompanyResult]:
        """
        Deduplicate company results by name, merging domains and metadata.

        Args:
            company_results: List of company results to deduplicate

        Returns:
            List[CompanyResult]: Deduplicated company results
        """
        if not company_results:
            return []

        # Group by normalized company name
        company_groups = {}
        for company in company_results:
            normalized_name = company.name.lower().strip()
            if normalized_name not in company_groups:
                company_groups[normalized_name] = []
            company_groups[normalized_name].append(company)

        # Merge groups
        merged_companies = []
        for group in company_groups.values():
            if len(group) == 1:
                merged_companies.append(group[0])
            else:
                # Merge multiple companies with same name
                merged_company = self._merge_company_results(group)
                merged_companies.append(merged_company)

        return merged_companies

    def _merge_company_results(self, companies: List[CompanyResult]) -> CompanyResult:
        """
        Merge multiple CompanyResult objects with the same name.

        Args:
            companies: List of companies to merge

        Returns:
            CompanyResult: Merged company result
        """
        if not companies:
            return None

        # Use the first company as base
        merged = companies[0]

        # Merge domains, avoiding duplicates
        all_domains = list(merged.email_domains)
        domain_set = {d.domain for d in all_domains}

        for company in companies[1:]:
            for domain in company.email_domains:
                if domain.domain not in domain_set:
                    all_domains.append(domain)
                    domain_set.add(domain.domain)

        # Merge metadata
        merged_metadata = dict(merged.metadata)
        for company in companies[1:]:
            for key, value in company.metadata.items():
                if key not in merged_metadata and value:
                    merged_metadata[key] = value

        # Merge search aliases
        all_aliases = list(merged.search_aliases)
        alias_set = {a.lower() for a in all_aliases}

        for company in companies[1:]:
            for alias in company.search_aliases:
                if alias.lower() not in alias_set:
                    all_aliases.append(alias)
                    alias_set.add(alias.lower())

        # Create merged result
        return CompanyResult(
            name=merged.name,
            email_domains=all_domains,
            metadata=merged_metadata,
            search_aliases=all_aliases,
        )
