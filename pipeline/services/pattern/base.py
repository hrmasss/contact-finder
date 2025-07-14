from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass


@dataclass
class PatternResult:
    """Email pattern discovery result."""

    domain: str
    pattern: str
    confidence: float
    source: str
    verified_count: int = 0


@dataclass
class EmailResult:
    """Known email discovery result."""

    email: str
    source: str
    confidence: float


class PatternDiscoveryService(ABC):
    """Base interface for email pattern discovery services."""

    @abstractmethod
    def discover_email_patterns(self, domain: str) -> List[PatternResult]:
        """
        Discover email patterns for a domain.

        Args:
            domain: Domain to analyze for patterns

        Returns:
            List[PatternResult]: Email patterns found
        """
        pass

    @abstractmethod
    def discover_known_emails(self, domain: str) -> List[EmailResult]:
        """
        Discover known public emails for a domain.

        Args:
            domain: Domain to search for public emails

        Returns:
            List[EmailResult]: Known emails found
        """
        pass
