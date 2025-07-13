import requests
import logging
from typing import Dict, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailValidationService:
    """
    Service for advanced email validation using multiple external APIs.
    Designed to be extensible for future validation providers (Hunter.io, Clearbit, etc.).
    """

    @staticmethod
    def validate_email_smtp(email: str) -> Dict[str, Any]:
        """
        Validate email using SMTP checker API.

        Returns:
            dict: {
                'valid': bool,
                'status': str,  # 'deliverable', 'undeliverable', 'catch_all', 'unknown'
                'confidence_adjustment': float,  # multiplier for existing confidence
                'reason': str
            }
        """
        if (
            not hasattr(settings, "EMAIL_VERIFIER_KEY")
            or not settings.EMAIL_VERIFIER_KEY
        ):
            logger.warning(
                "EMAIL_VERIFIER_KEY not configured, skipping SMTP validation"
            )
            return {
                "valid": None,
                "status": "unknown",
                "confidence_adjustment": 1.0,
                "reason": "No API key configured",
            }

        try:
            url = "https://api.emails-checker.net/check"
            response = requests.get(
                url,
                params={"access_key": settings.EMAIL_VERIFIER_KEY, "email": email},
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()

                # Handle emails-checker.net API response format
                if data.get("success") == "true" and "response" in data:
                    api_response = data["response"]
                    result = api_response.get("result", "unknown").lower()
                    description = api_response.get("description", "")
                    catch_all = api_response.get("catch_all", False)

                    # Map API response to our confidence adjustments
                    if result == "deliverable":
                        return {
                            "valid": True,
                            "status": "deliverable",
                            "confidence_adjustment": 1.3,  # +30% boost (most cases truly valid)
                            "reason": f"SMTP validation passed: {description}",
                        }
                    elif result == "undeliverable":
                        return {
                            "valid": False,
                            "status": "undeliverable",
                            "confidence_adjustment": 0.8,  # -20% penalty (most invalid, some security blocks)
                            "reason": f"SMTP validation failed: {description}",
                        }
                    elif result == "risky" or catch_all:
                        return {
                            "valid": None,
                            "status": "catch_all",
                            "confidence_adjustment": 0.9,  # -10% penalty (domain valid, username uncertain)
                            "reason": f"Domain accepts all emails: {description}",
                        }
                    else:
                        return {
                            "valid": None,
                            "status": "unknown",
                            "confidence_adjustment": 1.0,
                            "reason": f"Unknown validation result: {result} - {description}",
                        }
                else:
                    return {
                        "valid": None,
                        "status": "unknown",
                        "confidence_adjustment": 1.0,
                        "reason": "Invalid API response format",
                    }
            else:
                logger.error(f"SMTP validation API error: {response.status_code}")
                return {
                    "valid": None,
                    "status": "unknown",
                    "confidence_adjustment": 1.0,
                    "reason": f"API error: {response.status_code}",
                }

        except Exception as e:
            logger.error(f"SMTP validation failed: {e}")
            return {
                "valid": None,
                "status": "unknown",
                "confidence_adjustment": 1.0,
                "reason": f"Validation error: {str(e)}",
            }

    @staticmethod
    def adjust_confidence_by_source(candidate_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust confidence based on source type as defined in the prompt.
        This ensures consistency with LLM-generated confidence levels.
        """
        source = candidate_email.get("source", "pattern_generic")
        current_confidence = candidate_email.get("confidence", 0.5)

        # Source-based confidence adjustments (keeping within 1-99% realistic bounds)
        source_adjustments = {
            "public_found": (0.85, 0.95),  # High confidence range (85-95%)
            "pattern_verified": (0.70, 0.84),  # Medium-high confidence range (70-84%)
            "pattern_suspected": (0.50, 0.69),  # Medium confidence range (50-69%)
            "pattern_generic": (0.30, 0.49),  # Low confidence range (30-49%)
        }

        if source in source_adjustments:
            min_conf, max_conf = source_adjustments[source]

            # If LLM confidence is outside expected range, adjust it
            if current_confidence < min_conf:
                candidate_email["confidence"] = EmailValidationService.clamp_confidence(
                    min_conf
                )
                candidate_email["confidence_adjusted"] = True
            elif current_confidence > max_conf:
                candidate_email["confidence"] = EmailValidationService.clamp_confidence(
                    max_conf
                )
                candidate_email["confidence_adjusted"] = True
            else:
                candidate_email["confidence_adjusted"] = False

        return candidate_email

    @staticmethod
    def clamp_confidence(confidence: float) -> float:
        """
        Clamp confidence to realistic bounds (1-99%).
        Never allow 0% or 100% confidence - always leave room for uncertainty.
        """
        return min(max(confidence, 0.01), 0.99)

    @staticmethod
    def confidence_to_percentage(confidence: float) -> str:
        """
        Convert confidence to percentage string for display.
        """
        return f"{confidence * 100:.1f}%"

    @staticmethod
    def validate_and_score_candidates(
        candidate_emails: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Validate all candidate emails and adjust their confidence scores.

        Args:
            candidate_emails: List of candidate email dicts from LLM

        Returns:
            List of updated candidate email dicts with validation results
        """
        validated_candidates = []

        for candidate in candidate_emails:
            # 1. Ensure source-based confidence consistency
            candidate = EmailValidationService.adjust_confidence_by_source(candidate)

            # 2. Perform advanced validation  SMTP, multiple APIs)
            email = candidate.get("email")
            if email:
                smtp_result = EmailValidationService.validate_email_smtp(email)

                # Update candidate with validation results
                candidate.update(
                    {
                        "smtp_status": smtp_result["status"],
                        "smtp_valid": smtp_result["valid"],
                        "validation_reason": smtp_result["reason"],
                        "verification_method": "smtp_check",
                    }
                )

                # Apply confidence adjustment with proper clamping
                original_confidence = candidate["confidence"]
                adjusted_confidence = (
                    original_confidence * smtp_result["confidence_adjustment"]
                )
                # Clamp to realistic bounds: never 0% or 100%, keep in 1-99% range
                candidate["confidence"] = EmailValidationService.clamp_confidence(
                    adjusted_confidence
                )

                # Recalculate final score (confidence * relevance_score)
                relevance_score = candidate.get("relevance_score", 1.0)
                candidate["final_score"] = candidate["confidence"] * relevance_score

                # Add validation metadata
                candidate["validation_applied"] = True
                if adjusted_confidence != original_confidence:
                    candidate["confidence_change"] = (
                        adjusted_confidence - original_confidence
                    )

                logger.info(
                    f"Validated {email}: {smtp_result['status']} "
                    f"(confidence: {original_confidence:.3f} → {candidate['confidence']:.3f})"
                )

            validated_candidates.append(candidate)

        # Sort by final_score descending
        validated_candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)

        return validated_candidates


def validate_email_candidates(
    candidate_emails: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convenience function for advanced email validation.
    Extensible for future validation providers and methods.
    """
    return EmailValidationService.validate_and_score_candidates(candidate_emails)
