from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class DomainResult:
    """Result from domain discovery."""

    domain: str
    confidence: float
    source: str


@dataclass
class CompanyResult:
    """Company discovery result."""

    name: str
    email_domains: List[DomainResult]
    metadata: Dict[str, Any]  # website, linkedin, summary, location, industry, etc.
    search_aliases: List[str]


class DomainDiscoveryService(ABC):
    """Base interface for domain discovery services."""

    @abstractmethod
    def discover_company_domains(
        self, company_query: str, additional_info: Dict[str, Any] = None
    ) -> List[CompanyResult]:
        """
        Discover domains for a company.

        Args:
            company_query: Company name to search for
            additional_info: Optional context for disambiguation

        Returns:
            List[CompanyResult]: Found companies with their domains
        """
        pass
