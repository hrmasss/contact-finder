from typing import List, Dict, Any, Optional
from django.utils import timezone
from .employee.gemini import GeminiEmployeeService
from .employee.base import EmployeeResult
from .company_discovery import CompanyDiscoveryPipeline
from ..models import DiscoveredEmployee, DiscoveredCompany


class EmployeeDiscoveryPipeline:
    """
    Main pipeline for employee discovery with caching.
    """

    def __init__(self):
        self.employee_service = GeminiEmployeeService()

    def discover(
        self,
        employee_query: str,
        company_query: str = None,
        company_id: int = None,
        search_level: str = "basic",
        additional_info: Dict[str, Any] = None,
        force_refresh: bool = False,
    ) -> List[DiscoveredEmployee]:
        """
        Discover employees with caching.

        Args:
            employee_query: Employee name to search for
            company_query: Company name for context
            company_id: Specific company ID to search within
            search_level: Search level (basic/advanced)
            additional_info: Optional context for disambiguation
            force_refresh: Force refresh even if cached data exists

        Returns:
            List[DiscoveredEmployee]: Discovered employees with email candidates
        """
        if additional_info is None:
            additional_info = {}

        # Resolve company context
        company = self._resolve_company(company_query, company_id, search_level)
        if not company:
            return []

        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_employee = self._check_cache(employee_query, company)
            if cached_employee:
                cached_employee.is_cached = True
                return [cached_employee]

        # Step 1: Discover employees using service
        company_info = self._build_company_info(company)
        employee_results = self.employee_service.discover_employees(
            employee_query=employee_query,
            company_info=company_info,
            additional_info=additional_info,
        )

        # Step 2: Create or update employee model instances
        employees = []
        for employee_result in employee_results:
            employee = self._create_or_update_employee(
                employee_result=employee_result,
                company=company,
                search_level=search_level,
                additional_info=additional_info,
                employee_query=employee_query,
            )
            employees.append(employee)

        # Step 3: Sort employees by best email confidence
        employees.sort(key=lambda e: self._get_best_email_confidence(e), reverse=True)

        return employees

    def _resolve_company(
        self,
        company_query: str = None,
        company_id: int = None,
        search_level: str = "basic",
    ) -> Optional[DiscoveredCompany]:
        """Resolve company from query or ID, auto-discovering if needed."""
        if company_id:
            try:
                return DiscoveredCompany.objects.get(id=company_id)
            except DiscoveredCompany.DoesNotExist:
                return None

        if company_query:
            # Try to find by name or alias first
            company = DiscoveredCompany.find_by_alias(company_query)
            if company:
                return company

            # If not found, auto-discover the company
            print(f"Company '{company_query}' not found in cache. Auto-discovering...")
            company_pipeline = CompanyDiscoveryPipeline()
            discovered_companies = company_pipeline.discover(
                company_query=company_query,
                search_level=search_level,  # Use the same search level as employee discovery
                additional_info={},
                force_refresh=False,
            )

            # Return the first discovered company
            if discovered_companies:
                return discovered_companies[0]

        return None

    def _build_company_info(self, company: DiscoveredCompany) -> Dict[str, Any]:
        """Build company context for employee discovery."""
        # Get primary domain
        primary_domain = ""
        if company.email_domains:
            primary_domain = max(
                company.email_domains, key=lambda d: d.get("confidence", 0)
            ).get("domain", "")

        return {
            "name": company.name,
            "primary_domain": primary_domain,
            "website": company.metadata.get("website", ""),
            "industry": company.metadata.get("industry", ""),
            "location": company.metadata.get("location", ""),
            "email_domains": company.email_domains,
            "email_patterns": company.email_patterns,
        }

    def _check_cache(
        self, employee_query: str, company: DiscoveredCompany
    ) -> Optional[DiscoveredEmployee]:
        """Check if employee exists in cache and is still valid."""
        try:
            # First try exact name match
            employee = DiscoveredEmployee.objects.filter(
                company=company, full_name__iexact=employee_query.strip()
            ).first()
            if employee and employee.is_cache_valid():
                return employee

            # Then try alias match
            employee = DiscoveredEmployee.find_by_alias(employee_query, company)
            if employee and employee.is_cache_valid():
                return employee

            return None
        except Exception as e:
            print(f"Error checking employee cache: {e}")
            return None

    def _create_or_update_employee(
        self,
        employee_result: EmployeeResult,
        company: DiscoveredCompany,
        search_level: str,
        additional_info: Dict[str, Any],
        employee_query: str,
    ) -> DiscoveredEmployee:
        """Create or update DiscoveredEmployee model instance."""

        # Try to find existing employee
        employee = DiscoveredEmployee.objects.filter(
            company=company, full_name__iexact=employee_result.full_name
        ).first()

        # Serialize email candidates
        email_candidates = []
        for candidate in employee_result.email_candidates:
            email_candidates.append(
                {
                    "email": candidate.email,
                    "confidence": candidate.confidence,
                    "source": candidate.source,
                    "pattern_used": candidate.pattern_used,
                    "domain": candidate.domain,
                    "verified": candidate.verified,
                    "verification_method": candidate.verification_method,
                    "last_checked": timezone.now().isoformat(),
                }
            )

        if employee:
            # Update existing employee
            employee.name_variations = employee_result.name_variations
            employee.email_candidates = email_candidates
            employee.additional_info = employee_result.additional_info
            employee.search_aliases = list(
                set(employee.search_aliases + employee_result.search_aliases)
            )
            employee.search_level = search_level
            employee.metadata = employee_result.metadata
            employee.last_validated_at = timezone.now()
            employee.update_cache_expiry()

            # Add search query as alias if different from name
            if employee_query.lower().strip() != employee.full_name.lower().strip():
                employee.add_search_alias(employee_query)

            employee.save()
        else:
            # Create new employee
            employee = DiscoveredEmployee.objects.create(
                company=company,
                full_name=employee_result.full_name,
                name_variations=employee_result.name_variations,
                email_candidates=email_candidates,
                additional_info=employee_result.additional_info,
                search_aliases=employee_result.search_aliases,
                search_level=search_level,
                metadata=employee_result.metadata,
                last_validated_at=timezone.now(),
            )
            employee.update_cache_expiry()

            # Add search query as alias if different from name
            if employee_query.lower().strip() != employee.full_name.lower().strip():
                employee.add_search_alias(employee_query)

        # Set cache status (new/updated employees are not from cache)
        employee.is_cached = False
        return employee

    def _get_best_email_confidence(self, employee: DiscoveredEmployee) -> float:
        """Get confidence of best email for sorting."""
        best_email = employee.get_best_email()
        return best_email.get("confidence", 0.0) if best_email else 0.0
