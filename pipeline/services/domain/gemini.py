import json
from typing import List, Dict, Any
from .base import DomainDiscoveryService, CompanyResult, DomainResult
from ..prompts import DOMAIN_DISCOVERY_PROMPT
from contactfinder.agents.gemini_agent import gemini_agent


class GeminiDomainService(DomainDiscoveryService):
    """Domain discovery using Gemini with Google Search."""

    def discover_company_domains(
        self, company_query: str, additional_info: Dict[str, Any] = None
    ) -> List[CompanyResult]:
        """
        Discover company domains using Gemini.

        Args:
            company_query: Company name to search for
            additional_info: Optional context for disambiguation

        Returns:
            List[CompanyResult]: Found companies with their domains
        """
        if additional_info is None:
            additional_info = {}

        # Format the prompt
        prompt = DOMAIN_DISCOVERY_PROMPT.format(
            company_query=company_query,
            additional_info=json.dumps(additional_info) if additional_info else "None",
        )

        try:
            # Call Gemini agent
            response = gemini_agent(prompt)

            # Try to extract JSON from response if it's wrapped in markdown
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()

            # Parse JSON response
            data = json.loads(response)

            # Convert to CompanyResult objects
            companies = []
            for company_data in data.get("companies", []):
                # Convert email domains
                email_domains = []
                for domain_data in company_data.get("email_domains", []):
                    domain_result = DomainResult(
                        domain=domain_data["domain"],
                        confidence=domain_data["confidence"],
                        source=domain_data["source"],
                    )
                    email_domains.append(domain_result)

                # Create company result
                company_result = CompanyResult(
                    name=company_data["name"],
                    email_domains=email_domains,
                    metadata=company_data.get("metadata", {}),
                    search_aliases=company_data.get("search_aliases", []),
                )
                companies.append(company_result)

            return companies

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Gemini response: {e}")
            print(f"Raw response: {response}")

            # Fallback: try to create a basic result from the query
            print(f"Creating fallback result for: {company_query}")
            fallback_result = CompanyResult(
                name=company_query,
                email_domains=[],
                metadata={
                    "source": "fallback",
                    "error": "Failed to parse Gemini response",
                },
                search_aliases=[],
            )
            return [fallback_result]

        except Exception as e:
            print(f"Error in Gemini domain discovery: {e}")

            # Fallback: try to create a basic result from the query
            print(f"Creating fallback result for: {company_query}")
            fallback_result = CompanyResult(
                name=company_query,
                email_domains=[],
                metadata={"source": "fallback", "error": str(e)},
                search_aliases=[],
            )
            return [fallback_result]
