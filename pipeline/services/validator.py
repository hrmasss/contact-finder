import re
import logging
from typing import List, Dict, Any
from .confidence import (
    SUSPICIOUS_EMAIL_PATTERNS,
    MIN_CONFIDENCE_THRESHOLDS,
    SERVICE_CONFIDENCE_MULTIPLIERS,
)
from .validation import ComprehensiveDomainValidator

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates and filters discovery results."""
    
    _domain_validator = None
    
    @classmethod
    def get_domain_validator(cls) -> ComprehensiveDomainValidator:
        """Get singleton instance of domain validator."""
        if cls._domain_validator is None:
            cls._domain_validator = ComprehensiveDomainValidator()
        return cls._domain_validator

    @staticmethod
    def validate_domain(domain: str) -> bool:
        """
        Check if domain is valid and not suspicious.
        
        This is a simplified interface for backward compatibility.
        For detailed validation results, use validate_domain_comprehensive().
        """
        validator = DataValidator.get_domain_validator()
        result = validator.validate_domain(domain)
        return result.is_valid

    @staticmethod 
    def validate_domain_comprehensive(domain: str, original_confidence: float = 1.0) -> Dict[str, Any]:
        """
        Comprehensive domain validation with MX record check and confidence adjustment.
        
        Args:
            domain: Domain to validate
            original_confidence: Original confidence score (0.0-1.0)
            
        Returns:
            Dict with validation results and adjusted confidence
        """
        validator = DataValidator.get_domain_validator()
        return validator.validate_and_adjust_confidence(domain, original_confidence)

    @staticmethod
    def adjust_confidence_for_domain(domain: str, confidence: float) -> float:
        """
        Adjust confidence based on domain validation results.
        
        This method applies domain validation penalties in addition to source reliability.
        """
        validation_result = DataValidator.validate_domain_comprehensive(domain, confidence)
        adjusted_confidence = validation_result['adjusted_confidence']
        
        # Log significant penalties
        if validation_result['confidence_penalty'] < 0.5:
            logger.warning(
                f"Domain {domain} received significant confidence penalty: "
                f"{confidence:.3f} → {adjusted_confidence:.3f} "
                f"(status: {validation_result['validation_status']})"
            )
        
        return adjusted_confidence

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
                domain = result.get("domain", "")
                if not DataValidator.validate_domain(domain):
                    continue
                # Apply comprehensive domain validation with confidence adjustment
                adjusted_confidence = DataValidator.adjust_confidence_for_domain(
                    domain, result.get("confidence", 0)
                )
            elif result_type == "pattern":
                if not DataValidator.validate_email_pattern(result.get("pattern", "")):
                    continue
                # Apply source-based confidence adjustment
                adjusted_confidence = DataValidator.adjust_confidence(
                    result.get("confidence", 0), result.get("source", "unknown")
                )
            elif result_type == "email":
                if not DataValidator.validate_email(result.get("email", "")):
                    continue
                # Apply source-based confidence adjustment
                adjusted_confidence = DataValidator.adjust_confidence(
                    result.get("confidence", 0), result.get("source", "unknown")
                )
            else:
                # Default case: just apply source-based adjustment
                adjusted_confidence = DataValidator.adjust_confidence(
                    result.get("confidence", 0), result.get("source", "unknown")
                )

            if adjusted_confidence >= min_confidence:
                result["confidence"] = adjusted_confidence
                filtered.append(result)

        # Sort by confidence and return top results
        filtered.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return filtered
