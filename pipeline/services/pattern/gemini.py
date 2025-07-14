import json
from typing import List
from .base import PatternDiscoveryService, PatternResult, EmailResult
from ..prompts import PATTERN_DISCOVERY_PROMPT
from contactfinder.agents.gemini_agent import gemini_agent


class GeminiPatternService(PatternDiscoveryService):
    """Email pattern discovery using Gemini with Google Search."""

    def discover_email_patterns(self, domain: str) -> List[PatternResult]:
        """
        Discover email patterns for a domain using Gemini.

        Args:
            domain: Domain to analyze for patterns

        Returns:
            List[PatternResult]: Email patterns found
        """
        # Format the prompt
        prompt = PATTERN_DISCOVERY_PROMPT.format(domain=domain)

        try:
            # Call Gemini agent
            response = gemini_agent(prompt)

            # Clean the response to extract JSON
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()

            # Parse JSON response
            data = json.loads(response_clean)

            # Convert to PatternResult objects
            patterns = []
            for pattern_data in data.get("patterns", []):
                pattern_result = PatternResult(
                    domain=pattern_data["domain"],
                    pattern=pattern_data["pattern"],
                    confidence=pattern_data["confidence"],
                    source=pattern_data["source"],
                    verified_count=pattern_data.get("verified_count", 0),
                )
                patterns.append(pattern_result)

            return patterns

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Gemini response for {domain}: {e}")
            print(f"Raw response: {response}")
            # Return fallback patterns
            return self._get_fallback_patterns(domain)
        except Exception as e:
            print(f"Error in Gemini pattern discovery for {domain}: {e}")
            return self._get_fallback_patterns(domain)

    def _get_fallback_patterns(self, domain: str) -> List[PatternResult]:
        """Get fallback patterns when Gemini fails."""
        fallback_patterns = [
            PatternResult(
                domain=domain,
                pattern="first.last",
                confidence=0.4,
                source="fallback",
                verified_count=0,
            ),
            PatternResult(
                domain=domain,
                pattern="firstlast",
                confidence=0.4,
                source="fallback",
                verified_count=0,
            ),
            PatternResult(
                domain=domain,
                pattern="f.last",
                confidence=0.4,
                source="fallback",
                verified_count=0,
            ),
        ]
        return fallback_patterns

    def discover_known_emails(self, domain: str) -> List[EmailResult]:
        """
        Discover known public emails for a domain using Gemini.

        Args:
            domain: Domain to search for public emails

        Returns:
            List[EmailResult]: Known emails found
        """
        # Format the prompt
        prompt = PATTERN_DISCOVERY_PROMPT.format(domain=domain)

        try:
            # Call Gemini agent
            response = gemini_agent(prompt)

            # Clean the response to extract JSON
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()

            # Parse JSON response
            data = json.loads(response_clean)

            # Convert to EmailResult objects
            emails = []
            for email_data in data.get("known_emails", []):
                email_result = EmailResult(
                    email=email_data["email"],
                    source=email_data["source"],
                    confidence=email_data["confidence"],
                )
                emails.append(email_result)

            return emails

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing Gemini response for {domain}: {e}")
            print(f"Raw response: {response}")
            # Return fallback emails
            return self._get_fallback_emails(domain)
        except Exception as e:
            print(f"Error in Gemini email discovery for {domain}: {e}")
            return self._get_fallback_emails(domain)

    def _get_fallback_emails(self, domain: str) -> List[EmailResult]:
        """Get fallback emails when Gemini fails."""
        fallback_emails = [
            EmailResult(email=f"info@{domain}", source="fallback", confidence=0.7),
            EmailResult(email=f"contact@{domain}", source="fallback", confidence=0.6),
            EmailResult(email=f"support@{domain}", source="fallback", confidence=0.5),
        ]
        return fallback_emails
