import json
from typing import List, Dict, Any
from .base import EmployeeDiscoveryService, EmployeeResult, EmailCandidate
from ..validator import DataValidator
from ..prompts import EMPLOYEE_DISCOVERY_PROMPT
from contactfinder.agents.gemini_agent import gemini_agent


class GeminiEmployeeService(EmployeeDiscoveryService):
    """Employee discovery using Gemini with Google Search."""

    def discover_employees(
        self, 
        employee_query: str, 
        company_info: Dict[str, Any] = None,
        additional_info: Dict[str, Any] = None
    ) -> List[EmployeeResult]:
        """
        Discover employees using Gemini AI search.

        Args:
            employee_query: Employee name or identifier to search for
            company_info: Company context for better discovery
            additional_info: Optional context for disambiguation

        Returns:
            List[EmployeeResult]: Found employees with email candidates
        """
        if company_info is None:
            company_info = {}
        if additional_info is None:
            additional_info = {}

        try:
            # Build the search prompt
            prompt = self._build_search_prompt(employee_query, company_info, additional_info)
            
            # Call Gemini agent
            response = gemini_agent(prompt)
            
            # Clean and parse response
            response_clean = self._clean_response(response)
            data = json.loads(response_clean)
            
            # Convert to EmployeeResult objects
            results = []
            for employee_data in data.get("employees", []):
                employee_result = self._parse_employee_data(employee_data, company_info)
                if employee_result:
                    results.append(employee_result)
            
            return results
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Gemini response for employee '{employee_query}': {e}")
            print(f"Raw response: {response}")
            return self._get_fallback_employee(employee_query, company_info)
        except Exception as e:
            print(f"Error in Gemini employee discovery for '{employee_query}': {e}")
            return self._get_fallback_employee(employee_query, company_info)

    def _build_search_prompt(self, employee_query: str, company_info: Dict[str, Any], additional_info: Dict[str, Any]) -> str:
        """Build search prompt for Gemini using the standard template."""
        company_name = company_info.get("name", "Unknown Company")
        primary_domain = company_info.get("primary_domain", "")
        email_patterns = company_info.get("email_patterns", [])
        email_domains = company_info.get("email_domains", [])
        
        # Format patterns for display
        patterns_str = ", ".join([p.get("pattern", "") for p in email_patterns[:5]])
        domains_str = ", ".join([d.get("domain", "") for d in email_domains[:3]])
        
        # Use the standard prompt template
        return EMPLOYEE_DISCOVERY_PROMPT.format(
            employee_query=employee_query,
            company_info=company_info,
            additional_info=additional_info,
            company_name=company_name,
            primary_domain=primary_domain,
            email_patterns=patterns_str,
            email_domains=domains_str
        )

    def _clean_response(self, response: str) -> str:
        """Clean Gemini response to extract JSON."""
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]
        return response_clean.strip()

    def _parse_employee_data(self, employee_data: Dict[str, Any], company_info: Dict[str, Any]) -> EmployeeResult:
        """Parse employee data from Gemini response."""
        try:
            # Validate and process email candidates
            email_candidates = []
            for email_data in employee_data.get("email_candidates", []):
                email = email_data.get("email", "")
                if DataValidator.validate_email(email):
                    # Adjust confidence based on source
                    confidence = DataValidator.adjust_confidence(
                        email_data.get("confidence", 0.5),
                        email_data.get("source", "gemini_raw")
                    )
                    
                    candidate = EmailCandidate(
                        email=email,
                        confidence=confidence,
                        source=email_data.get("source", "gemini_search"),
                        pattern_used=email_data.get("pattern_used", ""),
                        domain=email_data.get("domain", ""),
                        verified=False,
                        verification_method="none"
                    )
                    email_candidates.append(candidate)
            
            # Sort by confidence
            email_candidates.sort(key=lambda x: x.confidence, reverse=True)
            
            # Build result
            result = EmployeeResult(
                full_name=employee_data.get("full_name", ""),
                name_variations=employee_data.get("name_variations", {}),
                email_candidates=email_candidates,
                additional_info=employee_data.get("additional_info", {}),
                search_aliases=employee_data.get("search_aliases", []),
                metadata=employee_data.get("metadata", {})
            )
            
            return result
            
        except Exception as e:
            print(f"Error parsing employee data: {e}")
            return None

    def _get_fallback_employee(self, employee_query: str, company_info: Dict[str, Any]) -> List[EmployeeResult]:
        """Generate fallback employee result when Gemini fails."""
        try:
            # Parse basic name components
            name_parts = employee_query.strip().split()
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""
            
            # Generate basic email candidates if we have company domain
            email_candidates = []
            company_domain = company_info.get("primary_domain", "")
            
            if company_domain and first_name and last_name:
                # Common email patterns
                patterns = [
                    f"{first_name.lower()}.{last_name.lower()}@{company_domain}",
                    f"{first_name.lower()}{last_name.lower()}@{company_domain}",
                    f"{first_name[0].lower()}.{last_name.lower()}@{company_domain}",
                    f"{first_name.lower()}@{company_domain}",
                ]
                
                for i, pattern in enumerate(patterns):
                    if DataValidator.validate_email(pattern):
                        confidence = 0.4 - (i * 0.05)  # Decreasing confidence
                        candidate = EmailCandidate(
                            email=pattern,
                            confidence=confidence,
                            source="fallback_pattern",
                            pattern_used="fallback",
                            domain=company_domain,
                            verified=False,
                            verification_method="none"
                        )
                        email_candidates.append(candidate)
            
            # Build fallback result
            fallback_result = EmployeeResult(
                full_name=employee_query,
                name_variations={
                    "first_name": first_name,
                    "last_name": last_name,
                    "name_variants": [employee_query]
                },
                email_candidates=email_candidates,
                additional_info={},
                search_aliases=[employee_query],
                metadata={
                    "discovery_source": "fallback",
                    "confidence_score": 0.3,
                    "sources": ["fallback_generation"]
                }
            )
            
            return [fallback_result]
            
        except Exception as e:
            print(f"Error generating fallback employee: {e}")
            return []
