from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class EmailCandidate:
    """Email candidate with confidence score."""
    email: str
    confidence: float
    source: str
    pattern_used: str = ""
    domain: str = ""
    verified: bool = False
    verification_method: str = "none"


@dataclass
class EmployeeResult:
    """Employee discovery result."""
    full_name: str
    name_variations: Dict[str, Any]
    email_candidates: List[EmailCandidate]
    additional_info: Dict[str, Any]
    search_aliases: List[str]
    metadata: Dict[str, Any]


class EmployeeDiscoveryService(ABC):
    """Base interface for employee discovery services."""

    @abstractmethod
    def discover_employees(
        self, 
        employee_query: str, 
        company_info: Dict[str, Any] = None,
        additional_info: Dict[str, Any] = None
    ) -> List[EmployeeResult]:
        """
        Discover employees matching the query.

        Args:
            employee_query: Employee name or identifier to search for
            company_info: Company context for better discovery
            additional_info: Optional context for disambiguation

        Returns:
            List[EmployeeResult]: Found employees with email candidates
        """
        pass
