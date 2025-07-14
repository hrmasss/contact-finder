import re
from typing import List, Dict, Any
from .confidence import (
    SUSPICIOUS_DOMAIN_PATTERNS,
    SUSPICIOUS_EMAIL_PATTERNS,
    MIN_CONFIDENCE_THRESHOLDS,
    SERVICE_CONFIDENCE_MULTIPLIERS,
)


class DataValidator:
    """Validates and filters discovery results."""

    @staticmethod
    def validate_domain(domain: str) -> bool:
        """Check if domain is valid and not suspicious."""
        if not domain or len(domain) < 3:
            return False

        # Check against suspicious patterns
        for pattern in SUSPICIOUS_DOMAIN_PATTERNS:
            if re.match(pattern, domain, re.IGNORECASE):
                return False

        # Basic domain format validation
        if not re.match(
            r"^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$", domain
        ):
            return False

        return True

    @staticmethod
    def validate_email_pattern(pattern: str) -> bool:
        """Check if email pattern is valid and not suspicious."""
        if not pattern:
            return False

        # Check against suspicious patterns
        for suspicious in SUSPICIOUS_EMAIL_PATTERNS:
            if suspicious.lower() in pattern.lower():
                return False

        return True

    @staticmethod
    def validate_email(email: str) -> bool:
        """Check if email is valid format."""
        if not email:
            return False

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            return False

        # Check domain part
        domain = email.split("@")[1]
        return DataValidator.validate_domain(domain)

    @staticmethod
    def adjust_confidence(confidence: float, source: str) -> float:
        """Adjust confidence based on source reliability."""
        multiplier = SERVICE_CONFIDENCE_MULTIPLIERS.get(source, 0.5)
        adjusted = confidence * multiplier
        return min(adjusted, 1.0)  # Cap at 1.0

    @staticmethod
    def filter_results(
        results: List[Dict[str, Any]], result_type: str
    ) -> List[Dict[str, Any]]:
        """Filter results based on validation and confidence thresholds."""
        filtered = []
        min_confidence = MIN_CONFIDENCE_THRESHOLDS.get(result_type, 0.3)

        for result in results:
            # Validate based on result type
            if result_type == "domain":
                if not DataValidator.validate_domain(result.get("domain", "")):
                    continue
            elif result_type == "pattern":
                if not DataValidator.validate_email_pattern(result.get("pattern", "")):
                    continue
            elif result_type == "email":
                if not DataValidator.validate_email(result.get("email", "")):
                    continue

            # Check minimum confidence
            adjusted_confidence = DataValidator.adjust_confidence(
                result.get("confidence", 0), result.get("source", "unknown")
            )

            if adjusted_confidence >= min_confidence:
                result["confidence"] = adjusted_confidence
                filtered.append(result)

        # Sort by confidence and return top results
        filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return filtered
