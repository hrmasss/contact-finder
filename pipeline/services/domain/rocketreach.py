import os
import requests
from typing import List, Dict, Any
from .base import DomainDiscoveryService, CompanyResult, DomainResult


class RocketReachDomainService(DomainDiscoveryService):
    """Domain discovery using RocketReach API."""

    def __init__(self):
        self.api_key = os.getenv("ROCKET_REACH_API_KEY")
        if not self.api_key:
            raise ValueError("ROCKET_REACH_API_KEY not found in environment variables")

    def discover_company_domains(
        self, company_query: str, additional_info: Dict[str, Any] = None
    ) -> List[CompanyResult]:
        """
        Discover domains for a company using RocketReach API.

        Args:
            company_query: Company name to search for
            additional_info: Optional context for disambiguation

        Returns:
            List[CompanyResult]: Found companies with their domains
        """
        if additional_info is None:
            additional_info = {}

        try:
            # Prepare the API request with correct format
            url = "https://api.rocketreach.co/api/v2/searchCompany"
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Api-Key": self.api_key,
            }

            # Build search payload with correct structure
            payload = {"query": {"name": [company_query]}}

            # Make the API call
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            # Parse the response
            response_data = response.json()

            # Handle different response formats
            if isinstance(response_data, dict):
                companies_data = response_data.get("companies", [])
                if not companies_data:
                    # If no companies key, might be direct array or different structure
                    companies_data = (
                        response_data if isinstance(response_data, list) else []
                    )
            elif isinstance(response_data, list):
                companies_data = response_data
            else:
                print(f"Unexpected response format: {type(response_data)}")
                return []

            # Convert to CompanyResult objects
            results = []
            for company_data in companies_data:
                if not isinstance(company_data, dict):
                    continue

                email_domains = []

                # Extract email domain if available
                if company_data.get("email_domain"):
                    domain_result = DomainResult(
                        domain=company_data["email_domain"],
                        confidence=0.75,  # Adjust confidence for RocketReach
                        source="rocketreach_api",
                    )
                    email_domains.append(domain_result)

                # Build minimal metadata - let Gemini handle detailed info
                metadata = {
                    "rocketreach_id": company_data.get("id"),
                    "source": "rocketreach",
                }

                # Add basic info if available
                if company_data.get("ticker_symbol"):
                    metadata["ticker_symbol"] = company_data["ticker_symbol"]
                if company_data.get("industry_str"):
                    metadata["industry_hint"] = company_data["industry_str"]

                # Create search aliases
                search_aliases = [company_data.get("name", company_query)]
                if company_data.get("ticker_symbol"):
                    search_aliases.append(company_data["ticker_symbol"])

                # Create CompanyResult
                company_result = CompanyResult(
                    name=company_data.get("name", company_query),
                    email_domains=email_domains,
                    metadata=metadata,
                    search_aliases=search_aliases,
                )
                results.append(company_result)

            return results

        except requests.exceptions.RequestException as e:
            print(f"RocketReach API request failed: {e}")
            return []
        except Exception as e:
            print(f"Error in RocketReach domain discovery: {e}")
            return []
